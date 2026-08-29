# AI Airlock Windows Validation Report Template

> Copy this file to the external evidence directory. Do not fill it inside the tested checkout.
> Never include raw Secret/PII/injection values, tokens, usernames, machine names or unredacted absolute paths.

## 1. Verdict

```text
OVERALL_VERDICT:       NOT_RUN | PASS | FAIL | INCONCLUSIVE
WINDOWS_POWERSHELL:    NOT_RUN | PASS | FAIL | INCONCLUSIVE
QODER_DISCOVERY:       NOT_RUN | PASS | FAIL | INCONCLUSIVE
QODER_TRIGGER_MATRIX:  NOT_RUN | PASS | FAIL | INCONCLUSIVE
CAPSULE_ONLY_FLAGSHIP: NOT_RUN | PASS | FAIL | INCONCLUSIVE
LEAKAGE_REVIEW:        NOT_RUN | PASS | FAIL | INCONCLUSIVE
```

Reason for final verdict:

```text
[One bounded paragraph. Do not replace missing evidence with an assumption.]
```

## 2. Candidate identity

| Field | Value |
|---|---|
| Source repository URL | `[REDACT ONLY IF PRIVATE]` |
| Candidate tag | |
| Expected commit | |
| Actual HEAD | |
| Tag commit | |
| Expected tree | |
| Actual tree | |
| Initial worktree clean | `YES / NO` |
| Clone UTC timestamp | |
| Run ID | |

Identity verdict: `PASS / FAIL / INCONCLUSIVE`

## 3. Environment

| Field | Value |
|---|---|
| Windows edition/build | |
| Architecture / CPU model | |
| Intel device | `YES / NO / UNKNOWN`; exact model if safe |
| Windows PowerShell | |
| PowerShell 7 | |
| Python | |
| Git | |
| Qoder IDE/CLI | |
| OpenVINO Runtime | |
| Network policy/window | |
| Evidence root | `[REDACTED PATH HASH OR SAFE ALIAS]` |

Do not record computer name, username, serial number, organization account or network endpoint.

## 4. Candidate file hashes

| File | SHA-256 |
|---|---|
| `SKILL.md` | |
| `scripts/run.ps1` | |
| `.qoderignore` | |
| `meta.json` | |
| `info.json` | |
| Permission baseline | |

## 5. Windows wrapper results

| Case | Shell | State | Exit | Stdout contract | Stderr contract | Duration | Evidence ref |
|---|---|---|---:|---|---|---:|---|
| Cold health | PowerShell 5.1 | `NOT_RUN` | | | | | |
| Warm health | PowerShell 5.1 | `NOT_RUN` | | | | | |
| Cold health | PowerShell 7 | `NOT_RUN` | | | | | |
| Warm health | PowerShell 7 | `NOT_RUN` | | | | | |
| Chinese task | both | `NOT_RUN` | | | | | |
| Space path | both | `NOT_RUN` | | | | | |
| Fixed error JSON | both | `NOT_RUN` | | | | | |
| Concurrent cold start | required shells | `NOT_RUN` | | | | | |
| Timeout/fault path | disposable copy | `NOT_RUN` | | | | | |
| Residual process check | required shells | `NOT_RUN` | | | | | |

Cold bootstrap network summary:

```text
[Count, purpose and bounded time window; no credential or endpoint values.]
```

Warm task-period unexpected network count: `[NOT_RUN / integer / UNKNOWN]`

## 6. Qoder discovery and isolation

| Check | State | Evidence ref / note |
|---|---|---|
| Exact Skill visible | `NOT_RUN` | |
| Loaded Skill source recorded | `NOT_RUN` | |
| No duplicate Skill | `NOT_RUN` | |
| `.qoderignore` active before open | `NOT_RUN` | |
| Actual merged permissions recorded | `NOT_RUN` | |
| No prior index/workspace contamination | `NOT_RUN` | |
| No attachment/editor/raw-read path | `NOT_RUN` | |

If any contamination cannot be ruled out, non-bypass is `INCONCLUSIVE`.

## 7. Positive trigger matrix

