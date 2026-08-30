$ErrorActionPreference = 'Stop'

# This is a production machine-readable wrapper. Even malformed invocations
# return one fixed JSON error; the argument gate below still requires one flag.
$JsonRequested = $true
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$VenvDir = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'
$ModelDir = Join-Path $ProjectRoot 'models\multilingual-e5-small-openvino-fp16'
$BootstrapContract = 'qoder-openvino-v1'
$ReadyMarker = Join-Path $VenvDir '.airlock-ready-qoder-openvino-v1'
$PackageManifest = Join-Path $ProjectRoot 'pyproject.toml'
$WindowsGatedLauncherPath = Join-Path $PSScriptRoot 'windows_gated_launcher.ps1'

function Write-AirlockError {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if ($JsonRequested) {
        $Payload = [ordered]@{
            schema_version = '0.1'
            error = [ordered]@{
                code = $Code
                message = $Message
            }
        }
        [Console]::Error.WriteLine(($Payload | ConvertTo-Json -Compress -Depth 3))
    }
    else {
        [Console]::Error.WriteLine("ERROR ${Code}: ${Message}")
    }
}

function Stop-Airlock {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [Parameter(Mandatory = $true)][string]$Message,
        [int]$ExitCode = 2
    )

    Write-AirlockError -Code $Code -Message $Message
    exit $ExitCode
}

function Write-AirlockProgress {
    param([Parameter(Mandatory = $true)][string]$Message)

    if (-not $JsonRequested) {
        [Console]::Error.WriteLine($Message)
    }
}

try {
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PIP_NO_INPUT = '1'
    $env:PIP_DEFAULT_TIMEOUT = '30'
    $env:PIP_RETRIES = '1'
    # Pin health and analyze to a path derived from this installed Skill, never caller cwd.
    $env:AI_AIRLOCK_EMBEDDING_MODEL_DIR = $ModelDir
}
catch {
    Stop-Airlock -Code 'AIRLOCK_CONSOLE_INITIALIZATION_FAILED' `
        -Message 'AI Airlock could not initialize UTF-8 console I/O.'
}

function Test-Python312 {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$Prefix = @()
    )

    $ProbeArguments = @($Prefix) + @(
        '-c',
        'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'
    )
    $Probe = Invoke-BoundedProcess -Executable $Executable `
        -ProcessArguments $ProbeArguments -TimeoutMilliseconds 30000
    return $Probe.Started -and -not $Probe.TimedOut -and $Probe.ExitCode -eq 0
}

function Test-AirlockRuntime {
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        return $false
    }
    $Probe = Invoke-BoundedProcess -Executable $VenvPython `
        -ProcessArguments @(
            '-c',
            'import sys; import airlock.cli, airlock.pipeline, airlock.qoder_gate; raise SystemExit(sys.version_info[:2] != (3, 12))'
        ) `
        -TimeoutMilliseconds 30000
    return $Probe.Started -and -not $Probe.TimedOut -and $Probe.ExitCode -eq 0
}

function Test-AirlockOpenVINOReady {
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        return $false
    }
    $Probe = Invoke-BoundedProcess -Executable $VenvPython `
        -ProcessArguments @(
            '-c',
            'import sys; from airlock.relevance.openvino_ranker import openvino_ready; raise SystemExit(not openvino_ready(sys.argv[1]))',
            $ModelDir
        ) `
        -TimeoutMilliseconds 120000
    return $Probe.Started -and -not $Probe.TimedOut -and $Probe.ExitCode -eq 0
}

function Get-PackageStamp {
    if (-not (Test-Path -LiteralPath $PackageManifest -PathType Leaf)) {
        return $null
    }
    try {
        $ManifestHash = (Get-FileHash -LiteralPath $PackageManifest -Algorithm SHA256).Hash
        return '{0}:{1}' -f $ManifestHash, $BootstrapContract
    }
    catch {
        return $null
    }
}

function Test-ReadyMarker {
    param([Parameter(Mandatory = $true)][string]$ExpectedStamp)

    if (-not (Test-Path -LiteralPath $ReadyMarker -PathType Leaf)) {
        return $false
    }
    try {
        return (Get-Content -LiteralPath $ReadyMarker -Raw -Encoding UTF8).Trim() -ceq $ExpectedStamp
    }
    catch {
        return $false
    }
}

function Test-JsonProperty {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    return $null -ne $Object -and @($Object.PSObject.Properties.Name) -ccontains $Name
}

function Test-JsonObjectWithProperties {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    if ($null -eq $Object -or -not ($Object -is [pscustomobject])) {
        return $false
    }
    foreach ($Name in $Names) {
        if (-not (Test-JsonProperty -Object $Object -Name $Name)) {
            return $false
        }
    }
    return $true
}

function Test-JsonStringProperty {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    return (Test-JsonProperty -Object $Object -Name $Name) -and `
        $Object.$Name -is [string] -and `
        -not [string]::IsNullOrWhiteSpace($Object.$Name)
}

function Test-JsonIntegerValue {
    param(
        [Parameter(Mandatory = $true)][AllowNull()]$Value,
        [switch]$Positive
    )

    if ($null -eq $Value) {
        return $false
    }
    $IntegerTypes = @(
        [byte], [sbyte], [int16], [uint16], [int32], [uint32], [int64], [uint64]
    )
    if ($IntegerTypes -notcontains $Value.GetType()) {
        return $false
    }
    if ($Positive) {
        return [decimal]$Value -gt 0
    }
    return [decimal]$Value -ge 0
}

