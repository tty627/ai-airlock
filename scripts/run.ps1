$ErrorActionPreference = 'Stop'

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$VenvDir = Join-Path $ProjectRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    try {
        $BootstrapExe = $null
        $BootstrapPrefix = @()

        if (Get-Command 'py' -ErrorAction SilentlyContinue) {
            & py -3.12 -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) {
                $BootstrapExe = 'py'
                $BootstrapPrefix = @('-3.12')
            }
        }

        if (($null -eq $BootstrapExe) -and (Get-Command 'python' -ErrorAction SilentlyContinue)) {
            & python -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' 1>$null 2>$null
            if ($LASTEXITCODE -eq 0) {
                $BootstrapExe = 'python'
            }
        }

        if ($null -eq $BootstrapExe) {
            throw 'required interpreter unavailable'
        }

        [Console]::Error.WriteLine('AI Airlock: creating an isolated Python 3.12 environment...')
        & $BootstrapExe @BootstrapPrefix -m venv $VenvDir 1>&2
        if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }

        [Console]::Error.WriteLine('AI Airlock: installing local package and runtime dependencies...')
        & $VenvPython -m pip --disable-pip-version-check install -e $ProjectRoot 1>&2
        if ($LASTEXITCODE -ne 0) { throw 'package installation failed' }
    }
    catch {
        [Console]::Error.WriteLine('{"error":"AIRLOCK_BOOTSTRAP_FAILED"}')
        exit 1
    }
}

& $VenvPython -m airlock.cli @args
exit $LASTEXITCODE
