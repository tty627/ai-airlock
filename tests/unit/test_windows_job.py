from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = PROJECT_ROOT / "scripts" / "run.ps1"
WINDOWS_JOB_HELPER = PROJECT_ROOT / "scripts" / "windows_job.ps1"
GATED_LAUNCHER = PROJECT_ROOT / "scripts" / "windows_gated_launcher.ps1"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


def _windows_powershells() -> tuple[str, ...]:
    if os.name != "nt":
        return ()

    discovered: list[str] = []
    for executable in ("powershell.exe", "pwsh.exe"):
        resolved = shutil.which(executable)
        if resolved is not None and resolved.casefold() not in {
            existing.casefold() for existing in discovered
        }:
            discovered.append(resolved)
    return tuple(discovered)


def _ps_single_quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _production_controller_prefix() -> str:
    return f"""
$ErrorActionPreference = 'Stop'
$JsonRequested = $true
$ProjectRoot = {_ps_single_quoted(str(PROJECT_ROOT))}
$WindowsGatedLauncherPath = {_ps_single_quoted(str(GATED_LAUNCHER))}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
. {_ps_single_quoted(str(WINDOWS_JOB_HELPER))}

$ParserTokens = $null
$ParserErrors = $null
$WrapperAst = [System.Management.Automation.Language.Parser]::ParseFile(
    {_ps_single_quoted(str(WRAPPER))},
    [ref]$ParserTokens,
    [ref]$ParserErrors
)
if ($ParserErrors.Count -ne 0) {{
    throw 'The production wrapper did not parse.'
}}
$RequiredFunctions = @(
    'Write-AirlockError',
    'Stop-Airlock',
    'ConvertTo-NativeArgument',
    'Stop-ProcessTreeBounded',
    'Invoke-BoundedProcess'
)
$Definitions = $WrapperAst.FindAll({{
    param($Node)
    $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and `
        $RequiredFunctions -ccontains $Node.Name
}}, $true)
if ($Definitions.Count -ne $RequiredFunctions.Count) {{
    throw 'The bounded-process production functions were not found.'
}}
foreach ($Definition in $Definitions) {{
    Invoke-Expression $Definition.Extent.Text
}}
""".lstrip()