function Test-JsonFiniteNumberValue {
    param([Parameter(Mandatory = $true)][AllowNull()]$Value)

    if ($null -eq $Value -or $Value -is [bool] -or -not ($Value -is [System.ValueType])) {
        return $false
    }
    try {
        $Number = [double]$Value
        return -not [double]::IsNaN($Number) -and -not [double]::IsInfinity($Number)
    }
    catch {
        return $false
    }
}

function Test-JsonBooleanProperty {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )

    return (Test-JsonProperty -Object $Object -Name $Name) -and `
        $Object.$Name -is [bool]
}

function Test-JsonNonNegativeIntegerProperties {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Object,
        [Parameter(Mandatory = $true)][string[]]$Names
    )

    if (-not (Test-JsonObjectWithProperties -Object $Object -Names $Names)) {
        return $false
    }
    foreach ($Name in $Names) {
        if (-not (Test-JsonIntegerValue -Value $Object.$Name)) {
            return $false
        }
    }
    return $true
}

function Test-JsonStringArray {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Values,
        [switch]$AllowEmpty
    )

    if (-not ($Values -is [System.Array]) -or (-not $AllowEmpty -and $Values.Count -eq 0)) {
        return $false
    }
    foreach ($Value in $Values) {
        if (-not ($Value -is [string]) -or [string]::IsNullOrWhiteSpace($Value)) {
            return $false
        }
    }
    return $true
}

function Test-InferenceMetadata {
    param([Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Inference)

    if (-not (Test-JsonObjectWithProperties -Object $Inference `
        -Names @('mode', 'openvino_available')) -or `
        -not (Test-JsonStringProperty -Object $Inference -Name 'mode') -or `
        -not (Test-JsonBooleanProperty -Object $Inference -Name 'openvino_available') -or `
        @('deterministic_rules', 'openvino_embedding') -cnotcontains [string]$Inference.mode) {
        return $false
    }
    if ($Inference.mode -ceq 'openvino_embedding') {
        return $Inference.openvino_available -eq $true -and `
            (Test-JsonStringProperty -Object $Inference -Name 'device') -and `
            (Test-JsonStringProperty -Object $Inference -Name 'model_id') -and `
            (Test-JsonStringProperty -Object $Inference -Name 'model_revision') -and `
            (Test-JsonIntegerValue -Value $Inference.chunks_processed) -and `
            (Test-JsonStringProperty -Object $Inference -Name 'fallback_state') -and `
            $Inference.fallback_state -ceq 'not_used'
    }
    return $true
}

function Test-FactArray {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Facts
    )

    if (-not ($Facts -is [System.Array])) {
        return $false
    }
    foreach ($Fact in $Facts) {
        if (-not (Test-JsonObjectWithProperties -Object $Fact -Names @(
            'id', 'text', 'source', 'local_ref', 'selection_score'
        ))) {
            return $false
        }
        foreach ($Name in @('id', 'text', 'source', 'local_ref')) {
            if (-not (Test-JsonStringProperty -Object $Fact -Name $Name)) {
                return $false
            }
        }
        if (-not (Test-JsonIntegerValue -Value $Fact.selection_score)) {
            return $false
        }
    }
    return $true
}

function Test-FindingArray {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][AllowEmptyCollection()]$Findings
    )

    if (-not ($Findings -is [System.Array])) {
        return $false
    }
    foreach ($Finding in $Findings) {
        if (-not (Test-JsonObjectWithProperties -Object $Finding -Names @(
            'type', 'severity', 'source', 'line', 'detector', 'action'
        ))) {
            return $false
        }
        foreach ($Name in @('type', 'severity', 'source', 'detector', 'action')) {
            if (-not (Test-JsonStringProperty -Object $Finding -Name $Name)) {
                return $false
            }
        }
        if (-not (Test-JsonIntegerValue -Value $Finding.line -Positive)) {
            return $false
        }
    }
    return $true
}

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Value)

    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }

    $Quoted = '"'
    $Backslashes = 0
    foreach ($Character in $Value.ToCharArray()) {
        if ($Character -eq '\') {
            $Backslashes += 1
            continue
        }
        if ($Character -eq '"') {
            if ($Backslashes -gt 0) {
                $Quoted += (('\' * ($Backslashes * 2)) -join '')
            }
            $Quoted += '\"'
            $Backslashes = 0
            continue
        }
        if ($Backslashes -gt 0) {
            $Quoted += (('\' * $Backslashes) -join '')
            $Backslashes = 0
        }
        $Quoted += $Character
    }
    if ($Backslashes -gt 0) {
        $Quoted += (('\' * ($Backslashes * 2)) -join '')
    }
    return $Quoted + '"'
}

function Stop-ProcessTreeBounded {
    param([Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process)

    if ($Process.HasExited) {
        return
    }

    $TreeKillStarted = $false
    try {
        $KillTreeMethod = $Process.GetType().GetMethod('Kill', [type[]]@([bool]))
        if ($null -ne $KillTreeMethod) {
            $KillTreeMethod.Invoke($Process, @($true)) | Out-Null
            $TreeKillStarted = $true
        }
    }
    catch {
        $TreeKillStarted = $false
    }

    if (-not $TreeKillStarted -and -not $Process.HasExited) {
        $TaskKillPath = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        if (Test-Path -LiteralPath $TaskKillPath -PathType Leaf) {
            $TaskKillInfo = [System.Diagnostics.ProcessStartInfo]::new()
            $TaskKillInfo.FileName = $TaskKillPath
            $TaskKillInfo.Arguments = "/PID $($Process.Id) /T /F"
            $TaskKillInfo.UseShellExecute = $false
            $TaskKillInfo.CreateNoWindow = $true
            $TaskKillInfo.RedirectStandardOutput = $true
            $TaskKillInfo.RedirectStandardError = $true
            $TaskKill = [System.Diagnostics.Process]::new()
            $TaskKill.StartInfo = $TaskKillInfo
            try {
                if ($TaskKill.Start()) {
                    $TaskKill.StandardOutput.ReadToEndAsync() | Out-Null
                    $TaskKill.StandardError.ReadToEndAsync() | Out-Null
                    if (-not $TaskKill.WaitForExit(5000)) {
                        $TaskKill.Kill()
                        $TaskKill.WaitForExit(1000) | Out-Null
                    }
                }
            }
            catch {
                # Fall through to the direct parent-process kill below.
            }
            finally {
                $TaskKill.Dispose()
            }
        }
    }

    if (-not $Process.HasExited) {
        try {
            $Process.Kill()
        }
        catch {
            # The process may have exited between the bounded checks.
        }
    }
    try {
        $Process.WaitForExit(5000) | Out-Null
    }
    catch {
        # Never turn process cleanup into an unbounded wait or raw exception.
    }
}

function Invoke-BoundedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [string[]]$ProcessArguments = @(),
        [string]$ProcessWorkingDirectory = $ProjectRoot,
        [int]$TimeoutMilliseconds = 120000,
        [AllowNull()][object]$StandardInputText = $null,
        [int]$MaxCapturedCharacters = 4194304
    )

    $ArgumentText = (($ProcessArguments | ForEach-Object {
        ConvertTo-NativeArgument -Value ([string]$_)
    }) -join ' ')

    $Process = $null
    $KillOnCloseJob = $null
    $ControlPipe = $null
    $ProcessStarted = $false
    $ProcessIsolationFailed = $false
    $ExitedProcessJobCompleted = $false
    try {
        if ($TimeoutMilliseconds -le 0 -or $MaxCapturedCharacters -le 0 -or `
            ($null -ne $StandardInputText -and -not ($StandardInputText -is [string]))) {
            throw 'invalid bounded-process limits'
        }
        $Watch = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $Session = Start-AirlockGatedProcess `
                -Executable $Executable `
                -ArgumentText $ArgumentText `
                -WorkingDirectory $ProcessWorkingDirectory `
                -LauncherPath $WindowsGatedLauncherPath `
                -RedirectStandardInput ($null -ne $StandardInputText) `
                -HandshakeTimeoutMilliseconds ([Math]::Min($TimeoutMilliseconds, 10000))
        }
        catch {
            $ProcessIsolationFailed = $true
            throw
        }
        if (-not $Session.TargetStarted) {
            return [pscustomobject]@{
                Started = $false
                TimedOut = $false
                OutputLimitExceeded = $false
                ExitCode = 2
                Stdout = ''
                Stderr = ''
            }
        }
        $Process = $Session.Process
        $KillOnCloseJob = $Session.Job
        $ControlPipe = $Session.ControlPipe
        $ProcessStarted = $true

        # Read both pipes in fixed-size chunks. This keeps memory bounded and
        # prevents either child pipe from blocking the other.
        $StdoutBuilder = [System.Text.StringBuilder]::new()
        $StderrBuilder = [System.Text.StringBuilder]::new()
        $StdoutBuffer = [char[]]::new(4096)
        $StderrBuffer = [char[]]::new(4096)
        $StdoutTask = $Process.StandardOutput.ReadAsync(
            $StdoutBuffer, 0, $StdoutBuffer.Length
        )
        $StderrTask = $Process.StandardError.ReadAsync(
            $StderrBuffer, 0, $StderrBuffer.Length
        )
        $CompletionBuffer = [byte[]]::new(5)
        $CompletionOffset = 0
        $CompletionTask = $ControlPipe.ReadAsync(
            $CompletionBuffer, $CompletionOffset, $CompletionBuffer.Length
        )
        $CompletionComplete = $false
        $TargetExitCode = $null
        $StdoutComplete = $false
        $StderrComplete = $false
        $InputComplete = $null -eq $StandardInputText
        $InputTask = $null
        if ($null -ne $StandardInputText) {
            # Never synchronously write to a child pipe before the timeout
            # clock starts: a non-reading child could otherwise hang forever.
            $InputTask = $Process.StandardInput.WriteAsync([string]$StandardInputText)
        }

        while ($true) {
            if ($Watch.ElapsedMilliseconds -ge $TimeoutMilliseconds) {
                try {
                    Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob
                    $KillOnCloseJob = $null
                }
                catch {
                    $ProcessIsolationFailed = $true
                    throw
                }
                return [pscustomobject]@{
                    Started = $true
                    TimedOut = $true
                    OutputLimitExceeded = $false
                    ExitCode = 2
                    Stdout = ''
                    Stderr = ''
                }
            }

            if (-not $InputComplete -and $InputTask.IsCompleted) {
                try {
                    $InputTask.GetAwaiter().GetResult()
                }
                finally {
                    $Process.StandardInput.Close()
                    $InputComplete = $true
                }
            }

            if (-not $StdoutComplete -and $StdoutTask.IsCompleted) {
                $ReadCount = $StdoutTask.GetAwaiter().GetResult()
                if ($ReadCount -eq 0) {
                    $StdoutComplete = $true
                }
                elseif ($StdoutBuilder.Length -gt $MaxCapturedCharacters - $ReadCount) {
                    try {
                        Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob
                        $KillOnCloseJob = $null
                    }
                    catch {
                        $ProcessIsolationFailed = $true
                        throw
                    }
                    return [pscustomobject]@{
                        Started = $true
                        TimedOut = $false
                        OutputLimitExceeded = $true
                        ExitCode = 2
                        Stdout = ''
                        Stderr = ''
                    }
                }
                else {
                    $StdoutBuilder.Append($StdoutBuffer, 0, $ReadCount) | Out-Null
                    $StdoutTask = $Process.StandardOutput.ReadAsync(
                        $StdoutBuffer, 0, $StdoutBuffer.Length
                    )
                }
            }

            if (-not $StderrComplete -and $StderrTask.IsCompleted) {
                $ReadCount = $StderrTask.GetAwaiter().GetResult()
                if ($ReadCount -eq 0) {
                    $StderrComplete = $true
                }
                elseif ($StderrBuilder.Length -gt $MaxCapturedCharacters - $ReadCount) {
                    try {
                        Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob
                        $KillOnCloseJob = $null
                    }
                    catch {
                        $ProcessIsolationFailed = $true
                        throw
                    }
                    return [pscustomobject]@{
                        Started = $true
                        TimedOut = $false
                        OutputLimitExceeded = $true
                        ExitCode = 2
                        Stdout = ''
                        Stderr = ''
                    }
                }
                else {
                    $StderrBuilder.Append($StderrBuffer, 0, $ReadCount) | Out-Null
                    $StderrTask = $Process.StandardError.ReadAsync(
                        $StderrBuffer, 0, $StderrBuffer.Length
                    )
                }
            }

            if (-not $CompletionComplete -and $CompletionTask.IsCompleted) {
                try {
                    $CompletionReadCount = $CompletionTask.GetAwaiter().GetResult()
                }
                catch {
                    $ProcessIsolationFailed = $true
                    throw
                }
                if ($CompletionReadCount -le 0) {
                    $ProcessIsolationFailed = $true
                    throw 'The gated launcher ended without a completion frame.'
                }
                $CompletionOffset += $CompletionReadCount
                if ($CompletionOffset -eq $CompletionBuffer.Length) {
                    if ([int]$CompletionBuffer[0] -ne 4) {
                        $ProcessIsolationFailed = $true
                        throw 'The gated launcher reported an internal failure.'
                    }
                    $TargetExitCode = [System.BitConverter]::ToInt32(
                        $CompletionBuffer, 1
                    )
                    $CompletionComplete = $true
                }
                else {
                    $CompletionTask = $ControlPipe.ReadAsync(
                        $CompletionBuffer,
                        $CompletionOffset,
                        $CompletionBuffer.Length - $CompletionOffset
                    )
                }
            }

            $ProcessExited = $Process.HasExited
            if ($ProcessExited -and -not $ExitedProcessJobCompleted) {
                # Descendants may still own copies of the redirected pipe handles.
                # Terminate the job and prove it empty before waiting for pipe EOF.
                try {
                    Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob
                    $KillOnCloseJob = $null
                    $ExitedProcessJobCompleted = $true
                }
                catch {
                    $ProcessIsolationFailed = $true
                    throw
                }
            }
            if ($ProcessExited -and -not $InputComplete) {
                $Process.StandardInput.Close()
                $InputComplete = $true
            }
            if ($ProcessExited -and $StdoutComplete -and $StderrComplete -and `
                $CompletionComplete) {
                break
            }
            Start-Sleep -Milliseconds 10
        }

        return [pscustomobject]@{
            Started = $true
            TimedOut = $false
            OutputLimitExceeded = $false
            ExitCode = $TargetExitCode
            Stdout = $StdoutBuilder.ToString()
            Stderr = $StderrBuilder.ToString()
        }
    }
    catch {
        if ($ProcessStarted -and $null -ne $KillOnCloseJob) {
            try {
                Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob
                $KillOnCloseJob = $null
            }
            catch {
                $ProcessIsolationFailed = $true
            }
        }
        elseif ($ProcessStarted -and $null -ne $Process) {
            try {
                Stop-ProcessTreeBounded -Process $Process
            }
            catch {
                # Cleanup failure must not expose a native exception or block the wrapper.
            }
        }
        if ($ProcessIsolationFailed) {
            Stop-Airlock -Code 'AIRLOCK_PROCESS_ISOLATION_FAILED' `
                -Message 'AI Airlock could not isolate its bounded child process.'
        }
        return [pscustomobject]@{
            Started = $false
            TimedOut = $false
            OutputLimitExceeded = $false
            ExitCode = 2
            Stdout = ''
            Stderr = ''
        }
    }
    finally {
        Close-AirlockKillOnCloseJob -Job $KillOnCloseJob
        if ($null -ne $ControlPipe) {
            $ControlPipe.Dispose()
        }
        if ($null -ne $Process) {
            $Process.Dispose()
        }
    }
}

