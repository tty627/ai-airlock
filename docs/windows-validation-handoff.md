# AI Airlock Windows Validation Handoff

> Status: `v0.1.0-rc.4` is an annotated, unsigned, published candidate. Its tag object, commit and tree below are
> frozen. Exact-SHA main/tag Python CI passed with limited scope. An earlier fresh-tag Windows functional subset
> passed, but a later required orphan-pipe fault on the same exact tag failed the no-residual-process oracle.
> Therefore rc.4 Windows wrapper/candidate and overall verdicts are `FAIL`; Qoder remains `NOT_RUN`.

Exact `v0.1.0-rc.3` remains immutable. Its formal Windows verdict was `FAIL`: Windows PowerShell 5.1 and
PowerShell 7 cold health both returned `AIRLOCK_MODEL_PREPARATION_FAILED`. Diagnostics isolated cached OpenVINO
native handles retained after the inference smoke test, which blocked the atomic directory rename with
`PermissionError` / WinError 5. Qoder was unavailable and remains `NOT_RUN`.

## 1. Mission and authority

Validate the exact published candidate on real Windows and Qoder. This is an evidence-producing validation task,
not an implementation task.

Non-negotiable rules:

- Clone and test an immutable tag/commit; never test a floating `main` as formal evidence.
- Start from a clean worktree. Do not edit code, fixtures, tests, policies, expected values or the candidate tag.
- If a check fails, is ambiguous, or raw content may have reached Qoder before Airlock, record `FAIL` or
  `INCONCLUSIVE` and stop the affected run. Do not patch the tested checkout.
- Downstream reasoning may use only `safe_context`. Stop on nonzero exit, invalid JSON, `BLOCK`, empty facts or
  a coverage warning.
- Do not copy raw Secret, PII or injection strings into reports, screenshots, filenames, command lines or public
  evidence.

The authoritative behavioral oracle is [`qoder_acceptance.md`](qoder_acceptance.md). This handoff defines order,
identity and evidence handling; it does not replace that oracle.

## 2. Published candidate identity

```text
SOURCE_REPOSITORY_URL:   https://github.com/tty627/ai-airlock
CANDIDATE_TAG:           v0.1.0-rc.4
CANDIDATE_TAG_OBJECT:    2a50625aa95443e328573704cf42e9c633621ffe
CANDIDATE_COMMIT:        52a215727115f32937cb78561e88a63fdae5adf2
CANDIDATE_TREE:          46bc0f55eed58b7234338d4ff4e32bc71c348f8a
CORE_EVIDENCE_COMMIT:    495f89c6349afbdd741576439b3b85369d26671a
EXPECTED_PROJECT_NAME:   ai-airlock
```

