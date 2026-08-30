function Test-AirlockWindowsPlatform {
    return [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
}

function Initialize-AirlockWindowsJobType {
    if (-not (Test-AirlockWindowsPlatform)) {
        return
    }
    if ($null -ne ('Airlock.Windows.KillOnCloseJob' -as [type])) {
        return
    }

    $TypeDefinition = @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

namespace Airlock.Windows
{
    internal static class JobNativeMethods
    {
        internal const UInt32 JobObjectLimitKillOnJobClose = 0x00002000;
        internal const Int32 JobObjectBasicAccountingInformationClass = 1;
        internal const Int32 JobObjectExtendedLimitInformationClass = 9;

        [StructLayout(LayoutKind.Sequential)]
        internal struct IoCounters
        {
            internal UInt64 ReadOperationCount;
            internal UInt64 WriteOperationCount;
            internal UInt64 OtherOperationCount;
            internal UInt64 ReadTransferCount;
            internal UInt64 WriteTransferCount;
            internal UInt64 OtherTransferCount;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct JobObjectBasicLimitInformation
        {
            internal Int64 PerProcessUserTimeLimit;
            internal Int64 PerJobUserTimeLimit;
            internal UInt32 LimitFlags;
            internal UIntPtr MinimumWorkingSetSize;
            internal UIntPtr MaximumWorkingSetSize;
            internal UInt32 ActiveProcessLimit;
            internal UIntPtr Affinity;
            internal UInt32 PriorityClass;
            internal UInt32 SchedulingClass;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct JobObjectExtendedLimitInformation
        {
            internal JobObjectBasicLimitInformation BasicLimitInformation;
            internal IoCounters IoInfo;
            internal UIntPtr ProcessMemoryLimit;
            internal UIntPtr JobMemoryLimit;
            internal UIntPtr PeakProcessMemoryUsed;
            internal UIntPtr PeakJobMemoryUsed;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct JobObjectBasicAccountingInformation
        {
            internal Int64 TotalUserTime;
            internal Int64 TotalKernelTime;
            internal Int64 ThisPeriodTotalUserTime;
            internal Int64 ThisPeriodTotalKernelTime;
            internal UInt32 TotalPageFaultCount;
            internal UInt32 TotalProcesses;
            internal UInt32 ActiveProcesses;
            internal UInt32 TotalTerminatedProcesses;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        internal static extern IntPtr CreateJobObject(IntPtr jobAttributes, String name);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean SetInformationJobObject(
            IntPtr job,
            Int32 informationClass,
            ref JobObjectExtendedLimitInformation information,
            UInt32 informationLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean AssignProcessToJobObject(
            IntPtr job,
            IntPtr process);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean TerminateJobObject(
            IntPtr job,
            UInt32 exitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean QueryInformationJobObject(
            IntPtr job,
            Int32 informationClass,
            ref JobObjectBasicAccountingInformation information,
            UInt32 informationLength,
            IntPtr returnLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean CloseHandle(IntPtr handle);

        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        internal static extern Boolean GetNamedPipeClientProcessId(
            IntPtr pipe,
            out UInt32 clientProcessId);
    }

    public sealed class KillOnCloseJob : IDisposable
    {
        private readonly Object syncRoot = new Object();
        private IntPtr handle;

        public KillOnCloseJob()
        {
            IntPtr created = JobNativeMethods.CreateJobObject(IntPtr.Zero, null);
            if (created == IntPtr.Zero)
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            JobNativeMethods.JobObjectExtendedLimitInformation information =
                new JobNativeMethods.JobObjectExtendedLimitInformation();
            information.BasicLimitInformation.LimitFlags =
                JobNativeMethods.JobObjectLimitKillOnJobClose;
            UInt32 informationLength = checked((UInt32)Marshal.SizeOf(
                typeof(JobNativeMethods.JobObjectExtendedLimitInformation)));
            if (!JobNativeMethods.SetInformationJobObject(
                created,
                JobNativeMethods.JobObjectExtendedLimitInformationClass,
                ref information,
                informationLength))
            {
                Int32 error = Marshal.GetLastWin32Error();
                JobNativeMethods.CloseHandle(created);
                throw new Win32Exception(error);
            }
            handle = created;
        }

        public void AssignProcess(IntPtr processHandle)
        {
            lock (syncRoot)
            {
                if (handle == IntPtr.Zero)
                {
                    throw new ObjectDisposedException("KillOnCloseJob");
                }
                if (processHandle == IntPtr.Zero)
                {
                    throw new ArgumentException("A valid process handle is required.");
                }
                if (!JobNativeMethods.AssignProcessToJobObject(handle, processHandle))
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
            }
        }

        public void TerminateAndWait(Int32 timeoutMilliseconds)
        {
            if (timeoutMilliseconds <= 0)
            {
                throw new ArgumentOutOfRangeException("timeoutMilliseconds");
            }

            lock (syncRoot)
            {
                if (handle == IntPtr.Zero)
                {
                    throw new ObjectDisposedException("KillOnCloseJob");
                }
                if (!JobNativeMethods.TerminateJobObject(handle, 2))
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }

                Stopwatch watch = Stopwatch.StartNew();
                while (true)
                {
                    JobNativeMethods.JobObjectBasicAccountingInformation information =
                        new JobNativeMethods.JobObjectBasicAccountingInformation();
                    UInt32 informationLength = checked((UInt32)Marshal.SizeOf(
                        typeof(JobNativeMethods.JobObjectBasicAccountingInformation)));
                    if (!JobNativeMethods.QueryInformationJobObject(
                        handle,
                        JobNativeMethods.JobObjectBasicAccountingInformationClass,
                        ref information,
                        informationLength,
                        IntPtr.Zero))
                    {
                        throw new Win32Exception(Marshal.GetLastWin32Error());
                    }
                    if (information.ActiveProcesses == 0)
                    {
                        return;
                    }
                    if (watch.ElapsedMilliseconds >= timeoutMilliseconds)
                    {
                        throw new TimeoutException(
                            "The bounded process job did not become empty in time.");
                    }
                    Thread.Sleep(10);
                }
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        private void Dispose(Boolean disposing)
        {
            lock (syncRoot)
            {
                if (handle == IntPtr.Zero)
                {
                    return;
                }
                IntPtr closing = handle;
                handle = IntPtr.Zero;
                if (!JobNativeMethods.CloseHandle(closing) && disposing)
                {
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                }
            }
        }

        ~KillOnCloseJob()
        {
            try
            {
                Dispose(false);
            }
            catch
            {
            }
        }
    }

    public static class NamedPipeIdentity
    {
        public static UInt32 GetClientProcessId(IntPtr pipeHandle)
        {
            UInt32 clientProcessId;
            if (pipeHandle == IntPtr.Zero)
            {
                throw new ArgumentException("A valid pipe handle is required.");
            }
            if (!JobNativeMethods.GetNamedPipeClientProcessId(
                pipeHandle,
                out clientProcessId))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            return clientProcessId;
        }
    }
}
'@

    try {
        Add-Type -TypeDefinition $TypeDefinition -Language CSharp -ErrorAction Stop | Out-Null
    }
    catch {
        throw [System.InvalidOperationException]::new(
            'The bounded process isolation helper could not be initialized.'
        )
    }
}

function New-AirlockKillOnCloseJob {
    if (-not (Test-AirlockWindowsPlatform)) {
        return $null
    }

    try {
        Initialize-AirlockWindowsJobType
        return New-Object -TypeName 'Airlock.Windows.KillOnCloseJob'
    }
    catch {
        throw [System.InvalidOperationException]::new(
            'The bounded process isolation job could not be created.'
        )
    }
}

function Register-AirlockProcessWithKillOnCloseJob {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][object]$Job,
        [Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process
    )

    if ($null -eq $Job) {
        return
    }
    try {
        $Job.AssignProcess($Process.Handle)
    }
    catch {
        throw [System.InvalidOperationException]::new(
            'The bounded child process could not be isolated.'
        )
    }
}

function Close-AirlockKillOnCloseJob {
    param([Parameter(Mandatory = $true)][AllowNull()][object]$Job)

    if ($null -eq $Job) {
        return
    }
    try {
        $Job.Dispose()
    }
    catch {
        # Cleanup must never expose a native error through the wrapper boundary.
    }
}

function Complete-AirlockKillOnCloseJob {
    param(
        [Parameter(Mandatory = $true)][AllowNull()][object]$Job,
        [int]$TimeoutMilliseconds = 5000
    )

    if ($null -eq $Job) {
        return
    }
    $CleanupFailure = $null
    try {
        $Job.TerminateAndWait($TimeoutMilliseconds)
    }
    catch {
        $CleanupFailure = $_.Exception
    }
    try {
        $Job.Dispose()
    }
    catch {
        if ($null -eq $CleanupFailure) {
            $CleanupFailure = $_.Exception
        }
    }
    if ($null -ne $CleanupFailure) {
        throw [System.InvalidOperationException]::new(
            'The bounded process isolation job could not be emptied.',
            $CleanupFailure
        )
    }
}

function Start-AirlockGatedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$ArgumentText,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$LauncherPath,
        [bool]$RedirectStandardInput = $false,
        [int]$HandshakeTimeoutMilliseconds = 10000
    )

    if (-not (Test-AirlockWindowsPlatform) -or `
        $HandshakeTimeoutMilliseconds -le 0 -or `
        -not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) {
        throw [System.InvalidOperationException]::new(
            'The gated process launcher is unavailable.'
        )
    }

    $Job = $null
    $ControlPipe = $null
    $ConnectResult = $null
    $ConnectWaitHandle = $null
    $Process = $null
    $ProcessStarted = $false
    $ProcessAssigned = $false
    $HandshakeWatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $Job = New-AirlockKillOnCloseJob
        $PipeName = 'ai-airlock-' + [System.Guid]::NewGuid().ToString('N')
        $ControlPipe = [System.IO.Pipes.NamedPipeServerStream]::new(
            $PipeName,
            [System.IO.Pipes.PipeDirection]::InOut,
            1,
            [System.IO.Pipes.PipeTransmissionMode]::Byte,
            [System.IO.Pipes.PipeOptions]::Asynchronous
        )
        $ConnectResult = $ControlPipe.BeginWaitForConnection($null, $null)

        $PowerShellExecutable = (Get-Process -Id $PID).Path
        if ([string]::IsNullOrWhiteSpace([string]$PowerShellExecutable)) {
            throw 'The current PowerShell executable could not be resolved.'
        }
        $LauncherArguments = @(
            '-NoLogo',
            '-NoProfile',
            '-NonInteractive',
            '-File',
            $LauncherPath,
            '-ControlPipeName',
            $PipeName
        )
        $LauncherArgumentText = (($LauncherArguments | ForEach-Object {
            ConvertTo-NativeArgument -Value ([string]$_)
        }) -join ' ')

        $StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $StartInfo.FileName = $PowerShellExecutable
        $StartInfo.Arguments = $LauncherArgumentText
        $StartInfo.WorkingDirectory = $WorkingDirectory
        $StartInfo.UseShellExecute = $false
        $StartInfo.CreateNoWindow = $true
        $StartInfo.RedirectStandardOutput = $true
        $StartInfo.RedirectStandardError = $true
        $StartInfo.RedirectStandardInput = $RedirectStandardInput
        $StartInfo.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
        $StartInfo.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)

        $Process = [System.Diagnostics.Process]::new()
        $Process.StartInfo = $StartInfo
        if (-not $Process.Start()) {
            throw 'The gated launcher process did not start.'
        }
        $ProcessStarted = $true
        Register-AirlockProcessWithKillOnCloseJob -Job $Job -Process $Process
        $ProcessAssigned = $true

        $ConnectWaitHandle = $ConnectResult.AsyncWaitHandle
        $RemainingMilliseconds = $HandshakeTimeoutMilliseconds - `
            [int]$HandshakeWatch.ElapsedMilliseconds
        if ($RemainingMilliseconds -le 0 -or `
            -not $ConnectWaitHandle.WaitOne($RemainingMilliseconds)) {
            throw 'The gated launcher did not connect in time.'
        }
        $ControlPipe.EndWaitForConnection($ConnectResult)
        $ConnectWaitHandle.Close()
        $ConnectWaitHandle = $null
        $ConnectResult = $null
        $PipeClientProcessId = [Airlock.Windows.NamedPipeIdentity]::GetClientProcessId(
            $ControlPipe.SafePipeHandle.DangerousGetHandle()
        )
        if ($PipeClientProcessId -ne $Process.Id) {
            throw 'The gated launcher control pipe client identity did not match.'
        }

        $Descriptor = [ordered]@{
            schema_version = '1'
            executable = $Executable
            argument_text = $ArgumentText
            working_directory = $WorkingDirectory
        }
        $PayloadText = $Descriptor | ConvertTo-Json -Compress -Depth 2
        $PayloadBytes = [System.Text.UTF8Encoding]::new($false, $true).GetBytes($PayloadText)
        if ($PayloadBytes.Length -le 0 -or $PayloadBytes.Length -gt 131072) {
            throw 'The gated launcher descriptor is too large.'
        }
        $LengthBytes = [System.BitConverter]::GetBytes([int]$PayloadBytes.Length)
        $Frame = [byte[]]::new(4 + $PayloadBytes.Length)
        [System.Buffer]::BlockCopy($LengthBytes, 0, $Frame, 0, 4)
        [System.Buffer]::BlockCopy($PayloadBytes, 0, $Frame, 4, $PayloadBytes.Length)
        $WriteTask = $ControlPipe.WriteAsync($Frame, 0, $Frame.Length)
        $RemainingMilliseconds = $HandshakeTimeoutMilliseconds - `
            [int]$HandshakeWatch.ElapsedMilliseconds
        if ($RemainingMilliseconds -le 0 -or `
            -not $WriteTask.Wait($RemainingMilliseconds)) {
            throw 'The gated launcher descriptor write timed out.'
        }
        $WriteTask.GetAwaiter().GetResult()
        $ControlPipe.Flush()

        $StatusBuffer = [byte[]]::new(1)
        $ReadTask = $ControlPipe.ReadAsync($StatusBuffer, 0, 1)
        $RemainingMilliseconds = $HandshakeTimeoutMilliseconds - `
            [int]$HandshakeWatch.ElapsedMilliseconds
        if ($RemainingMilliseconds -le 0 -or `
            -not $ReadTask.Wait($RemainingMilliseconds)) {
            throw 'The gated launcher start acknowledgement timed out.'
        }
        $StatusLength = $ReadTask.GetAwaiter().GetResult()
        if ($StatusLength -ne 1) {
            throw 'The gated launcher ended before acknowledging target start.'
        }
        $LauncherStatus = [int]$StatusBuffer[0]

        if ($LauncherStatus -eq 2) {
            $ControlPipe.Dispose()
            $ControlPipe = $null
            Complete-AirlockKillOnCloseJob -Job $Job
            $Job = $null
            $Process.Dispose()
            $Process = $null
            return [pscustomobject]@{
                TargetStarted = $false
                Process = $null
                Job = $null
            }
        }
        if ($LauncherStatus -ne 1) {
            throw 'The gated launcher returned an invalid start acknowledgement.'
        }

        $Session = [pscustomobject]@{
            TargetStarted = $true
            Process = $Process
            Job = $Job
            ControlPipe = $ControlPipe
        }
        $Process = $null
        $Job = $null
        $ControlPipe = $null
        return $Session
    }
    catch {
        if ($null -ne $ControlPipe) {
            try {
                $ControlPipe.Dispose()
            }
            catch {
            }
            $ControlPipe = $null
        }
        if ($ProcessAssigned -and $null -ne $Job) {
            try {
                Complete-AirlockKillOnCloseJob -Job $Job
                $Job = $null
            }
            catch {
            }
        }
        elseif ($ProcessStarted -and $null -ne $Process) {
            try {
                if (-not $Process.WaitForExit(250)) {
                    $Process.Kill()
                }
                if (-not $Process.WaitForExit(10000) -or -not $Process.HasExited) {
                    throw 'The unassigned gated launcher did not stop in time.'
                }
            }
            catch {
            }
        }
        throw [System.InvalidOperationException]::new(
            'The gated process could not be isolated and started.',
            $_.Exception
        )
    }
    finally {
        if ($null -ne $ControlPipe) {
            $ControlPipe.Dispose()
        }
        if ($null -ne $ConnectWaitHandle) {
            $ConnectWaitHandle.Close()
        }
        if ($null -ne $Process) {
            $Process.Dispose()
        }
        Close-AirlockKillOnCloseJob -Job $Job
    }
}