function Test-AirlockAbsoluteWindowsPath {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value) -or $Value.IndexOf([char]0) -ge 0) {
        return $false
    }
    $DriveAbsolute = $Value -match '^[A-Za-z]:[\\/]'
    $UncAbsolute = $Value -match '^[\\/]{2}[^\\/:*?"<>|]+[\\/][^\\/:*?"<>|]+(?:[\\/]|$)'
    if (-not $DriveAbsolute -and -not $UncAbsolute) {
        return $false
    }
    $Components = @($Value -split '[\\/]')
    $FirstPathComponent = if ($DriveAbsolute) { 1 } else { 2 }
    for ($ComponentIndex = $FirstPathComponent; `
        $ComponentIndex -lt $Components.Count; $ComponentIndex += 1) {
        $Component = [string]$Components[$ComponentIndex]
        if ([string]::IsNullOrEmpty($Component)) {
            if ($ComponentIndex -eq $Components.Count - 1) {
                continue
            }
            return $false
        }
        # Ordinary Win32 APIs normalize trailing spaces/dots and device names.
        # Reject those spellings so the approved text cannot resolve elsewhere.
        if ($Component -ceq '.' -or $Component -ceq '..' -or `
            $Component.StartsWith(' ', [StringComparison]::Ordinal) -or `
            $Component.EndsWith(' ', [StringComparison]::Ordinal) -or `
            $Component.EndsWith('.', [StringComparison]::Ordinal) -or `
            $Component -match '[<>:"|?*\x00-\x1F]' -or `
            $Component -match '^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]|CONIN\$|CONOUT\$)(?:\.|$)') {
            return $false
        }
    }
    return $true
}

