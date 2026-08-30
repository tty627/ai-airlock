param(
    [Parameter(Mandatory = $true)][string]$ControlPipeName
)

$ErrorActionPreference = 'Stop'
$ControlPipe = $null
$TargetProcess = $null
$StatusSent = $false
$CompletionSent = $false
$ExitCode = 251

try {
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
}
catch {
    exit 251
}

function Read-ExactBytes {
    param(
        [Parameter(Mandatory = $true)][System.IO.Stream]$Stream,
        [Parameter(Mandatory = $true)][int]$Count
    )

    $Buffer = [byte[]]::new($Count)
    $Offset = 0
    while ($Offset -lt $Count) {
        $ReadCount = $Stream.Read($Buffer, $Offset, $Count - $Offset)
        if ($ReadCount -le 0) {
            throw 'The launcher control pipe ended before the frame was complete.'
        }
        $Offset += $ReadCount
    }
    return $Buffer
}

function Send-LauncherStatus {
    param([Parameter(Mandatory = $true)][ValidateRange(1, 3)][int]$Status)

    $ControlPipe.WriteByte([byte]$Status)
    $ControlPipe.Flush()
    $script:StatusSent = $true
}

function Send-LauncherCompletion {
    param(
        [Parameter(Mandatory = $true)][ValidateSet(3, 4)][int]$Status,
        [int]$TargetExitCode = 0
    )

    $Frame = [byte[]]::new(5)
    $Frame[0] = [byte]$Status
    $ExitCodeBytes = [System.BitConverter]::GetBytes($TargetExitCode)
    [System.Buffer]::BlockCopy($ExitCodeBytes, 0, $Frame, 1, 4)
    $ControlPipe.Write($Frame, 0, $Frame.Length)
    $ControlPipe.Flush()
    $script:CompletionSent = $true
}

try {
    $ControlPipe = [System.IO.Pipes.NamedPipeClientStream]::new(
        '.',
        $ControlPipeName,
        [System.IO.Pipes.PipeDirection]::InOut,
        [System.IO.Pipes.PipeOptions]::None
    )
    $ControlPipe.Connect(10000)

    $LengthBytes = Read-ExactBytes -Stream $ControlPipe -Count 4
    $PayloadLength = [System.BitConverter]::ToInt32($LengthBytes, 0)
    if ($PayloadLength -le 0 -or $PayloadLength -gt 131072) {
        throw 'The launcher control frame length is invalid.'
    }
    $PayloadBytes = Read-ExactBytes -Stream $ControlPipe -Count $PayloadLength
    $PayloadText = [System.Text.UTF8Encoding]::new($false, $true).GetString($PayloadBytes)
    $Descriptor = $PayloadText | ConvertFrom-Json -ErrorAction Stop

    $PropertyNames = @($Descriptor.PSObject.Properties.Name | Sort-Object)
    $ExpectedPropertyNames = @(
        'argument_text',
        'executable',
        'schema_version',
        'working_directory'
    )
    if (($PropertyNames -join "`n") -cne ($ExpectedPropertyNames -join "`n") -or `
        [string]$Descriptor.schema_version -cne '1' -or `
        [string]::IsNullOrWhiteSpace([string]$Descriptor.executable) -or `
        [string]::IsNullOrWhiteSpace([string]$Descriptor.working_directory)) {
        throw 'The launcher descriptor is invalid.'
    }

    try {
        $StartParameters = @{
            FilePath = [string]$Descriptor.executable
            WorkingDirectory = [string]$Descriptor.working_directory
            NoNewWindow = $true
            PassThru = $true
            ErrorAction = 'Stop'
        }
        $ArgumentText = [string]$Descriptor.argument_text
        if (-not [string]::IsNullOrEmpty($ArgumentText)) {
            $StartParameters.ArgumentList = @($ArgumentText)
        }
        $TargetProcess = Start-Process @StartParameters
        # Windows PowerShell 5.1 must open the process handle before exit or
        # its Start-Process result can lose the real native exit code.
        $TargetHandle = $TargetProcess.Handle
    }
    catch {
        Send-LauncherStatus -Status 2
        $ExitCode = 250
        throw [System.ComponentModel.Win32Exception]::new('Target process start failed.')
    }

    Send-LauncherStatus -Status 1
    $TargetProcess.WaitForExit()
    $TargetProcess.Refresh()
    $ExitCode = $TargetProcess.ExitCode
    Send-LauncherCompletion -Status 4 -TargetExitCode $ExitCode
}
catch [System.ComponentModel.Win32Exception] {
    # A target-start failure already sent status 2. Keep all launcher errors off
    # stdout/stderr; the trusted parent owns the fixed public error mapping.
    if ($ExitCode -ne 250 -and $null -ne $ControlPipe -and `
        $ControlPipe.IsConnected -and $StatusSent -and -not $CompletionSent) {
        try {
            Send-LauncherCompletion -Status 3
        }
        catch {
        }
        $ExitCode = 251
    }
}
catch {
    if ($null -ne $ControlPipe -and $ControlPipe.IsConnected -and `
        $StatusSent -and -not $CompletionSent) {
        try {
            Send-LauncherCompletion -Status 3
        }
        catch {
        }
    }
    elseif ($null -ne $ControlPipe -and $ControlPipe.IsConnected -and -not $StatusSent) {
        try {
            Send-LauncherStatus -Status 3
        }
        catch {
        }
    }
    $ExitCode = 251
}
finally {
    if ($null -ne $TargetProcess) {
        $TargetProcess.Dispose()
    }
    if ($null -ne $ControlPipe) {
        $ControlPipe.Dispose()
    }
}

exit $ExitCode
