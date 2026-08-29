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

Previous Windows candidate: v0.1.0-rc.2 (immutable; superseded for Windows validation)
Windows candidate tag:      v0.1.0-rc.3
Windows candidate commit:   [OWNER_HANDOFF_AFTER_TAG_CREATION]
Windows candidate tree:     [OWNER_HANDOFF_AFTER_TAG_CREATION]
GitHub remote:               https://github.com/tty627/ai-airlock (public)
```

`v0.1.0-rc.1` and `v0.1.0-rc.2` remain immutable. `v0.1.0-rc.2` is superseded for formal Windows validation
because canonical-LF checkout and Windows legacy-code-page benchmark defects were corrected after that tag.
`v0.1.0-rc.3` freezes those portability corrections plus the reviewed documentation and Windows handoff. Run
formal Windows acceptance only from the immutable `v0.1.0-rc.3` tag, and cross-check the resolved commit and tree
against the owner's post-tag handoff; do not validate floating `main`. If this candidate fails, create a new tag
rather than moving an existing one.

## Status summary

| Area | State | Current evidence | Next gate |
|---|---|---|---|
| Python security core | `VERIFIED` | Frozen rc.1 clean-checkout evidence | Re-run on the future release candidate |
| macOS / Apple M4 / OpenVINO CPU | `VERIFIED` | Fixed model revision, public CLI, strict Python response gate, flagship and synthetic A/B | Do not extrapolate to Windows, Intel or Qoder |
| Numerical public claims | `VERIFIED_WITH_SCOPE` | [Claims Ledger](docs/claims-ledger.md) and frozen JSON | Keep estimator, fixture, device and commit qualifiers |
| Competition docs and visuals | `READY_FOR_CANDIDATE_REVIEW` | README, article draft, seven SVG/PNG pairs, demo script | Validate from a clean candidate checkout and target renderers |
| Windows PowerShell 5.1 / 7 | `NOT_RUN` | Static wrapper and acceptance oracle only | Cold/warm, paths, errors, concurrency and residual-process checks |
| Qoder host integration | `NOT_RUN` | 12 positive and 12 negative trigger specifications | Real discovery, tool trace, Capsule-only and non-bypass evidence |
| Intel hardware | `NOT_RUN` | None | Named device and cold/warm performance evidence, or explicit limitation |
| Release metadata | `BLOCKED` | Apache-2.0, copyright and author are confirmed; remaining issues are documented in the publication runbook | Memory, timeout, model and parser decisions |
| GitHub / Python CI | `VERIFIED_WITH_SCOPE` | Public repository, immutable rc.2 evidence, and successful Windows/Ubuntu Python 3.12 portability CI on pre-candidate commit `7c06769` | Require exact rc.3 main/tag CI before owner handoff; this is not wrapper/Qoder evidence |
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

## Current blockers and decisions

### Confirmed public GitHub identity

- Repository: `https://github.com/tty627/ai-airlock`, public.
- Project license: Apache-2.0.
- Copyright: 2026 谭天晔.
- Public author/byline: 谭天晔.
- Candidate Tag: immutable `v0.1.0-rc.3` after exact-SHA main CI; `v0.1.0-rc.2` is never moved.

Model distribution remains a later publication decision: fixed upstream revision plus local conversion, or a
separately licensed hosted IR.

### Technical blockers before publication

- Measure `info.json.mem_need_gb` as model residency plus inference peak; current `0.25` is not release evidence.
- Confirm the host meaning of `server_alive_timeout=0`.
- Confirm that the platform accepts `models=[]` and the current extra `info.json` fields.
- Resolve Skill frontmatter, zip-root and naming behavior using the real ModelScope upload/preflight path.
- Publish a sanitized evidence bundle with URL and SHA-256; the local ignored `.release-evidence/` is not public.
- Complete real Windows/Qoder validation and preserve sanitized traces plus uncut private recordings.
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

1. Commit the rc.3 release-preparation documents and require Windows/Ubuntu CI on that exact SHA.
2. Create and publish the annotated `v0.1.0-rc.3` tag without moving prior tags; verify the remote tag object,
   peeled commit, tree and tag-triggered CI externally.
3. Provide the exact commit/tree in the owner handoff. On Windows, clone and detach at that exact tag and return
   a sanitized validation report. A failure or inconclusive result creates a new candidate.
4. Only after evidence review, update this file, the Claims Ledger, public wording, article and visuals from the
   same run identity.

## Update rules

- Distinguish `VERIFIED`, `NOT_RUN`, `BLOCKED` and `INCONCLUSIVE`; do not turn a prepared test into a pass.
- Do not copy new numerical claims directly into README or images. Admit them through the Claims Ledger first.
- Do not treat Mac CLI rehearsal, static PowerShell review, CI, or screenshots as real Qoder host evidence.
- Never store raw Secret/PII/injection values in status files, reports, command output, screenshots or public
  evidence.