$Command = if ($args.Count -gt 0) { [string]$args[0] } else { '' }
$CliArguments = @($args)
$RequestedOpenVINO = $false
$PathValues = @()
$TaskValues = @()
$BackendValues = @()
$JsonCount = 0
$ModelOverrideRequested = $false
$UnexpectedArguments = @()

for ($Index = 1; $Index -lt $args.Count; $Index += 1) {
    $Argument = [string]$args[$Index]
    if ($Argument -ceq '--json') {
        $JsonCount += 1
    }
    elseif ($Argument -ceq '--path' -or $Argument -ceq '--task' -or `
        $Argument -ceq '--relevance-backend') {
        $Value = if ($Index + 1 -lt $args.Count) { [string]$args[$Index + 1] } else { '' }
        $Index += 1
        if ($Argument -ceq '--path') {
            $PathValues += $Value
        }
        elseif ($Argument -ceq '--task') {
            $TaskValues += $Value
        }
        else {
            $BackendValues += $Value
        }
    }
    elseif ($Argument.StartsWith('--path=', [StringComparison]::Ordinal)) {
        $PathValues += $Argument.Substring('--path='.Length)
    }
    elseif ($Argument.StartsWith('--task=', [StringComparison]::Ordinal)) {
        $TaskValues += $Argument.Substring('--task='.Length)
    }
    elseif ($Argument.StartsWith('--relevance-backend=', [StringComparison]::Ordinal)) {
        $BackendValues += $Argument.Substring('--relevance-backend='.Length)
    }
    elseif ($Argument -ceq '--model-dir' -or `
        $Argument.StartsWith('--model-dir=', [StringComparison]::Ordinal)) {
        $ModelOverrideRequested = $true
        if ($Argument -ceq '--model-dir' -and $Index + 1 -lt $args.Count) {
            $Index += 1
        }
    }
    else {
        $UnexpectedArguments += $Argument
    }
}

