# AI Airlock Project Status

> Last reviewed: 2026-08-30 (Asia/Shanghai)
>
> This file is the current project-state entry point. It records what is verified, pending, or blocked.
> Numerical release claims remain authoritative only in
> [`docs/claims-ledger.md`](docs/claims-ledger.md).

## Current identities

```text
Core tag:       v0.1.0-rc.1
Core commit:    495f89c6349afbdd741576439b3b85369d26671a
Core tree:      4fe991ded88f38a6c1952c506d20005d2956a915
Core evidence:  .release-evidence/495f89c6349afbdd741576439b3b85369d26671a/

Previous Windows candidates: v0.1.0-rc.3 and v0.1.0-rc.4 (immutable; formal Windows verdicts FAIL)
Windows candidate tag:      v0.1.0-rc.5 (annotated, unsigned, published; immutable by release policy)
Windows candidate tag object: 7d4034f9e8575658190dacef53f9ba749de8ed6c
Windows candidate commit:   9abf825943f8f68f2bc6cd3afc1baa8717e0c01a
Windows candidate tree:     88b914598de60fa385820860b13dc8bd6db26b7d
GitHub remote:               https://github.com/tty627/ai-airlock (public)
```

`v0.1.0-rc.1` through `v0.1.0-rc.5` remain immutable. Formal Windows validation of exact rc.3 failed during
cold health on both Windows PowerShell 5.1 and PowerShell 7; exact rc.4 later failed its required orphan-pipe
no-residual-process oracle. `v0.1.0-rc.5` is the current annotated, unsigned, published candidate with the exact
identity above. Never infer candidate identity from floating `main`, and never move an existing tag.

## Status summary

| Area | State | Current evidence | Next gate |
|---|---|---|---|
| Python security core | `VERIFIED` | Frozen rc.1 clean-checkout evidence | Re-run on the future release candidate |
| macOS / Apple M4 / OpenVINO CPU | `VERIFIED` | Fixed model revision, public CLI, strict Python response gate, flagship and synthetic A/B | Do not extrapolate to Windows, Intel or Qoder |
| Numerical public claims | `VERIFIED_WITH_SCOPE` | [Claims Ledger](docs/claims-ledger.md) and frozen JSON | Keep estimator, fixture, device and commit qualifiers |
| Competition docs and visuals | `READY_FOR_CANDIDATE_REVIEW` | README, article draft, seven SVG/PNG pairs, demo script | Validate from a clean candidate checkout and target renderers |
| Windows PowerShell 5.1 / 7 | `FAIL_RC3 / FAIL_RC4 / RC5_SCOPED_PASS / FULL_MATRIX_INCONCLUSIVE` | Exact rc.5 passed orphan-pipe no-residual-process oracles in PowerShell 5.1 and 7 plus scoped health/analyze controls | Run empty-cache, network and remaining external fault cases against exact rc.5; never move an earlier tag |
| Qoder host integration | `NOT_RUN` | rc.5 evidence covers the production wrapper, not Qoder; 12 positive and 12 negative trigger specifications remain unexecuted | Real discovery, tool trace, Capsule-only and non-bypass evidence |
| Intel hardware | `PERFORMANCE_NOT_RUN` | rc.5 scoped Windows evidence establishes bounded wrapper functionality only | Named Intel device, cold/warm latency and successful device/performance oracle, or explicit limitation |
| Overall candidate validation | `INCONCLUSIVE` | Exact rc.5 closed the blocking rc.4 orphan-pipe regression, but the full Windows matrix, Qoder and Intel evidence remain incomplete | Keep each unknown explicit; a scoped pass is not full acceptance |
| Release metadata | `PASS_WITH_PLATFORM_PREFLIGHT` | Public immutable icon, measured `mem_need_gb=1.0`, documented timeout `300`, and template-only `info.json` fields | Confirm `models=[]` on the real upload parser |
| GitHub / Python CI | `RC5_VERIFIED_WITH_SCOPE` | Exact-SHA rc.5 main/tag CI succeeded; Windows reported `225 passed / 8 skipped` and Ubuntu `213 passed / 14 skipped` | Keep prepared-OpenVINO/Windows-Job skips and wrapper/Qoder/Intel non-coverage explicit |
| ModelScope publication | `LOGIN_REQUIRED` | Local fields, article, package builder and authorization are prepared | Authenticate ModelScope, run platform preflight, publish URLs and save receipt |

