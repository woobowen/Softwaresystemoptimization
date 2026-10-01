param(
    [int]$Samples = 6,
    [int]$IntervalSeconds = 10,
    [string]$Distribution = 'Ubuntu-24.04',
    [string]$LinuxUser = 'addaswsw'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
if ($Samples -lt 5 -or $IntervalSeconds -lt 1) { throw 'At least five spaced samples required' }
$epoch = [DateTime]::SpecifyKind([DateTime]'1970-01-01', [DateTimeKind]::Utc)
$rows = @()
for ($i = 0; $i -lt $Samples; $i++) {
    $t0 = [DateTime]::UtcNow
    $s0 = [Diagnostics.Stopwatch]::GetTimestamp()
    $linux = & wsl.exe --distribution $Distribution --user $LinuxUser --exec /usr/bin/python3 -c 'import time;print(time.clock_gettime(time.CLOCK_REALTIME))'
    $code = $LASTEXITCODE
    $s1 = [Diagnostics.Stopwatch]::GetTimestamp()
    $t1 = [DateTime]::UtcNow
    if ($code -ne 0) { throw "WSL comparison failed: $code" }
    $realtime = [double]::Parse(($linux | Out-String).Trim(), [Globalization.CultureInfo]::InvariantCulture)
    $wall = ($t1 - $t0).TotalSeconds
    $rtt = ($s1 - $s0) / [double][Diagnostics.Stopwatch]::Frequency
    $midpoint = ($t0 - $epoch).TotalSeconds + $wall / 2
    # Include boundary latency, host wall/monotonic disagreement, and 2 ms clock-read allowance.
    $uncertainty = [Math]::Max([Math]::Abs($wall), $rtt) / 2 + [Math]::Abs($wall - $rtt) + .002
    $rows += [ordered]@{
        sample_index = $i; host_t0_utc = $t0.ToString('o'); host_t1_utc = $t1.ToString('o')
        host_t0_ticks = $t0.Ticks; host_t1_ticks = $t1.Ticks
        counter_start = $s0; counter_end = $s1; stopwatch_frequency = [Diagnostics.Stopwatch]::Frequency
        host_midpoint_epoch_seconds = $midpoint; linux_realtime_epoch_seconds = $realtime
        round_trip_seconds = $rtt; host_wall_round_trip_seconds = $wall
        alignment_error_seconds = $realtime - $midpoint; practical_uncertainty_seconds = $uncertainty
        wsl_exit_code = $code
    }
    if ($i -lt $Samples - 1) { Start-Sleep -Seconds $IntervalSeconds }
}
$rows | ConvertTo-Json -Depth 4
