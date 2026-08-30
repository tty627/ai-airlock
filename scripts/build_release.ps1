[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Ref,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$OutputRoot = [IO.Path]::GetFullPath($OutputDirectory)
$Allowlist = @(
    '.qoderignore',
    'STATUS.md',
    'README.md',
    'SKILL.md',
    'LICENSE',
    'THIRD_PARTY_NOTICES.md',
    'meta.json',
    'info.json',
    'pyproject.toml',
    'requirements.txt',
    'src',
    'scripts',
    'config',
    'demo',
    'tests',
    'benchmark/README.md',
    'benchmark/run_benchmark.py',
    'benchmark/variants.json',
    'benchmark/datasets',
    'assets/competition',
    'docs/architecture.md',
    'docs/claims-ledger.md',
    'docs/competition-story.md',
    'docs/demo-script.md',
    'docs/license-decision.md',
    'docs/modelscope-article.md',
    'docs/modelscope-article-submission.md',
    'docs/modelscope-submission-fields.md',
    'docs/publication-runbook.md',
    'docs/qoder_acceptance.md',
    'docs/release-evidence.md',
    'docs/release-metadata.md',
    'docs/submission-checklist.md',
    'docs/threat-model.md',
    'docs/trae-acceptance.md',
    'docs/windows-validation-handoff.md',
    'docs/windows-validation-report-template.md',
    'docs/windows-intel-rc6-evidence.md'
)

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)

    $output = & git -C $RepoRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
    return $output
}

$Dirty = @(Invoke-Git status --porcelain=v1 --untracked-files=all)
if ($Dirty.Count -ne 0) {
    throw 'The source worktree must be clean before packaging.'
}

$CommitExpression = $Ref + '^{commit}'
$Commit = (Invoke-Git rev-parse $CommitExpression).Trim()
if ($Commit -notmatch '^[0-9a-f]{40}$') {
    throw "Ref did not resolve to a full commit: $Ref"
}

[IO.Directory]::CreateDirectory($OutputRoot) | Out-Null
$ShortCommit = $Commit.Substring(0, 12)
$Archive = Join-Path $OutputRoot "ai-airlock-skill-$ShortCommit.zip"
$MembersFile = Join-Path $OutputRoot "ai-airlock-skill-$ShortCommit.members.txt"
$ChecksumFile = "$Archive.sha256"

foreach ($Target in @($Archive, $MembersFile, $ChecksumFile)) {
    if ([IO.File]::Exists($Target)) {
        throw "Refusing to overwrite existing release artifact: $Target"
    }
}

& git -C $RepoRoot archive --format=zip --output=$Archive $Commit -- @Allowlist
if ($LASTEXITCODE -ne 0) {
    throw "git archive failed with exit code $LASTEXITCODE"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Zip = [IO.Compression.ZipFile]::OpenRead($Archive)
try {
    $Members = @($Zip.Entries | ForEach-Object FullName | Sort-Object)
} finally {
    $Zip.Dispose()
}

if (@($Members | Where-Object { $_ -eq 'SKILL.md' }).Count -ne 1) {
    throw 'Archive root must contain exactly one SKILL.md.'
}
if (@($Members | Where-Object { $_ -match '(^|/)SKILL\.md$' }).Count -ne 1) {
    throw 'Archive must contain exactly one SKILL.md in total.'
}

$Denied = @($Members | Where-Object {
    $_ -match '(^|/)(\.venv[^/]*|models|__pycache__|\.pytest_cache|\.ruff_cache|[^/]+\.egg-info|benchmark/results|\.release-evidence|cache)(/|$)'
})
if ($Denied.Count -ne 0) {
    throw "Archive contains denied paths: $($Denied -join ', ')"
}

$UnexpectedLogs = @($Members | Where-Object {
    $_ -match '\.log$' -and
    $_ -notin @('demo/incident/payment-service.log', 'demo/incident/production.log')
})
if ($UnexpectedLogs.Count -ne 0) {
    throw "Archive contains unexpected logs: $($UnexpectedLogs -join ', ')"
}

$ArchiveInfo = [IO.FileInfo]::new($Archive)
if ($ArchiveInfo.Length -gt 5MB) {
    throw "Archive exceeds the 5 MiB publication gate: $($ArchiveInfo.Length) bytes"
}

$Sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Archive).Hash.ToLowerInvariant()
[IO.File]::WriteAllLines($MembersFile, $Members, [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText(
    $ChecksumFile,
    "$Sha256  $($ArchiveInfo.Name)$([Environment]::NewLine)",
    [Text.UTF8Encoding]::new($false)
)

[pscustomobject]@{
    ref = $Ref
    commit = $Commit
    archive = $Archive
    sha256 = $Sha256
    size_bytes = $ArchiveInfo.Length
    entries = $Members.Count
    members_file = $MembersFile
    checksum_file = $ChecksumFile
} | ConvertTo-Json -Compress
