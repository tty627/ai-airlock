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

Previous Windows candidate: v0.1.0-rc.3 (immutable; formal Windows verdict FAIL)
Windows candidate tag:      v0.1.0-rc.4 (annotated, unsigned, published; immutable by release policy)
Windows candidate tag object: 2a50625aa95443e328573704cf42e9c633621ffe
Windows candidate commit:   52a215727115f32937cb78561e88a63fdae5adf2
Windows candidate tree:     46bc0f55eed58b7234338d4ff4e32bc71c348f8a
GitHub remote:               https://github.com/tty627/ai-airlock (public)
```

`v0.1.0-rc.1`, `v0.1.0-rc.2` and `v0.1.0-rc.3` remain immutable. Formal Windows validation of exact rc.3
failed during cold health on both Windows PowerShell 5.1 and PowerShell 7. `v0.1.0-rc.4` is now an annotated,
unsigned, published candidate with the exact identity above. The tag remains immutable by release policy; never
infer candidate identity from floating `main`, and never move an existing tag.

## Status summary

| Area | State | Current evidence | Next gate |
|---|---|---|---|
| Python security core | `VERIFIED` | Frozen rc.1 clean-checkout evidence | Re-run on the future release candidate |
| macOS / Apple M4 / OpenVINO CPU | `VERIFIED` | Fixed model revision, public CLI, strict Python response gate, flagship and synthetic A/B | Do not extrapolate to Windows, Intel or Qoder |
| Numerical public claims | `VERIFIED_WITH_SCOPE` | [Claims Ledger](docs/claims-ledger.md) and frozen JSON | Keep estimator, fixture, device and commit qualifiers |
| Competition docs and visuals | `READY_FOR_CANDIDATE_REVIEW` | README, article draft, seven SVG/PNG pairs, demo script | Validate from a clean candidate checkout and target renderers |
| Windows PowerShell 5.1 / 7 | `FAIL_RC3 / RC4_FUNCTIONAL_SUBSET_PASS / RC4_ORPHAN_FAULT_FAIL / RC4_CANDIDATE_FAIL` | The earlier exact-rc.4 subset passed, but the required orphan-pipe oracle left one nonce-matched descendant alive after wrapper return | Validate the post-rc.4 untagged isolation fix, then create and test a new immutable candidate; never move rc.4 |
| Qoder host integration | `NOT_RUN` | Qoder was absent/not discoverable in the rc.4 Windows run; 12 positive and 12 negative trigger specifications remain unexecuted | Real discovery, tool trace, Capsule-only and non-bypass evidence |
| Intel hardware | `PERFORMANCE_NOT_RUN` | rc.4 regression subset established bounded wrapper functionality only | Named Intel device, cold/warm latency and successful device/performance oracle, or explicit limitation |
| Overall candidate validation | `FAIL` | Exact rc.4 violated a required Windows no-residual-process oracle | Keep Qoder, Intel, empty-cache and network unknowns separate; none is the cause of this failure |
| Release metadata | `BLOCKED` | Apache-2.0, copyright and author are confirmed; remaining issues are documented in the publication runbook | Memory, timeout, model and parser decisions |
| GitHub / Python CI | `RC4_VERIFIED_WITH_SCOPE` | Exact-SHA rc.4 main/tag CI succeeded on Windows and Ubuntu Python 3.12; all four jobs reported `212 passed / 8 skipped` | Keep prepared-OpenVINO skips and wrapper/Qoder/Intel non-coverage explicit |
| ModelScope publication | `BLOCKED` | Local fields, article and runbook are prepared | Platform preflight, public URLs, real host evidence and user authorization |

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
- The working-tree process-isolation repair is only `POST_RC4_FIX_UNTAGGED / VALIDATION_PENDING`; it is not rc.4
  evidence and must not be named as a new candidate until an immutable tag and exact-tag rerun exist.

## Current blockers and decisions

### Confirmed public GitHub identity

- Repository: `https://github.com/tty627/ai-airlock`, public.
- Project license: Apache-2.0.
- Copyright: 2026 谭天晔.
- Public author/byline: 谭天晔.
- Previous Candidate: immutable `v0.1.0-rc.3`, with formal Windows verdict `FAIL`.
- Current Candidate Tag: annotated, unsigned, published `v0.1.0-rc.4`; exact tag object, commit and tree are recorded
  above. rc.1 through rc.4 are never moved by release policy.

Model distribution remains a later publication decision: fixed upstream revision plus local conversion, or a
separately licensed hosted IR.

### Technical blockers before publication

- Measure `info.json.mem_need_gb` as model residency plus inference peak; current `0.25` is not release evidence.
- Confirm the host meaning of `server_alive_timeout=0`.
- Confirm that the platform accepts `models=[]` and the current extra `info.json` fields.
- Resolve Skill frontmatter, zip-root and naming behavior using the real ModelScope upload/preflight path.
- Publish the sanitized rc.4 Windows report bundle at a public URL after review; its manifest `99/99` and top-level
  `SHA256SUMS` file hash are recorded above, but the current external copy is not public.
- Preserve rc.4 remaining timeout/fault cases and network measurement as historical `NOT_RUN` / `NOT_MEASURED`;
  rerunning them on rc.4 can add diagnostic evidence but cannot reverse its blocking orphan-pipe `FAIL`.
- Form a new immutable candidate from the post-rc.4 isolation fix, then run the complete Windows timeout/fault and
  network matrix against that exact identity; publication requires its no-residual-process oracle to `PASS`.
- Run Qoder discovery, 12+12 triggers, Capsule-only/non-bypass and Agent Task Completed against the new immutable
  candidate. A later exact-rc.4 Qoder run would be historical evidence only and would not repair rc.4's verdict.
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
6. [`docs/windows-validation-report-template.md`](docs/windows-validation-report-template.md) — evidence report.
7. [`docs/submission-checklist.md`](docs/submission-checklist.md) — competition GO/NO-GO checklist.
8. [`docs/publication-runbook.md`](docs/publication-runbook.md) — GitHub/ModelScope release procedure.

`PROJECT_SPEC.md` is a historical design draft. `docs/final-integrator-report.md` and
`docs/relevance-closure-report.md` are historical internal audits. They are not the current runtime contract and
must not be included in the public Skill archive.

## Next actions in order

1. Publish the rc.4 failure correction without moving `v0.1.0-rc.4`; preserve both the earlier subset evidence and
   the later blocking fault evidence.
2. Complete local and CI validation of the post-rc.4 untagged process-isolation fix. Only after those gates pass,
   create a new immutable candidate and rerun the exact orphan-pipe oracle on both PowerShell 5.1 and 7.
3. On that later candidate, run the empty source-cache/network and remaining timeout/fault cases without rewriting
   rc.4 history.
4. Make Qoder available and execute the real discovery, 12+12 trigger, Capsule-only/non-bypass and Agent Task
   Completed oracle. Until then its state remains `NOT_RUN`.
5. Execute the named-device Intel performance oracle; do not infer performance from functional health/analyze.
6. Review and publish the sanitized report bundles, then update public URLs and any later claims from that same
   evidence identity.

## Update rules

- Distinguish `VERIFIED`, `NOT_RUN`, `BLOCKED` and `INCONCLUSIVE`; do not turn a prepared test into a pass.
- Do not copy new numerical claims directly into README or images. Admit them through the Claims Ledger first.
- Do not treat Mac CLI rehearsal, static PowerShell review, CI, or screenshots as real Qoder host evidence.
- Never store raw Secret/PII/injection values in status files, reports, command output, screenshots or public
  evidence.
