param(
    [ValidateSet('Probe', 'Sleep', 'Noop', 'ExitCheck')][string]$Mode = 'Probe',
    [int]$Seconds = 600,
    [string]$Distribution = 'Ubuntu-24.04',
    [string]$LinuxUser = 'addaswsw',
    [string]$Repository = '/home/addaswsw/lab/Software_system_optimization',
    [string]$GuestOutput,
    [ValidateSet('active', 'inactive')][string]$ExpectedService = 'inactive'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
if ($Seconds -lt 1) { throw 'Seconds must be positive' }
if ($Mode -eq 'Probe' -and -not $GuestOutput) { throw 'GuestOutput is required' }
$wslArgs = @('--distribution', $Distribution, '--user', $LinuxUser, '--exec')
switch ($Mode) {
    'Probe' { $wslArgs += @('/usr/bin/python3', "$Repository/A2/evidence/tools/host-reference-probe.py",
        $GuestOutput, '--seconds', "$Seconds", '--expected-service', $ExpectedService) }
    'Sleep' { $wslArgs += @('/usr/bin/sleep', "$Seconds") }
    'Noop' { $wslArgs += @('/usr/bin/true') }
    'ExitCheck' { $wslArgs += @('/bin/sh', '-c', 'exit 7') }
}
# This request exists only for this thread/process; it does not edit a power plan.
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
public static class A2Awake {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
$awakeResult = [A2Awake]::SetThreadExecutionState([uint32]2147483649)
if ($awakeResult -eq 0) { throw 'Temporary sleep prevention failed' }
$stopwatch = New-Object System.Diagnostics.Stopwatch
$exitCode = $null
$wrapperError = $null
$hostStart = [DateTime]::UtcNow
$startCounter = [Diagnostics.Stopwatch]::GetTimestamp()
$stopwatch.Start()
try {
    # Synchronous invocation: the timer cannot stop before this WSL probe returns.
    & wsl.exe @wslArgs | Out-Null
    $exitCode = $LASTEXITCODE
} catch {
    $wrapperError = $_.Exception.Message
} finally {
    $stopwatch.Stop()
    $endCounter = [Diagnostics.Stopwatch]::GetTimestamp()
    $hostEnd = [DateTime]::UtcNow
    $clearResult = [A2Awake]::SetThreadExecutionState([uint32]2147483648)
}
[ordered]@{
    host_start_utc = $hostStart.ToString('o')
    host_end_utc = $hostEnd.ToString('o')
    host_wall_seconds = ($hostEnd - $hostStart).TotalSeconds
    host_stopwatch_seconds = $stopwatch.Elapsed.TotalSeconds
    stopwatch_elapsed_ticks = $stopwatch.ElapsedTicks
    stopwatch_frequency = [Diagnostics.Stopwatch]::Frequency
    stopwatch_is_high_resolution = [Diagnostics.Stopwatch]::IsHighResolution
    enclosing_counter_start = $startCounter
    enclosing_counter_end = $endCounter
    wsl_exit_code = $exitCode
    wrapper_error = $wrapperError
    mode = $Mode
    requested_seconds = $Seconds
    powershell_pid = $PID
    powershell_version = $PSVersionTable.PSVersion.ToString()
    wsl_argv = $wslArgs
    temporary_awake_set_return = $awakeResult
    temporary_awake_clear_return = $clearResult
} | ConvertTo-Json -Depth 4
if ($wrapperError -or $null -eq $exitCode) { exit 1 }
exit $exitCode