## Verified rc.1 facts

The following are bounded rc.1 facts, not general product guarantees:

- Full pytest: `212 passed / 6 skipped`; all six skips were due to unavailable PowerShell on the recorded Mac.
- Flagship required-fact retention: rules-only `3/3`, OpenVINO `3/3`.
- Synthetic relevance Mean Recall@K: `0.583333 -> 0.9375` across 12 tasks.
- Synthetic Cross-lingual Mean Recall@K: `0.4375 -> 1.0` across four tasks.
- Flagship estimated-token context reduction: `66.5564% -> 75.3515%`, using
  `utf8_bytes_div_4_ceil_v1`; some other inputs expand.
- CLI P95 latency in the same frozen run: `103.052 ms -> 1204.529 ms`.
- The OpenVINO flagship observed `0 / 252` frozen known-fixture forbidden values in the specified stdout,
  stderr and audit surfaces. This is not a universal zero-leakage claim.

See [Claims Ledger](docs/claims-ledger.md) for definitions, JSON paths, denominators and limitations.

## GitHub publication evidence for rc.2

- Public repository: `https://github.com/tty627/ai-airlock`; anonymous API check reported `public`, default
  branch `main`, and detected license `Apache-2.0`.
- Remote `v0.1.0-rc.2^{}` resolves to commit `aca0c112f3d70752185b50f95191187548537798`; its tree is
  `80b8c2d8bcd336bb338b3864925c9c459ce2b472`.