def test_bounded_process_uses_gated_launcher_and_waits_for_empty_job() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    helper_source = WINDOWS_JOB_HELPER.read_text(encoding="utf-8")
    bounded_start = source.index("function Invoke-BoundedProcess")
    bounded_end = source.index("function Test-AirlockAbsoluteWindowsPath", bounded_start)
    bounded = source[bounded_start:bounded_end]

    gated_start = bounded.index("$Session = Start-AirlockGatedProcess")
    mark_started = bounded.index("$ProcessStarted = $true", gated_start)
    process_exited = bounded.index("$ProcessExited = $Process.HasExited", mark_started)
    close_exited_job = bounded.index(
        "Complete-AirlockKillOnCloseJob -Job $KillOnCloseJob", process_exited
    )
    pipe_break = bounded.index(
        "if ($ProcessExited -and $StdoutComplete -and $StderrComplete -and",
        close_exited_job,
    )
    catch_block = bounded.index("    catch {\n        if ($ProcessStarted", mark_started)
    fixed_error = bounded.index("AIRLOCK_PROCESS_ISOLATION_FAILED", catch_block)
    finally_block = bounded.index("    finally {\n        Close-AirlockKillOnCloseJob", catch_block)
    close_job = bounded.index("Close-AirlockKillOnCloseJob -Job $KillOnCloseJob", finally_block)
    dispose_process = bounded.index("$Process.Dispose()", close_job)

    assert gated_start < mark_started < process_exited < close_exited_job < pipe_break
    assert mark_started < catch_block < fixed_error < finally_block < close_job < dispose_process
    assert "AIRLOCK_PROCESS_ISOLATION_FAILED" in source
    helper_start = helper_source.index("function Start-AirlockGatedProcess")
    helper = helper_source[helper_start:]
    launcher_start = helper.index("if (-not $Process.Start())")
    assign_launcher = helper.index("Register-AirlockProcessWithKillOnCloseJob", launcher_start)
    descriptor = helper.index("$Descriptor = [ordered]", assign_launcher)
    send_descriptor = helper.index("$ControlPipe.WriteAsync", descriptor)
    assert launcher_start < assign_launcher < descriptor < send_descriptor
    assert source.index("$Command = if ($args.Count") < source.index(
        ". (Join-Path $PSScriptRoot 'windows_job.ps1')"
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: Path(executable).stem,
)
def test_closing_job_kills_nonce_child_inherited_from_exited_parent(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    nonce = f"airlock-job-{uuid.uuid4().hex}"
    controller = tmp_path / "job-inheritance-regression.ps1"
    controller.write_text(
        f"""
param(
    [ValidateSet('controller', 'parent', 'child')][string]$Mode = 'controller',
    [string]$Token = ''
)

$ErrorActionPreference = 'Stop'
. {_ps_single_quoted(str(WINDOWS_JOB_HELPER))}
$PowerShellExecutable = {_ps_single_quoted(powershell_executable)}
$Nonce = {_ps_single_quoted(nonce)}
if ([string]::IsNullOrWhiteSpace($Token)) {{
    $Token = $Nonce
}}
$GoPath = Join-Path $PSScriptRoot ($Token + '.go')
$PidPath = Join-Path $PSScriptRoot ($Token + '.pid')
$ReadyPath = Join-Path $PSScriptRoot ($Token + '.ready')

function New-TestProcessStartInfo {{
    param([Parameter(Mandatory = $true)][string]$ChildMode)

    $Info = [System.Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $PowerShellExecutable
    $QuotedScript = '"' + $PSCommandPath.Replace('"', '\\"') + '"'
    $Info.Arguments = '-NoLogo -NoProfile -NonInteractive -File ' + $QuotedScript + `
        ' -Mode ' + $ChildMode + ' -Token ' + $Token
    $Info.UseShellExecute = $false
    $Info.CreateNoWindow = $true
    if ($ChildMode -ceq 'parent') {{
        $Info.RedirectStandardOutput = $true
        $Info.RedirectStandardError = $true
    }}
    return $Info
}}

if ($Mode -ceq 'child') {{
    [System.IO.File]::WriteAllText($ReadyPath, ([string]$PID + '|' + $Token))
    while ($true) {{
        Start-Sleep -Milliseconds 250
    }}
}}

if ($Mode -ceq 'parent') {{
    $GoDeadline = [DateTime]::UtcNow.AddSeconds(15)
    while (-not (Test-Path -LiteralPath $GoPath -PathType Leaf)) {{
        if ([DateTime]::UtcNow -ge $GoDeadline) {{
            throw 'The parent did not receive its assignment signal.'
        }}
        Start-Sleep -Milliseconds 25
    }}

    $Child = [System.Diagnostics.Process]::new()
    $Child.StartInfo = New-TestProcessStartInfo -ChildMode 'child'
    try {{
        if (-not $Child.Start()) {{
            throw 'The nonce child did not start.'
        }}
        [System.IO.File]::WriteAllText($PidPath, [string]$Child.Id)
    }}
    finally {{
        $Child.Dispose()
    }}
    exit 0
}}

$Job = $null
$Parent = $null
$NonceChild = $null
$ParentStdoutTask = $null
$ParentStderrTask = $null
$Result = $null
try {{
    $Job = New-AirlockKillOnCloseJob
    if ($null -eq $Job) {{
        throw 'The Windows Job Object was not created.'
    }}

    $Parent = [System.Diagnostics.Process]::new()
    $Parent.StartInfo = New-TestProcessStartInfo -ChildMode 'parent'
    if (-not $Parent.Start()) {{
        throw 'The parent process did not start.'
    }}
    Register-AirlockProcessWithKillOnCloseJob -Job $Job -Process $Parent
    $ParentStdoutTask = $Parent.StandardOutput.ReadToEndAsync()
    $ParentStderrTask = $Parent.StandardError.ReadToEndAsync()
    [System.IO.File]::WriteAllText($GoPath, 'assigned')

    if (-not $Parent.WaitForExit(15000) -or $Parent.ExitCode -ne 0) {{
        throw 'The assigned parent process did not exit cleanly.'
    }}

    $ReadyDeadline = [DateTime]::UtcNow.AddSeconds(15)
    while (-not (Test-Path -LiteralPath $PidPath -PathType Leaf) -or `
        -not (Test-Path -LiteralPath $ReadyPath -PathType Leaf)) {{
        if ([DateTime]::UtcNow -ge $ReadyDeadline) {{
            throw 'The inherited nonce child did not become ready.'
        }}
        Start-Sleep -Milliseconds 25
    }}

    $NonceChildId = [int](Get-Content -LiteralPath $PidPath -Raw)
    $ReadyValue = (Get-Content -LiteralPath $ReadyPath -Raw).Trim()
    if ($ReadyValue -cne ([string]$NonceChildId + '|' + $Token)) {{
        throw 'The ready marker does not identify the unique nonce child.'
    }}
    $NonceChild = [System.Diagnostics.Process]::GetProcessById($NonceChildId)
    $ChildAliveAfterParentExit = -not $NonceChild.HasExited
    $PipesHeldAfterParentExit = -not (
        $ParentStdoutTask.IsCompleted -and $ParentStderrTask.IsCompleted
    )

    Close-AirlockKillOnCloseJob -Job $Job
    $Job = $null
    $ChildKilledByJobClose = $NonceChild.WaitForExit(10000)
    $ParentPipeTasks = [System.Threading.Tasks.Task[]]@(
        $ParentStdoutTask, $ParentStderrTask
    )
    $PipesClosedByJobClose = [System.Threading.Tasks.Task]::WaitAll(
        $ParentPipeTasks, 10000
    )

    $Result = [ordered]@{{
        token = $Token
        parent_exited = $Parent.HasExited
        child_alive_after_parent_exit = $ChildAliveAfterParentExit
        pipes_held_after_parent_exit = $PipesHeldAfterParentExit
        child_killed_by_job_close = $ChildKilledByJobClose
        pipes_closed_by_job_close = $PipesClosedByJobClose
    }}
}}
finally {{
    Close-AirlockKillOnCloseJob -Job $Job
    if ($null -ne $Parent -and -not $Parent.HasExited) {{
        $Parent.Kill()
        $Parent.WaitForExit(5000) | Out-Null
    }}
    if ($null -ne $NonceChild -and -not $NonceChild.HasExited) {{
        $NonceChild.Kill()
        $NonceChild.WaitForExit(5000) | Out-Null
    }}
    if ($null -ne $Parent) {{
        $Parent.Dispose()
    }}
    if ($null -ne $NonceChild) {{
        $NonceChild.Dispose()
    }}
    Remove-Item -LiteralPath $GoPath, $PidPath, $ReadyPath `
        -Force -ErrorAction SilentlyContinue
}}

$Result | ConvertTo-Json -Compress
""".lstrip(),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result == {
        "token": nonce,
        "parent_exited": True,
        "child_alive_after_parent_exit": True,
        "pipes_held_after_parent_exit": True,
        "child_killed_by_job_close": True,
        "pipes_closed_by_job_close": True,
    }


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: f"bounded-{Path(executable).stem}",
)
def test_bounded_process_closes_inherited_pipes_without_waiting_for_timeout(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    nonce = f"airlock-pipe-{uuid.uuid4().hex}"
    fixture = tmp_path / "orphan-pipe-fixture.ps1"
    child_pid_path = tmp_path / f"{nonce}.pid"
    child_ready_path = tmp_path / f"{nonce}.ready"
    fixture.write_text(
        """
param(
    [ValidateSet('parent', 'child')][string]$Mode,
    [string]$Token,
    [string]$ChildPidPath,
    [string]$ChildReadyPath
)

$ErrorActionPreference = 'Stop'
if ($Mode -ceq 'child') {
    [System.IO.File]::WriteAllText($ChildReadyPath, ([string]$PID + '|' + $Token))
    while ($true) {
        Start-Sleep -Milliseconds 250
    }
}

# Spawn immediately. The trusted gated launcher, not a timing delay in this
# fixture, must ensure that this parent already belongs to the Job.
$Info = [System.Diagnostics.ProcessStartInfo]::new()
$Info.FileName = (Get-Process -Id $PID).Path
$QuotedScript = '"' + $PSCommandPath.Replace('"', '\\"') + '"'
$Info.Arguments = '-NoLogo -NoProfile -NonInteractive -File ' + $QuotedScript + `
    ' -Mode child -Token ' + $Token + `
    ' -ChildPidPath "' + $ChildPidPath.Replace('"', '\\"') + '"' + `
    ' -ChildReadyPath "' + $ChildReadyPath.Replace('"', '\\"') + '"'
$Info.UseShellExecute = $false
$Info.CreateNoWindow = $true
$Child = [System.Diagnostics.Process]::new()
$Child.StartInfo = $Info
try {
    if (-not $Child.Start()) {
        throw 'The orphan-pipe nonce child did not start.'
    }
    [System.IO.File]::WriteAllText($ChildPidPath, [string]$Child.Id)
}
finally {
    $Child.Dispose()
}

$ReadyDeadline = [DateTime]::UtcNow.AddSeconds(10)
while (-not (Test-Path -LiteralPath $ChildReadyPath -PathType Leaf)) {
    if ([DateTime]::UtcNow -ge $ReadyDeadline) {
        throw 'The orphan-pipe nonce child did not become ready.'
    }
    Start-Sleep -Milliseconds 25
}
exit 0
""".lstrip(),
        encoding="utf-8",
    )

    controller = tmp_path / "invoke-bounded-process-regression.ps1"
    controller.write_text(
        f"""
$ErrorActionPreference = 'Stop'
$JsonRequested = $true
$ProjectRoot = {_ps_single_quoted(str(PROJECT_ROOT))}
$WindowsGatedLauncherPath = {_ps_single_quoted(str(PROJECT_ROOT / "scripts" / "windows_gated_launcher.ps1"))}
. {_ps_single_quoted(str(WINDOWS_JOB_HELPER))}

$ParserTokens = $null
$ParserErrors = $null
$WrapperAst = [System.Management.Automation.Language.Parser]::ParseFile(
    {_ps_single_quoted(str(WRAPPER))},
    [ref]$ParserTokens,
    [ref]$ParserErrors
)
if ($ParserErrors.Count -ne 0) {{
    throw 'The production wrapper did not parse.'
}}
$RequiredFunctions = @(
    'Write-AirlockError',
    'Stop-Airlock',
    'ConvertTo-NativeArgument',
    'Stop-ProcessTreeBounded',
    'Invoke-BoundedProcess'
)
$Definitions = $WrapperAst.FindAll({{
    param($Node)
    $Node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and `
        $RequiredFunctions -ccontains $Node.Name
}}, $true)
if ($Definitions.Count -ne $RequiredFunctions.Count) {{
    throw 'The bounded-process production functions were not found.'
}}
foreach ($Definition in $Definitions) {{
    Invoke-Expression $Definition.Extent.Text
}}

$Watch = [System.Diagnostics.Stopwatch]::StartNew()
$Invocation = Invoke-BoundedProcess `
    -Executable {_ps_single_quoted(powershell_executable)} `
    -ProcessArguments @(
        '-NoLogo', '-NoProfile', '-NonInteractive',
        '-File', {_ps_single_quoted(str(fixture))},
        '-Mode', 'parent',
        '-Token', {_ps_single_quoted(nonce)},
        '-ChildPidPath', {_ps_single_quoted(str(child_pid_path))},
        '-ChildReadyPath', {_ps_single_quoted(str(child_ready_path))}
    ) `
    -TimeoutMilliseconds 5000
$Watch.Stop()

$ChildPid = [int](Get-Content -LiteralPath {_ps_single_quoted(str(child_pid_path))} -Raw)
$ReadyValue = (Get-Content `
    -LiteralPath {_ps_single_quoted(str(child_ready_path))} -Raw).Trim()
$ChildAliveWhenFunctionReturned = $false
try {{
    $Residual = [System.Diagnostics.Process]::GetProcessById($ChildPid)
    try {{
        $ChildAliveWhenFunctionReturned = -not $Residual.HasExited
    }}
    finally {{
        $Residual.Dispose()
    }}
}}
catch [System.ArgumentException] {{
    $ChildAliveWhenFunctionReturned = $false
}}

[ordered]@{{
    token = {_ps_single_quoted(nonce)}
    ready_value = $ReadyValue
    started = $Invocation.Started
    timed_out = $Invocation.TimedOut
    output_limit_exceeded = $Invocation.OutputLimitExceeded
    exit_code = $Invocation.ExitCode
    stdout = $Invocation.Stdout
    stderr = $Invocation.Stderr
    elapsed_milliseconds = $Watch.ElapsedMilliseconds
    child_alive_when_function_returned = $ChildAliveWhenFunctionReturned
}} | ConvertTo-Json -Compress
""".lstrip(),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["token"] == nonce
    assert result["ready_value"].endswith(f"|{nonce}")
    assert result["started"] is True
    assert result["timed_out"] is False
    assert result["output_limit_exceeded"] is False
    assert result["exit_code"] == 0
    assert result["stdout"] == ""
    assert result["stderr"] == ""
    assert result["elapsed_milliseconds"] < 5000
    assert result["child_alive_when_function_returned"] is False


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: f"streams-{Path(executable).stem}",
)
def test_gated_launcher_preserves_unicode_stdin_stdout_and_stderr(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    input_text = "安全输入 with spaces U0001f512"
    input_base64 = base64.b64encode(input_text.encode()).decode("ascii")
    controller = tmp_path / "gated-stream-regression.ps1"
    controller.write_text(
        _production_controller_prefix()
        + f"""
$InputText = [System.Text.UTF8Encoding]::new($false, $true).GetString(
    [System.Convert]::FromBase64String('{input_base64}')
)
$Invocation = Invoke-BoundedProcess `
    -Executable {_ps_single_quoted(str(VENV_PYTHON))} `
    -ProcessArguments @(
        '-c',
        'import sys; data=sys.stdin.read(); sys.stdout.write(data); sys.stderr.write("stderr:\\u4e2d\\u6587"); raise SystemExit(7)'
    ) `
    -StandardInputText $InputText `
    -TimeoutMilliseconds 10000

[ordered]@{{
    started = $Invocation.Started
    timed_out = $Invocation.TimedOut
    output_limit_exceeded = $Invocation.OutputLimitExceeded
    exit_code = $Invocation.ExitCode
    stdout_base64 = [System.Convert]::ToBase64String(
        [System.Text.UTF8Encoding]::new($false).GetBytes($Invocation.Stdout)
    )
    stderr_base64 = [System.Convert]::ToBase64String(
        [System.Text.UTF8Encoding]::new($false).GetBytes($Invocation.Stderr)
    )
}} | ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["started"] is True
    assert result["timed_out"] is False
    assert result["output_limit_exceeded"] is False
    assert result["exit_code"] == 7
    assert base64.b64decode(result["stdout_base64"]).decode() == input_text
    assert base64.b64decode(result["stderr_base64"]).decode() == "stderr:中文"


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: f"timeout-{Path(executable).stem}",
)
def test_timeout_kills_nonreading_parent_and_nonce_descendant(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    nonce = f"airlock-timeout-{uuid.uuid4().hex}"
    child_pid_path = tmp_path / f"{nonce}.pid"
    fixture = tmp_path / "nonreading-parent.py"
    fixture.write_text(
        """
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

pid_path = Path(sys.argv[1])
nonce = sys.argv[2]
child = subprocess.Popen(
    [sys.executable, "-I", "-c", "import time; time.sleep(60)", nonce],
    stdin=subprocess.DEVNULL,
    stdout=None,
    stderr=None,
    close_fds=False,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
pid_path.write_text(str(child.pid), encoding="ascii")
time.sleep(60)
""".lstrip(),
        encoding="utf-8",
    )

    controller = tmp_path / "gated-timeout-regression.ps1"
    controller.write_text(
        _production_controller_prefix()
        + f"""
$Watch = [System.Diagnostics.Stopwatch]::StartNew()
$Invocation = Invoke-BoundedProcess `
    -Executable {_ps_single_quoted(str(VENV_PYTHON))} `
    -ProcessArguments @(
        '-I',
        {_ps_single_quoted(str(fixture))},
        {_ps_single_quoted(str(child_pid_path))},
        {_ps_single_quoted(nonce)}
    ) `
    -StandardInputText ('x' * 1048576) `
    -TimeoutMilliseconds 3000
$Watch.Stop()

$ChildPid = [int](Get-Content -LiteralPath {_ps_single_quoted(str(child_pid_path))} -Raw)
$ChildAliveWhenFunctionReturned = $false
try {{
    $Residual = [System.Diagnostics.Process]::GetProcessById($ChildPid)
    try {{
        $ChildAliveWhenFunctionReturned = -not $Residual.HasExited
    }}
    finally {{
        $Residual.Dispose()
    }}
}}
catch [System.ArgumentException] {{
    $ChildAliveWhenFunctionReturned = $false
}}

[ordered]@{{
    started = $Invocation.Started
    timed_out = $Invocation.TimedOut
    output_limit_exceeded = $Invocation.OutputLimitExceeded
    exit_code = $Invocation.ExitCode
    stdout = $Invocation.Stdout
    stderr = $Invocation.Stderr
    elapsed_milliseconds = $Watch.ElapsedMilliseconds
    child_alive_when_function_returned = $ChildAliveWhenFunctionReturned
}} | ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["started"] is True
    assert result["timed_out"] is True
    assert result["output_limit_exceeded"] is False
    assert result["exit_code"] == 2
    assert result["stdout"] == ""
    assert result["stderr"] == ""
    assert result["elapsed_milliseconds"] < 8000
    assert result["child_alive_when_function_returned"] is False


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: f"output-limit-{Path(executable).stem}",
)
def test_output_limit_kills_writer_and_nonce_descendant(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    nonce = f"airlock-output-{uuid.uuid4().hex}"
    child_pid_path = tmp_path / f"{nonce}.pid"
    fixture = tmp_path / "oversized-writer.py"
    fixture.write_text(
        """
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

pid_path = Path(sys.argv[1])
nonce = sys.argv[2]
child = subprocess.Popen(
    [sys.executable, "-I", "-c", "import time; time.sleep(60)", nonce],
    stdin=subprocess.DEVNULL,
    stdout=None,
    stderr=None,
    close_fds=False,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
pid_path.write_text(str(child.pid), encoding="ascii")
sys.stdout.write("x" * 131072)
sys.stdout.flush()
time.sleep(60)
""".lstrip(),
        encoding="utf-8",
    )

    controller = tmp_path / "gated-output-limit-regression.ps1"
    controller.write_text(
        _production_controller_prefix()
        + f"""
$Watch = [System.Diagnostics.Stopwatch]::StartNew()
$Invocation = Invoke-BoundedProcess `
    -Executable {_ps_single_quoted(str(VENV_PYTHON))} `
    -ProcessArguments @(
        '-I',
        {_ps_single_quoted(str(fixture))},
        {_ps_single_quoted(str(child_pid_path))},
        {_ps_single_quoted(nonce)}
    ) `
    -TimeoutMilliseconds 10000 `
    -MaxCapturedCharacters 1024
$Watch.Stop()

$ChildPid = [int](Get-Content -LiteralPath {_ps_single_quoted(str(child_pid_path))} -Raw)
$ChildAliveWhenFunctionReturned = $false
try {{
    $Residual = [System.Diagnostics.Process]::GetProcessById($ChildPid)
    try {{
        $ChildAliveWhenFunctionReturned = -not $Residual.HasExited
    }}
    finally {{
        $Residual.Dispose()
    }}
}}
catch [System.ArgumentException] {{
    $ChildAliveWhenFunctionReturned = $false
}}

[ordered]@{{
    started = $Invocation.Started
    timed_out = $Invocation.TimedOut
    output_limit_exceeded = $Invocation.OutputLimitExceeded
    exit_code = $Invocation.ExitCode
    stdout = $Invocation.Stdout
    stderr = $Invocation.Stderr
    elapsed_milliseconds = $Watch.ElapsedMilliseconds
    child_alive_when_function_returned = $ChildAliveWhenFunctionReturned
}} | ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["started"] is True
    assert result["timed_out"] is False
    assert result["output_limit_exceeded"] is True
    assert result["exit_code"] == 2
    assert result["stdout"] == ""
    assert result["stderr"] == ""
    assert result["elapsed_milliseconds"] < 8000
    assert result["child_alive_when_function_returned"] is False


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects require Windows")
@pytest.mark.parametrize(
    "powershell_executable",
    _windows_powershells(),
    ids=lambda executable: f"missing-target-{Path(executable).stem}",
)
def test_missing_target_preserves_started_false_contract(
    tmp_path: Path,
    powershell_executable: str,
) -> None:
    missing_executable = tmp_path / "missing-target.exe"
    controller = tmp_path / "gated-missing-target-regression.ps1"
    controller.write_text(
        _production_controller_prefix()
        + f"""
$Invocation = Invoke-BoundedProcess `
    -Executable {_ps_single_quoted(str(missing_executable))} `
    -TimeoutMilliseconds 5000
$Invocation | ConvertTo-Json -Compress
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            powershell_executable,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(controller),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result == {
        "Started": False,
        "TimedOut": False,
        "OutputLimitExceeded": False,
        "ExitCode": 2,
        "Stdout": "",
        "Stderr": "",
    }