if (@('health', 'scan', 'analyze') -cnotcontains $Command -or $JsonCount -ne 1 -or `
    $UnexpectedArguments.Count -ne 0) {
    Stop-Airlock -Code 'INVALID_ARGUMENTS' `
        -Message 'The Qoder production entry accepts only its documented JSON command form.' `
        -ExitCode 1
}
if ($ModelOverrideRequested) {
    Stop-Airlock -Code 'AIRLOCK_MODEL_OVERRIDE_NOT_ALLOWED' `
        -Message 'The Qoder production entry uses its installed, verified model directory.' `
        -ExitCode 1
}
if ($Command -eq 'health') {
    if ($PathValues.Count -ne 0 -or $TaskValues.Count -ne 0 -or `
        $BackendValues.Count -ne 0 -or $args.Count -ne 2) {
        Stop-Airlock -Code 'INVALID_ARGUMENTS' `
            -Message 'The Qoder production entry accepts only its documented JSON command form.' `
            -ExitCode 1
    }
}
elseif ($Command -eq 'scan') {
    if ($PathValues.Count -ne 1 -or $TaskValues.Count -ne 0 -or `
        $BackendValues.Count -ne 0) {
        Stop-Airlock -Code 'INVALID_ARGUMENTS' `
            -Message 'The Qoder production entry accepts only its documented JSON command form.' `
            -ExitCode 1
    }
}
else {
    if ($PathValues.Count -ne 1 -or $TaskValues.Count -ne 1 -or `
        [string]::IsNullOrWhiteSpace([string]$TaskValues[0])) {
        Stop-Airlock -Code 'INVALID_ARGUMENTS' `
            -Message 'The Qoder production entry accepts only its documented JSON command form.' `
            -ExitCode 1
    }
    if ($BackendValues.Count -ne 1 -or $BackendValues[0] -cne 'openvino') {
        Stop-Airlock -Code 'AIRLOCK_OPENVINO_REQUIRED' `
            -Message 'The Qoder production analyze entry requires explicit OpenVINO inference.' `
            -ExitCode 1
    }
    $RequestedOpenVINO = $true
}
if ($Command -ne 'health' -and `
    -not (Test-AirlockAbsoluteWindowsPath -Value ([string]$PathValues[0]))) {
    Stop-Airlock -Code 'AIRLOCK_ABSOLUTE_PATH_REQUIRED' `
        -Message 'The Qoder production entry requires one explicit absolute Windows target path.' `
        -ExitCode 1
}
if ($RequestedOpenVINO) {
    $CliArguments += @('--model-dir', $ModelDir)
}

try {
    . (Join-Path $PSScriptRoot 'windows_job.ps1')
}
catch {
    Stop-Airlock -Code 'AIRLOCK_PROCESS_ISOLATION_FAILED' `
        -Message 'AI Airlock could not initialize bounded process isolation.'
}