- Candidate tag CI: [GitHub Actions run 33258339574](https://github.com/tty627/ai-airlock/actions/runs/33258339574),
  `success`.
- Candidate-SHA main CI: [GitHub Actions run 33258339207](https://github.com/tty627/ai-airlock/actions/runs/33258339207),
  `success`.
- An anonymous fresh clone detached at the exact candidate passed `212 passed / 6 skipped` on the recorded Mac;
  all six skips were PowerShell-only. It also passed the benchmark smoke test and imported `airlock` from the
  fresh clone rather than the development checkout.
- The controlled candidate archive contained 130 entries, exactly one `SKILL.md`, was 1,251,636 bytes, passed
  the documented denylist/5 MB checks, and had SHA-256
  `ccf04f0d7ad7e461d61420bd946f1d2be85c3e034e3bc07630ed1d2044105544`. This local QA artifact has not been
  published as a release asset.

These checks prove source publication and Linux/macOS automation only. They do not prove Windows wrapper,
PowerShell 5.1/7, Intel hardware, Qoder discovery, host non-bypass or Agent Task Success.

## Pre-candidate portability evidence for rc.3

- Commit `7c067699` passed [GitHub Actions run 33262724723](https://github.com/tty627/ai-airlock/actions/runs/33262724723)
  on both Windows and Ubuntu with Python 3.12: each job reported `210 passed / 8 skipped`, and Ruff plus the
  benchmark smoke test passed.
- The Windows job verified canonical LF checkout bytes even with `core.autocrlf=true`; the benchmark acceptance
  regression launched its parent process with a legacy code page and verified the Chinese task through an
  explicitly UTF-8 child CLI.
- This run predates the rc.3 release-preparation documentation commit. It is supporting portability evidence,
  not exact rc.3 main/tag CI, formal `scripts/run.ps1` evidence, PowerShell 5.1/7 acceptance, real OpenVINO on
  Windows, Qoder host evidence or Intel hardware evidence.

## GitHub publication evidence for rc.3

- Remote annotated tag `v0.1.0-rc.3` has tag object
  `31679f3afb8e3010413b01d7a42df35695b294d3`, peels to commit
  `55eca4ceedb1f7e63e9444b86b32f58f2dccac3f`, and resolves to tree
  `a7392e3893eac83dddd53288785bed1defc1d5a0`.
- The tag is annotated but unsigned, and the repository had no GitHub ruleset at this review. “Immutable” is a
  release-process rule rather than a server-enforced guarantee; every handoff therefore verifies the exact tag
  object as well as its peeled commit and tree.
- Exact-SHA main CI: [GitHub Actions run 33264778975](https://github.com/tty627/ai-airlock/actions/runs/33264778975),
  `success`; Ubuntu job `99132798963` and Windows job `99132799076`.
- Candidate tag CI: [GitHub Actions run 33264852242](https://github.com/tty627/ai-airlock/actions/runs/33264852242),
  `success`; Ubuntu job `99132994364` and Windows job `99132994474`.
- All four Python 3.12 jobs reported `210 passed / 8 skipped`, passed Ruff and format checks, and passed the
  benchmark smoke test. Each set of eight skips was explicitly due to the prepared OpenVINO model/runtime being
  unavailable. Both Windows jobs also passed the canonical-LF checkout gate with `core.autocrlf=true`.
- This proves the published source identity and scoped Python portability CI. It does not run `scripts/run.ps1`,
  PowerShell 5.1/7 wrapper acceptance, a prepared Windows OpenVINO model, Qoder host integration or Intel
  hardware validation.

## Formal Windows validation evidence for rc.3

- The tested checkout reproduced the immutable rc.3 tag object, commit and tree and remained unmodified.
- Cold `health --json` through `scripts/run.ps1` failed on both Windows PowerShell 5.1 and PowerShell 7 with
  exit `2`, empty stdout and the fixed error code `AIRLOCK_MODEL_PREPARATION_FAILED`.
- External diagnostics against the unchanged candidate isolated the failure after the OpenVINO inference smoke
  test: cached OpenVINO native handles retained files in the candidate model directory, so the atomic directory
  rename failed with `PermissionError` / WinError 5. This is a bounded root-cause diagnosis, not a repaired rc.3.
- Qoder was not installed or discoverable, so discovery, the 12+12 trigger matrix and Capsule-only flagship are
  `NOT_RUN`. The named Intel CPU does not constitute successful Intel inference or performance evidence.
- The sanitized report and `SHA256SUMS` are stored outside the checkout and have not been published at a public
  URL. Private diagnostic artifacts must not be copied into a public bundle.

The rc.3 verdict is `FAIL`. Later rc.4 evidence does not repair, replace or reinterpret this immutable history.

## GitHub publication evidence for rc.4

- Remote annotated tag `v0.1.0-rc.4` has tag object
  `2a50625aa95443e328573704cf42e9c633621ffe`, peels to commit
  `52a215727115f32937cb78561e88a63fdae5adf2`, and resolves to tree
  `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`.
- The tag is annotated but unsigned. Candidate immutability is a release-process rule, so handoffs continue to
  verify the exact tag object, peeled commit and tree rather than trusting a floating ref.
- Exact-SHA main CI: [GitHub Actions run 33293985019](https://github.com/tty627/ai-airlock/actions/runs/33293985019),
  `success`; Windows job `99210391718` and Ubuntu job `99210391785`.
- Candidate tag CI: [GitHub Actions run 33294040300](https://github.com/tty627/ai-airlock/actions/runs/33294040300),
  `success`; Windows job `99210537344` and Ubuntu job `99210537462`.
- All four Python 3.12 jobs reported `212 passed / 8 skipped`, passed Ruff and format checks, and passed the
  benchmark smoke test. Each set of eight skips was due to the prepared OpenVINO model/runtime being unavailable;
  the Windows jobs also passed the canonical-LF checkout gate.
- This is exact-candidate scoped Python CI. It does not install and exercise the prepared Windows OpenVINO path,
  run `scripts/run.ps1` as the production wrapper, validate PowerShell 5.1/7 host behavior, open Qoder, or measure
  Intel performance.

## Exact-tag Windows evidence for rc.4

- A fresh checkout resolved and tested the exact rc.4 tag object, commit and tree above. The tested source remained
  bound to that identity.
- The regression subset passed independent process-cold and warm `health` checks through Windows PowerShell 5.1
  and PowerShell 7, Chinese-plus-space-path `analyze`, fixed invalid/missing-input error contracts, and a
  cross-shell concurrent-cold scenario.
- Wrapper exit left `0` residual child processes. Across 26 stdout/stderr surfaces, checks of all 252 frozen
  known-fixture forbidden markers observed `0` hits. This is a bounded marker/surface observation, not a universal
  zero-leakage result.
- The source-artifact cache was prefilled before this run, so “cold” does not prove an empty-cache source download
  or bootstrap. Network activity was `NOT_MEASURED`, and the remaining timeout/fault matrix was `NOT_RUN`.
  These limits remain attached to the earlier functional subset.
- A later required PowerShell 7 orphan-pipe fault on the same immutable exact tag returned in `32.164s` with exit
  `2`, empty stdout and one fixed `AIRLOCK_INVALID_JSON`. The direct gate parent had exited, but one descendant
  still held the redirected pipes and remained alive after wrapper return. The external harness observed residual
  counts `1` before its exact-PID cleanup and `0` after cleanup. Deadline and fixed-error normalization passed;
  the no-residual-process contract failed. This makes the rc.4 Windows wrapper and candidate verdict `FAIL`.
- Separately, Qoder was absent/not discoverable and remained `NOT_RUN`; no discovery, 12+12 trigger, Capsule-only,
  non-bypass, final-answer or Agent Task Completed evidence exists. Intel performance was also `NOT_RUN`. These
  unknowns do not dilute the observed rc.4 failure and are not its cause.
- The external sanitized report bundle has no public URL. Its manifest verification is `99/99`, and the SHA-256 of
  its top-level `SHA256SUMS` file is `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`.
- The later failure bundle is separate: manifest verification `29/29`, top-level `SHA256SUMS` file SHA-256
  `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`. Neither bundle has a public URL.
- The later rc.5 repair does not rewrite this history. rc.4 remains a formal failure even though a new immutable
  candidate now closes the observed orphan-pipe defect.

## GitHub publication evidence for rc.5

- Remote annotated tag `v0.1.0-rc.5` has tag object
  `7d4034f9e8575658190dacef53f9ba749de8ed6c`, peels to commit
  `9abf825943f8f68f2bc6cd3afc1baa8717e0c01a`, and resolves to tree
  `88b914598de60fa385820860b13dc8bd6db26b7d`.
- The tag is annotated but unsigned. Candidate immutability remains a release-process rule; handoffs verify the
  exact tag object, peeled commit and tree.
- Exact-SHA main CI: [GitHub Actions run 33298393856](https://github.com/tty627/ai-airlock/actions/runs/33298393856),
  `success`; Windows job `99221893931` and Ubuntu job `99221893989`.
- Candidate tag CI: [GitHub Actions run 33298491017](https://github.com/tty627/ai-airlock/actions/runs/33298491017),
  `success`; Windows job `99222148261` and Ubuntu job `99222148090`.
- Both runs passed Ruff, format and benchmark smoke. Each Windows job reported `225 passed / 8 skipped`; each
  Ubuntu job reported `213 passed / 14 skipped`. The skips reflect unavailable prepared OpenVINO/runtime or
  platform-specific Windows Job support, so this remains scoped Python CI.

## Exact-tag Windows evidence for rc.5

- A detached checkout verified the exact rc.5 tag object, commit and tree above and remained tracked-clean.
- PowerShell 7 and Windows PowerShell 5.1 orphan-pipe fault runs returned the fixed `AIRLOCK_INVALID_JSON` error
  in `3.937s` and `3.352s`. Both observed residual `0` before external cleanup, recorded
  `cleanup_performed=false`, and left no candidate process alive after wrapper return.
- Independent health and post-fault health controls passed in both shells. Chinese task text against a
  Chinese-plus-space target path also passed in both shells with six files, eight facts, OpenVINO CPU metadata,
  no fallback and `raw_sensitive_spans_forwarded=0`; the path was not forwarded.
- The source-artifact cache was prefilled for this scoped run. Empty-cache source bootstrap is `NOT_RUN`, network
  is `NOT_MEASURED`, and the remaining external timeout/fault cases are `NOT_RUN`. Qoder host and Intel
  performance remain independent `NOT_RUN` items.
- The checkout-external sanitized bundle has no public URL. Its manifest verifies `55/55`; the SHA-256 of its
  top-level `SHA256SUMS` file is
  `107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`.
- The bounded verdict is `RC5_WINDOWS_SCOPED_VALIDATION=PASS_WITH_SCOPE`; full rc.5 Windows/candidate acceptance
  remains `INCONCLUSIVE`. This post-tag documentation update is not part of the frozen rc.5 identity.

## Current blockers and decisions

### Confirmed public GitHub identity

- Repository: `https://github.com/tty627/ai-airlock`, public.
- Project license: Apache-2.0.
- Copyright: 2026 谭天晔.
- Public author/byline: 谭天晔.
- Previous Candidates: immutable `v0.1.0-rc.3` and `v0.1.0-rc.4`, both with formal Windows verdict `FAIL`.
- Current Candidate Tag: annotated, unsigned, published `v0.1.0-rc.5`; exact tag object, commit and tree are recorded
  above. rc.1 through rc.5 are never moved by release policy.

Model distribution remains a later publication decision: fixed upstream revision plus local conversion, or a
separately licensed hosted IR.

### Technical blockers before publication

- `mem_need_gb=1.0` now rounds above the observed `0.702 GiB` Windows OpenVINO analyze process-tree peak.
- `server_alive_timeout=300` now uses the documented default and non-template `info.json` fields are removed.
- Confirm that the real upload parser accepts the intentional self-managed-model declaration `models=[]`.
- Resolve Skill frontmatter, zip-root and naming behavior using the real ModelScope upload/preflight path.
- Publish the sanitized rc.3/rc.4 historical and rc.5 current Windows report bundles at public URLs after review;
  the external copies are not public.
- Preserve rc.4 remaining timeout/fault cases and network measurement as historical `NOT_RUN` / `NOT_MEASURED`;
  rerunning them on rc.4 can add diagnostic evidence but cannot reverse its blocking orphan-pipe `FAIL`.
- Complete the Windows empty-cache, network and remaining timeout/fault matrix against exact rc.5. The observed
  orphan-pipe no-residual-process oracle already passes, but it does not substitute for the unexecuted cases.
- Run Qoder discovery, 12+12 triggers, Capsule-only/non-bypass and Agent Task Completed against exact rc.5. A later
  exact-rc.4 Qoder run would be historical evidence only and would not repair rc.4's verdict.
- Run the declared Intel performance oracle; current bounded wrapper functionality is not performance evidence.
- GitHub preflight must account for the deliberately synthetic AWS-shaped detector fixture in
  `tests/unit/test_detectors.py`; it is not a credential, but push protection may still require an explicit safe
  resolution. Do not delete the test or weaken detection merely to silence a scanner.

## Required reading order

1. This file — current project state.
2. [`README.md`](README.md) — public overview and bounded rc.1 evidence.
3. [`SKILL.md`](SKILL.md) — current Agent behavior contract.
4. [`docs/windows-validation-handoff.md`](docs/windows-validation-handoff.md) — Windows operator handoff.
5. [`docs/qoder_acceptance.md`](docs/qoder_acceptance.md) — authoritative Windows/Qoder oracle.
6. [`docs/trae-acceptance.md`](docs/trae-acceptance.md) — TraeCode installation and host oracle.
7. [`docs/release-metadata.md`](docs/release-metadata.md) — measured memory and runtime field evidence.
8. [`docs/windows-validation-report-template.md`](docs/windows-validation-report-template.md) — evidence report.
9. [`docs/submission-checklist.md`](docs/submission-checklist.md) — competition GO/NO-GO checklist.
10. [`docs/publication-runbook.md`](docs/publication-runbook.md) — GitHub/ModelScope release procedure.

`PROJECT_SPEC.md` is a historical design draft. `docs/final-integrator-report.md` and
`docs/relevance-closure-report.md` are historical internal audits. They are not the current runtime contract and
must not be included in the public Skill archive.

## Next actions in order

1. Preserve rc.3/rc.4 failure history and the immutable rc.5 identity; do not move any published tag.
2. On exact rc.5, run the empty source-cache/network and remaining timeout/fault cases without rewriting rc.4
   history.
3. Complete TraeCode login and execute real discovery, the deadline-critical trigger set, Capsule-only/non-bypass
   and Agent Task Completed against the next immutable candidate. Qoder's larger 12+12 matrix remains hardening.
4. Execute the named-device Intel performance oracle; do not infer performance from functional health/analyze.
5. Review and publish the sanitized rc.3/rc.4/rc.5 report bundles, then update public URLs and any later claims from
   the same evidence identities without copying private diagnostic artifacts.
6. Use the existing publication authorization after closing login and platform preflight blockers.

## Update rules

- Distinguish `VERIFIED`, `NOT_RUN`, `BLOCKED` and `INCONCLUSIVE`; do not turn a prepared test into a pass.
- Do not copy new numerical claims directly into README or images. Admit them through the Claims Ledger first.
- Do not treat Mac CLI rehearsal, static PowerShell review, CI, or screenshots as real Qoder host evidence.
- Never store raw Secret/PII/injection values in status files, reports, command output, screenshots or public
  evidence.