| ID | State | Skill selected | First content action correct | Decision/oracle | Capsule-only | Evidence ref |
|---|---|---|---|---|---|---|
| QP-01 | `NOT_RUN` | | | | | |
| QP-02 | `NOT_RUN` | | | | | |
| QP-03 | `NOT_RUN` | | | | | |
| QP-04 | `NOT_RUN` | | | | | |
| QP-05 | `NOT_RUN` | | | | | |
| QP-06 | `NOT_RUN` | | | | | |
| QP-07 | `NOT_RUN` | | | | | |
| QP-08 | `NOT_RUN` | | | | | |
| QP-09 | `NOT_RUN` | | | | | |
| QP-10 | `NOT_RUN` | | | | | |
| QP-11 | `NOT_RUN` | | | | | |
| QP-12 | `NOT_RUN` | | | | | |

Positive total: `[0/12 REAL_QODER_EXECUTED until filled]`

## 8. Negative trigger matrix

| ID | State | Skill not selected | Airlock not called | Normal task behavior | Evidence ref |
|---|---|---|---|---|---|
| QN-01 | `NOT_RUN` | | | | |
| QN-02 | `NOT_RUN` | | | | |
| QN-03 | `NOT_RUN` | | | | |
| QN-04 | `NOT_RUN` | | | | |
| QN-05 | `NOT_RUN` | | | | |
| QN-06 | `NOT_RUN` | | | | |
| QN-07 | `NOT_RUN` | | | | |
| QN-08 | `NOT_RUN` | | | | |
| QN-09 | `NOT_RUN` | | | | |
| QN-10 | `NOT_RUN` | | | | |
| QN-11 | `NOT_RUN` | | | | |
| QN-12 | `NOT_RUN` | | | | |

Negative total: `[0/12 REAL_QODER_EXECUTED until filled]`

## 9. Capsule-only flagship

| Check | State | Evidence ref / bounded observation |
|---|---|---|
| Fresh interactive session | `NOT_RUN` | |
| Runtime prewarmed outside task window | `NOT_RUN` | |
| First content access is exact wrapper | `NOT_RUN` | |
| Wrapper exit/stdout/stderr contract | `NOT_RUN` | |
| OpenVINO metadata and fixed revision | `NOT_RUN` | |
| Only complete `safe_context` used | `NOT_RUN` | |
| Required facts retained | `NOT_RUN` | `[x/3]` |
| `source:local_ref` citations | `NOT_RUN` | |
| No blocked value/instruction reproduced | `NOT_RUN` | |
| Task-period unexpected network | `NOT_RUN` | `[count / UNKNOWN]` |
| Residual child processes | `NOT_RUN` | `[count / UNKNOWN]` |
| Final Agent task answer | `NOT_RUN` | `[sanitized evidence ref]` |

Do not import the Mac/English benchmark reduction number as the Chinese QP-01 result.

## 10. Leakage review

| Surface | Marker-set scope | Denominator | Hits | State | Evidence ref |
|---|---|---:|---:|---|---|
| Capsule | | | | `NOT_RUN` | |
| Wrapper stdout | | | | `NOT_RUN` | |
| Wrapper stderr | | | | `NOT_RUN` | |
| Audit | | | | `NOT_RUN` | |
| Controlled errors/exceptions | | | | `NOT_RUN` | |
| Qoder transcript/final answer | | | | `NOT_RUN` | |
| Screenshots/captions | | | | `NOT_RUN` | |

Boundary statement:

```text
[Example: No known-fixture marker was observed in the named checked surfaces for this run. This does not prove
unknown values cannot leak and is not a universal zero-leakage claim.]
```

## 11. Evidence manifest

| Artifact | Public/private | Sanitized | SHA-256 | Purpose |
|---|---|---|---|---|
| | | | | |

Top-level `SHA256SUMS` verification: `NOT_RUN / PASS / FAIL`

## 12. Failures, deviations and unknowns

| ID | Severity | State | Minimal reproduction/evidence | Effect on verdict | New candidate required |
|---|---|---|---|---|---|
| | | | | | |

Do not repair the tested checkout. Return failures to the source repository for diagnosis and a new candidate.

## 13. Reviewer sign-off

```text
Executed by:          [PUBLIC ALIAS OR REDACTED]
Execution UTC:
Reviewed by:
Review UTC:
Sanitization review:  NOT_RUN | PASS | FAIL
Manifest review:      NOT_RUN | PASS | FAIL
Final decision:       NOT_RUN | PASS | FAIL | INCONCLUSIVE
```