$PackageStamp = Get-PackageStamp
if ([string]::IsNullOrWhiteSpace([string]$PackageStamp)) {
    Stop-Airlock -Code 'AIRLOCK_PACKAGE_INVALID' `
        -Message 'AI Airlock is missing a readable package manifest.'
}

$RuntimeReady = (Test-ReadyMarker -ExpectedStamp $PackageStamp) -and `
    (Test-AirlockRuntime) -and (Test-AirlockOpenVINOReady)
if (-not $RuntimeReady) {
    try {
        $BootstrapMutex = [System.Threading.Mutex]::new(
            $false,
            'Local\AI-Airlock-Bootstrap-v0.1'
        )
    }
    catch {
        Stop-Airlock -Code 'AIRLOCK_BOOTSTRAP_LOCK_FAILED' `
            -Message 'AI Airlock could not initialize its bounded bootstrap lock.'
    }
    $BootstrapLockTaken = $false
    try {
        try {
            $BootstrapLockTaken = $BootstrapMutex.WaitOne(1200000)
        }
        catch [System.Threading.AbandonedMutexException] {
            $BootstrapLockTaken = $true
        }
        if (-not $BootstrapLockTaken) {
            Stop-Airlock -Code 'AIRLOCK_BOOTSTRAP_BUSY_TIMEOUT' `
                -Message 'AI Airlock waited 1200 seconds for another bootstrap to finish.'
        }

        # Another process may have completed bootstrap while this process waited.
        $RuntimeReady = (Test-ReadyMarker -ExpectedStamp $PackageStamp) -and `
            (Test-AirlockRuntime) -and (Test-AirlockOpenVINOReady)
        if (-not $RuntimeReady) {
            if (Test-Path -LiteralPath $ReadyMarker -PathType Leaf) {
                Remove-Item -LiteralPath $ReadyMarker -Force -ErrorAction SilentlyContinue
            }

            if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
                $BootstrapExe = $null
                $BootstrapPrefix = @()

                $PyLauncher = Get-Command 'py.exe' -CommandType Application `
                    -ErrorAction SilentlyContinue | Select-Object -First 1
                $PythonExecutable = Get-Command 'python.exe' -CommandType Application `
                    -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($null -ne $PyLauncher -and `
                    (Test-Python312 -Executable $PyLauncher.Source -Prefix @('-3.12'))) {
                    $BootstrapExe = $PyLauncher.Source
                    $BootstrapPrefix = @('-3.12')
                }
                elseif ($null -ne $PythonExecutable -and `
                    (Test-Python312 -Executable $PythonExecutable.Source)) {
                    $BootstrapExe = $PythonExecutable.Source
                }

                if ($null -eq $BootstrapExe) {
                    Stop-Airlock -Code 'AIRLOCK_PYTHON_NOT_FOUND' `
                        -Message 'Python 3.12 is required to initialize AI Airlock.'
                }

                Write-AirlockProgress 'AI Airlock: creating an isolated Python 3.12 environment...'
                $Creation = Invoke-BoundedProcess -Executable $BootstrapExe `
                    -ProcessArguments (@($BootstrapPrefix) + @('-m', 'venv', $VenvDir)) `
                    -TimeoutMilliseconds 120000
                if ($Creation.TimedOut) {
                    Stop-Airlock -Code 'AIRLOCK_BOOTSTRAP_TIMEOUT' `
                        -Message 'AI Airlock runtime initialization exceeded 120 seconds.'
                }
                if (-not $Creation.Started -or $Creation.ExitCode -ne 0 -or `
                    -not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
                    Stop-Airlock -Code 'AIRLOCK_BOOTSTRAP_FAILED' `
                        -Message 'AI Airlock could not create its isolated Python 3.12 runtime.'
                }
            }

            if (-not (Test-Python312 -Executable $VenvPython)) {
                Stop-Airlock -Code 'AIRLOCK_PYTHON_VERSION_UNSUPPORTED' `
                    -Message 'The installed AI Airlock environment is not Python 3.12; recreate .venv.'
            }

            Write-AirlockProgress 'AI Airlock: installing local OpenVINO runtime dependencies...'
            $OpenVINOInstallTarget = '{0}[openvino]' -f $ProjectRoot
            $Install = Invoke-BoundedProcess -Executable $VenvPython -ProcessArguments @(
                '-m', 'pip', '--disable-pip-version-check', '--no-input', '--retries', '1',
                '--timeout', '30', 'install', '--editable', $OpenVINOInstallTarget
            ) -TimeoutMilliseconds 600000
            if ($Install.TimedOut) {
                Stop-Airlock -Code 'AIRLOCK_DEPENDENCY_INSTALL_TIMEOUT' `
                    -Message 'AI Airlock dependency installation exceeded 600 seconds.'
            }
            if (-not $Install.Started -or $Install.ExitCode -ne 0) {
                Stop-Airlock -Code 'AIRLOCK_DEPENDENCY_INSTALL_FAILED' `
                    -Message 'AI Airlock could not install its local runtime dependencies.'
            }
            if (-not (Test-AirlockRuntime)) {
                Stop-Airlock -Code 'AIRLOCK_RUNTIME_UNAVAILABLE' `
                    -Message 'The AI Airlock runtime or a required dependency is unavailable.'
            }

            if (-not (Test-AirlockOpenVINOReady)) {
                Write-AirlockProgress 'AI Airlock: preparing the pinned local embedding model...'
                $ModelSetup = Invoke-BoundedProcess -Executable $VenvPython -ProcessArguments @(
                    '-m', 'airlock.relevance.model_setup', '--output', $ModelDir
                ) -TimeoutMilliseconds 900000
                if ($ModelSetup.TimedOut) {
                    Stop-Airlock -Code 'AIRLOCK_MODEL_PREPARATION_TIMEOUT' `
                        -Message 'AI Airlock model preparation exceeded 900 seconds.'
                }
                if (-not $ModelSetup.Started -or $ModelSetup.ExitCode -ne 0) {
                    Stop-Airlock -Code 'AIRLOCK_MODEL_PREPARATION_FAILED' `
                        -Message 'AI Airlock could not prepare its pinned local embedding model.'
                }
            }
            if (-not (Test-AirlockOpenVINOReady)) {
                Stop-Airlock -Code 'AIRLOCK_OPENVINO_UNAVAILABLE' `
                    -Message 'AI Airlock could not verify its OpenVINO runtime and local model.'
            }

            try {
                $ReadyMarkerTemp = "$ReadyMarker.$PID.tmp"
                Set-Content -LiteralPath $ReadyMarkerTemp -Value $PackageStamp `
                    -Encoding UTF8 -NoNewline
                Move-Item -LiteralPath $ReadyMarkerTemp -Destination $ReadyMarker -Force
            }
            catch {
                if (-not [string]::IsNullOrWhiteSpace([string]$ReadyMarkerTemp)) {
                    Remove-Item -LiteralPath $ReadyMarkerTemp -Force `
                        -ErrorAction SilentlyContinue
                }
                Stop-Airlock -Code 'AIRLOCK_BOOTSTRAP_FAILED' `
                    -Message 'AI Airlock could not finalize its isolated runtime.'
            }
        }
    }
    finally {
        if ($BootstrapLockTaken) {
            try {
                $BootstrapMutex.ReleaseMutex()
            }
            catch {
                # Process exit still releases an abandoned OS mutex.
            }
        }
        $BootstrapMutex.Dispose()
    }
}

$Invocation = Invoke-BoundedProcess -Executable $VenvPython `
    -ProcessArguments (@('-m', 'airlock.cli') + $CliArguments) `
    -TimeoutMilliseconds 120000
if (-not $Invocation.Started) {
    Stop-Airlock -Code 'AIRLOCK_CLI_LAUNCH_FAILED' `
        -Message 'AI Airlock could not start the local CLI.'
}
if ($Invocation.TimedOut) {
    Stop-Airlock -Code 'AIRLOCK_TIMEOUT' `
        -Message 'AI Airlock exceeded the 120 second local execution limit.'
}
if ($Invocation.OutputLimitExceeded) {
    Stop-Airlock -Code 'AIRLOCK_OUTPUT_LIMIT_EXCEEDED' `
        -Message 'AI Airlock exceeded the bounded machine-readable output limit.'
}

