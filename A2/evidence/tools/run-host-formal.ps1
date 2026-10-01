param(
    [ValidateSet('base', 'repeat', 'parameter')][string]$Kind,
    [string]$GuestOutput,
    [string]$CampaignId,
    [string]$Distribution = 'Ubuntu-24.04',
    [string]$LinuxUser = 'addaswsw',
    [string]$Repository = '/home/addaswsw/lab/Software_system_optimization'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
if (-not $Kind -or -not $GuestOutput -or -not $CampaignId) { throw 'All run arguments are required' }
Add-Type -AssemblyName System.Windows.Forms
$powerBefore = [Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus.ToString()
if ($powerBefore -ne 'Online') { throw 'Host AC power is not online' }
$schemeBefore = (powercfg /getactivescheme | Out-String).Trim()
$wslArgs = @('--distribution', $Distribution, '--user', $LinuxUser, '--exec',
    '/usr/bin/python3', '-B', "$Repository/A2/evidence/tools/measure-formal-run.py",
    $GuestOutput, $Kind, $CampaignId)
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
    kind = $Kind
    campaign_id = $CampaignId
    power_line_before = $powerBefore
    power_line_after = [Windows.Forms.SystemInformation]::PowerStatus.PowerLineStatus.ToString()
    power_scheme_before = $schemeBefore
    power_scheme_after = (powercfg /getactivescheme | Out-String).Trim()
    powershell_pid = $PID
    powershell_version = $PSVersionTable.PSVersion.ToString()
    wsl_argv = $wslArgs
    temporary_awake_set_return = $awakeResult
    temporary_awake_clear_return = $clearResult
} | ConvertTo-Json -Depth 4
if ($wrapperError -or $null -eq $exitCode) { exit 1 }
exit $exitCode