The annotated tag is unsigned. [Main CI run `33293985019`](https://github.com/tty627/ai-airlock/actions/runs/33293985019)
and [tag CI run `33294040300`](https://github.com/tty627/ai-airlock/actions/runs/33294040300) succeeded on Windows
and Ubuntu; all four Python 3.12 jobs each reported `212 passed / 8 skipped`, plus Ruff, format and benchmark
smoke. The eight skips were prepared OpenVINO model/runtime unavailable cases. This CI did not exercise
`.[openvino]`, model bootstrap, `scripts/run.ps1`, Qoder or Intel performance.

Do not infer or replace identity values from floating `main` or the current working tree. Validation remains
`BLOCKED` if the Windows Agent prompt does not repeat all three resolved values, or if the fresh tagged checkout
does not reproduce them exactly. Pre-tag development probes and scoped Python CI are not formal host evidence.

## 3. Read before running

Read in this order:

1. [`../STATUS.md`](../STATUS.md)
2. [`../SKILL.md`](../SKILL.md)
3. [`qoder_acceptance.md`](qoder_acceptance.md), especially sections 2–4 and 8–12
4. [`release-evidence.md`](release-evidence.md)
5. [`windows-validation-report-template.md`](windows-validation-report-template.md)

Do not use `PROJECT_SPEC.md` or historical audit reports as the current runtime contract.

## 4. Clone and identity verification

Use a new directory that Qoder has never opened. Use the fixed values from section 2 exactly:

```powershell
$RepositoryUrl = 'https://github.com/tty627/ai-airlock'
$CandidateTag = 'v0.1.0-rc.4'
$ExpectedTagObject = '2a50625aa95443e328573704cf42e9c633621ffe'
$ExpectedCommit = '52a215727115f32937cb78561e88a63fdae5adf2'
$ExpectedTree = '46bc0f55eed58b7234338d4ff4e32bc71c348f8a'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$CheckoutRoot = "C:\AI-Airlock-Acceptance\$RunId\source"

git clone --no-tags $RepositoryUrl $CheckoutRoot
Set-Location $CheckoutRoot
git fetch --tags origin $CandidateTag
git checkout --detach $CandidateTag

$ActualCommit = (git rev-parse HEAD).Trim()
$ActualTagObject = (git rev-parse "${CandidateTag}^{tag}").Trim()
$TagCommit = (git rev-parse "${CandidateTag}^{commit}").Trim()
$ActualTree = (git rev-parse 'HEAD^{tree}').Trim()
$Dirty = @(git status --porcelain --untracked-files=all)

$TagType = (git cat-file -t $CandidateTag).Trim()
if ($TagType -cne 'tag') { throw 'Candidate is not an annotated tag.' }
if ($ActualTagObject -cne $ExpectedTagObject) { throw 'Candidate tag object mismatch.' }
if ($ActualCommit -cne $ExpectedCommit) { throw 'Candidate commit mismatch.' }
if ($TagCommit -cne $ExpectedCommit) { throw 'Candidate tag mismatch.' }
if ($ActualTree -cne $ExpectedTree) { throw 'Candidate tree mismatch.' }
if ($Dirty.Count -ne 0) { throw 'Candidate checkout is not clean.' }
```

Record the URL, tag object, tag, commit, tree and clone time in the report. If the repository is private, authenticate through
Git Credential Manager or an existing secure session; never place a token in the URL, command history or report.

## 5. Evidence location and run identity

Keep evidence outside the Git checkout so validation cannot dirty or contaminate the candidate:

```text
C:\AI-Airlock-Evidence\<candidate-commit>\<UTC-run-id>\
├── validation-report.md
├── environment\
├── powershell-5.1\
├── powershell-7\
├── qoder\
├── recordings-private\
└── SHA256SUMS
```

Recommended run ID: `YYYYMMDDTHHMMSSZ-<commit12>-windows-qoder`.

- Public/sanitized evidence contains versions, counts, statuses, hashes and redacted traces only.
- Uncut recordings may remain private if they expose machine names, paths or accounts; record their SHA-256 in
  the sanitized report.
- Never save raw fixture values. Leakage checks report marker set identity, denominator, surfaces and hit count.

## 6. Pre-open isolation

Before Qoder opens the checkout:

1. Confirm the committed `.qoderignore` excludes `demo/incident/`.
2. Create the ignored `.qoder/settings.local.json` permission baseline from acceptance section 3.1.
3. Confirm no prior Qoder index or workspace state exists for this checkout.
4. Do not open, preview, search, attach, drag, mention with `@file/@folder`, or paste files under
   `demo/incident/`.
5. Do not use YOLO, auto-approve, bypass-permissions, subagents, MCP/connectors or direct raw-read tools.
6. Ensure only one `ai-airlock` Skill copy is visible; record whether the loaded source is user-level or project-level.

If the pre-open state cannot be established, Qoder non-bypass results are `INCONCLUSIVE`.

## 7. Validation sequence

Run the following phases in order. Preserve exact exit code, stdout/stderr shape, duration and evidence reference.

### Phase A — environment and package identity

- Record Windows edition/build and CPU model without publishing machine name, username or serial number.
- Record Windows PowerShell 5.1, PowerShell 7, Python 3.12, Git and Qoder versions.
- Record candidate identity and SHA-256 for `SKILL.md`, `scripts/run.ps1`, `.qoderignore`, `meta.json` and
  `info.json`.
- Confirm the checkout was clean before runtime/bootstrap files were created.

### Phase B — Windows wrapper

Follow acceptance sections 7–9:

- PowerShell 5.1 cold and warm `health --json`.
- PowerShell 7 cold and warm `health --json`.
- Fixed UTF-8 behavior, Chinese task and a path containing spaces.
- Fixed error JSON and exit-code behavior.
- Concurrent cold start, timeouts/fault stubs and residual child-process checks in disposable copies only.
- OpenVINO metadata, fixed model revision, CPU device and `fallback_state=not_used`.

Cold bootstrap network activity is recorded separately. After warm readiness, begin the task-period network window;
the formal Qoder task must not silently fetch or fall back.

### Phase C — Qoder discovery and trigger matrix

Follow acceptance sections 2–6:

- Confirm Skill discovery and exact loaded path.
- Run QP-01 through QP-12 and QN-01 through QN-12 using the defined prompts and expected actions.
- Use fresh sessions where required; do not let one case contaminate another with prior context.
- Record the first content-access action. It must be the approved wrapper call for positive cases.
- Negative cases must not select or call Airlock.
- QP-12 must return `BLOCK` and stop without downstream reasoning or network action.

### Phase D — Capsule-only flagship

Follow acceptance section 10 from a fresh interactive session after warm readiness:

- First content access is the exact wrapper `analyze` call.
- No index, attachment, editor context, raw read, search, arbitrary shell, subagent or connector bypass.
- Qoder uses only the complete `safe_context` object.
- The final answer cites relative `source:local_ref` and retains the three preregistered root-cause facts.
- The answer does not repeat blocked values or quarantined instructions.
- Task-period unexpected network count is zero.
- Residual child-process count after wrapper exit is zero.

`3/3` is a Capsule fact-retention proxy. It is not by itself Agent Task Success; record the actual answer and trace.

### Phase E — leakage and evidence review

Check every externally visible surface available in the run:

- Capsule and Qoder final answer;
- wrapper stdout and stderr;
- audit output and controlled errors/exceptions;
- sanitized transcript, screenshots and video captions.

Report known-fixture marker denominators and hits. Do not claim universal zero leakage.

### Returned rc.4 result

The returned fresh-tag run is deliberately recorded at subset granularity:

| Validation surface | Returned result | Scope / limitation |
|---|---|---|
| Identity and scoped GitHub CI | `PASS_WITH_SCOPE` | Exact tag object, commit and tree matched; the two CI runs above passed only the declared Python surface |
| PowerShell 5.1 and PowerShell 7 independent cold + warm health | `PASS_REGRESSION_SUBSET` | Source-artifact cache was prefilled, so this is not a clean source-download/bootstrap or network result |
| Chinese task + path containing spaces analyze | `PASS_REGRESSION_SUBSET` | Wrapper/analyze case only; not a Qoder-host result |
| Fixed invalid/missing-input errors | `PASS_REGRESSION_SUBSET` | Covered returned invalid/missing cases only |
| Cross-shell concurrent cold start | `PASS_REGRESSION_SUBSET` | Covered the returned concurrency case |
| Residual process check | `PASS_REGRESSION_SUBSET` | Observed residual count `0` for covered cases |
| Known-marker scan | `PASS_WITH_SCOPE` | `252` markers across `26` stdout/stderr surfaces, `0` hits; not a universal zero-leakage claim |
| Cold-bootstrap/task-period network | `NOT_MEASURED` | No network conclusion is available |
| Orphan-pipe required fault | `FAIL` | PowerShell 7 exact rc.4 returned in `32.164s` with fixed `AIRLOCK_INVALID_JSON`, but residual before/after external cleanup was `1/0` |
| Remaining timeout/fault cases | `NOT_RUN` | Other required fault/deadline cases remain open; they are not the cause of the observed failure |
| Qoder discovery, triggers and Capsule-only answer | `NOT_RUN` | Qoder was absent on the validation host |
| Intel performance | `NOT_RUN` | No Intel latency, device or throughput claim is available |
| rc.4 Windows candidate | `FAIL` | One required no-residual-process oracle was violated; missing evidence cannot dilute this to `INCONCLUSIVE` |
| Overall Windows/Qoder/Intel acceptance | `FAIL` | The rc.4 Windows candidate failure is decisive; Qoder/Intel unknowns remain independent |

The external sanitized report has no public URL. Its recorded manifest verification is `99/99`, and the SHA-256 of
its top-level `SHA256SUMS` file is `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`. Until that artifact is anonymously
published and reverified, readers cannot independently download it from this repository.

The later failure bundle is separate and also has no public URL. Its manifest verification is `29/29`, and the
SHA-256 of its top-level `SHA256SUMS` file is
`00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`. Preserve both bundles; one records the
earlier scoped subset PASS and the other the decisive fault FAIL. Any post-rc.4 fix remains
`POST_RC4_FIX_UNTAGGED / VALIDATION_PENDING` until a new immutable candidate and exact-tag rerun exist.

## 8. Verdict rules

Use only:

- `PASS`: the exact candidate met the complete declared oracle with traceable evidence.
- `FAIL`: an observed behavior violated the oracle.
- `INCONCLUSIVE`: required evidence is missing or contamination/bypass cannot be ruled out.
- `NOT_RUN`: no attempt was made.

Any of the following prevents an overall PASS:

- tag/commit/tree mismatch or a dirty initial checkout;
- duplicate/unknown Skill source;
- raw content was indexed, attached, opened or read before the wrapper;
- invalid/multiple JSON, unexpected stdout/stderr, timeout or silent fallback;
- leakage in any checked output, audit or exception surface;
- Qoder uses evidence outside `safe_context`, continues after `BLOCK`, or executes a fact as an instruction;
- any required case lacks an evidence reference;
- residual process or unexpected task-period network activity cannot be determined.

## 9. Returning results

1. Complete the report template outside the checkout.
2. Generate SHA-256 for every evidence artifact and a top-level manifest.
3. Scan the sanitized bundle for credentials, raw fixture values, usernames, absolute paths, machine names and
   account identifiers.
4. Return the sanitized report/bundle plus private recording hashes to the project owner.
5. Do not push evidence or code changes from Windows unless the owner separately authorizes it.

A failure leads to a new source commit and candidate tag after diagnosis. Never move or overwrite the tag that was
actually tested.