$StdoutText = $Invocation.Stdout.Trim()
$StderrText = $Invocation.Stderr.Trim()
$Utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
if ($Utf8WithoutBom.GetByteCount($StdoutText) -gt 4194304 -or `
    $Utf8WithoutBom.GetByteCount($StderrText) -gt 4194304) {
    Stop-Airlock -Code 'AIRLOCK_OUTPUT_LIMIT_EXCEEDED' `
        -Message 'AI Airlock exceeded the bounded machine-readable output limit.'
}
if ($Invocation.ExitCode -ne 0) {
    if (@(1, 2) -notcontains ([int]$Invocation.ExitCode)) {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an unsupported process exit code.'
    }
    if (-not [string]::IsNullOrWhiteSpace($StdoutText) -or [string]::IsNullOrWhiteSpace($StderrText)) {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an invalid machine-readable error.'
    }
    try {
        $ParsedError = $StderrText | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an invalid machine-readable error.'
    }
    if (-not (Test-JsonProperty -Object $ParsedError -Name 'schema_version') -or `
        $ParsedError.schema_version -cne '0.1' -or `
        -not (Test-JsonProperty -Object $ParsedError -Name 'error') -or `
        -not (Test-JsonProperty -Object $ParsedError.error -Name 'code') -or `
        -not (Test-JsonProperty -Object $ParsedError.error -Name 'message') -or `
        -not ($ParsedError.error.code -is [string]) -or `
        -not ($ParsedError.error.message -is [string]) -or `
        [string]::IsNullOrWhiteSpace($ParsedError.error.code) -or `
        [string]::IsNullOrWhiteSpace($ParsedError.error.message)) {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an invalid machine-readable error.'
    }
    if (($Invocation.ExitCode -eq 2 -and `
        $ParsedError.error.code -cne 'AIRLOCK_RUNTIME_UNAVAILABLE') -or `
        ($Invocation.ExitCode -eq 1 -and `
        $ParsedError.error.code -ceq 'AIRLOCK_RUNTIME_UNAVAILABLE')) {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an invalid machine-readable error.'
    }
    $ErrorGate = Invoke-BoundedProcess -Executable $VenvPython `
        -ProcessArguments @('-m', 'airlock.qoder_gate', '--kind', 'error') `
        -TimeoutMilliseconds 30000 -StandardInputText $StderrText
    if (-not $ErrorGate.Started -or $ErrorGate.TimedOut -or $ErrorGate.ExitCode -ne 0 -or `
        [string]::IsNullOrWhiteSpace($ErrorGate.Stdout) -or `
        -not [string]::IsNullOrWhiteSpace($ErrorGate.Stderr)) {
        Stop-Airlock -Code 'AIRLOCK_INVALID_ERROR_RESPONSE' `
            -Message 'AI Airlock returned an invalid machine-readable error.'
    }
    [Console]::Error.WriteLine($ErrorGate.Stdout.Trim())
    exit $Invocation.ExitCode
}

if (-not [string]::IsNullOrWhiteSpace($StderrText) -or [string]::IsNullOrWhiteSpace($StdoutText)) {
    Stop-Airlock -Code 'AIRLOCK_INVALID_JSON' `
        -Message 'AI Airlock returned an invalid machine-readable response.'
}
try {
    $Parsed = $StdoutText | ConvertFrom-Json -ErrorAction Stop
}
catch {
    Stop-Airlock -Code 'AIRLOCK_INVALID_JSON' `
        -Message 'AI Airlock returned an invalid machine-readable response.'
}
if (-not (Test-JsonProperty -Object $Parsed -Name 'schema_version') -or `
    $Parsed.schema_version -cne '0.1') {
    Stop-Airlock -Code 'AIRLOCK_INVALID_JSON' `
        -Message 'AI Airlock returned an invalid machine-readable response.'
}

$AllowedDecisions = @('ALLOW', 'ALLOW_WITH_TRANSFORM', 'REQUIRE_CONFIRMATION', 'BLOCK')
$AllowedRisks = @('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
$FileProperties = @('inspected', 'skipped', 'total_bytes')
$SecurityProperties = @(
    'api_keys', 'bearer_tokens', 'jwt_tokens', 'aws_keys', 'private_keys',
    'database_credentials', 'password_assignments', 'emails', 'phones',
    'chinese_ids', 'ip_addresses', 'pii_items', 'prompt_injections',
    'data_exfiltration_attempts', 'blocked_instructions'
)
$ValidShape = $false
if ($Command -eq 'health') {
    $ValidShape = (Test-JsonObjectWithProperties -Object $Parsed -Names @(
            'schema_version', 'status', 'version', 'commands', 'inference'
        )) -and `
        $Parsed.status -ceq 'ok' -and `
        (Test-JsonStringProperty -Object $Parsed -Name 'version') -and `
        (Test-JsonStringArray -Values $Parsed.commands) -and `
        (Test-InferenceMetadata -Inference $Parsed.inference)
}
elseif ($Command -eq 'scan') {
    $ValidShape = (Test-JsonObjectWithProperties -Object $Parsed -Names @(
            'schema_version', 'decision', 'risk_level', 'files', 'findings',
            'security', 'inference'
        )) -and `
        $AllowedDecisions -ccontains [string]$Parsed.decision -and `
        $AllowedRisks -ccontains [string]$Parsed.risk_level -and `
        (Test-JsonNonNegativeIntegerProperties -Object $Parsed.files `
            -Names $FileProperties) -and `
        (Test-FindingArray -Findings $Parsed.findings) -and `
        (Test-JsonNonNegativeIntegerProperties -Object $Parsed.security `
            -Names $SecurityProperties) -and `
        (Test-InferenceMetadata -Inference $Parsed.inference)
}
elseif ($Command -eq 'analyze') {
    $ValidShape = (Test-JsonObjectWithProperties -Object $Parsed -Names @(
            'schema_version', 'task', 'decision', 'risk_level', 'files',
            'safe_context', 'security', 'privacy', 'efficiency', 'inference'
        )) -and `
        (Test-JsonStringProperty -Object $Parsed -Name 'task') -and `
        $AllowedDecisions -ccontains [string]$Parsed.decision -and `
        $AllowedRisks -ccontains [string]$Parsed.risk_level -and `
        (Test-JsonNonNegativeIntegerProperties -Object $Parsed.files `
            -Names $FileProperties) -and `
        (Test-JsonObjectWithProperties -Object $Parsed.safe_context `
            -Names @('summary', 'facts', 'selection_method')) -and `
        $null -eq $Parsed.safe_context.summary -and `
        (Test-JsonStringProperty -Object $Parsed.safe_context -Name 'selection_method') -and `
        (Test-FactArray -Facts $Parsed.safe_context.facts) -and `
        (-not (Test-JsonProperty -Object $Parsed.safe_context -Name 'coverage_warning') -or `
            ((Test-JsonStringProperty -Object $Parsed.safe_context `
                -Name 'coverage_warning'))) -and `
        (Test-JsonNonNegativeIntegerProperties -Object $Parsed.security `
            -Names $SecurityProperties) -and `
        (Test-JsonNonNegativeIntegerProperties -Object $Parsed.privacy `
            -Names @('raw_sensitive_spans_forwarded')) -and `
        (Test-JsonObjectWithProperties -Object $Parsed.efficiency -Names @(
            'original_tokens_estimated', 'capsule_tokens_estimated',
            'reduction_ratio', 'estimator'
        )) -and `
        (Test-JsonIntegerValue -Value $Parsed.efficiency.original_tokens_estimated) -and `
        (Test-JsonIntegerValue -Value $Parsed.efficiency.capsule_tokens_estimated) -and `
        (Test-JsonFiniteNumberValue -Value $Parsed.efficiency.reduction_ratio) -and `
        (Test-JsonStringProperty -Object $Parsed.efficiency -Name 'estimator') -and `
        (Test-InferenceMetadata -Inference $Parsed.inference)
}
if (-not $ValidShape) {
    Stop-Airlock -Code 'AIRLOCK_INVALID_JSON' `
        -Message 'AI Airlock returned an invalid machine-readable response.'
}

$GateArguments = @(
    '-m', 'airlock.qoder_gate', '--kind', 'success', '--command', $Command
)
if ($RequestedOpenVINO -or $Command -eq 'health') {
    $GateArguments += '--require-openvino'
}
$SuccessGate = Invoke-BoundedProcess -Executable $VenvPython `
    -ProcessArguments $GateArguments -TimeoutMilliseconds 30000 `
    -StandardInputText $StdoutText
if (-not $SuccessGate.Started -or $SuccessGate.TimedOut -or `
    $SuccessGate.ExitCode -ne 0 -or `
    [string]::IsNullOrWhiteSpace($SuccessGate.Stdout) -or `
    -not [string]::IsNullOrWhiteSpace($SuccessGate.Stderr)) {
    Stop-Airlock -Code 'AIRLOCK_INVALID_JSON' `
        -Message 'AI Airlock returned an invalid machine-readable response.'
}

[Console]::Out.WriteLine($SuccessGate.Stdout.Trim())
exit 0
