# Windows Intel CPU Evidence · v0.1.0-rc.6

> Evidence date: 2026-08-30  
> Scope: exact `v0.1.0-rc.6` Skill package, synthetic payment-incident fixture, Windows Intel CPU.  
> This is functional and warm-latency evidence. It is not NPU/GPU evidence, a universal security guarantee,
> or a production-Agent host acceptance result.

## Candidate identity

| Field | Value |
|---|---|
| Annotated tag | `v0.1.0-rc.6` |
| Tag object | `ce81652ad107c59c52184c33417d1e9922d44281` |
| Commit | `2ea713a99053dae5ff96f8e9927c300d36439c0e` |
| Tree | `3a1554d94892baf8b32dbbdaedbe6f334d6f952c` |
| Skill archive SHA-256 | `8be21cf914a1488c09435e2c242c97e54fdb5cad63dbc783bed8c6e175055d09` |
| Archive size | `1,297,879` bytes |

The archive was extracted into a fresh TraeCode project Skill location. A separate clean archive install passed
`228 passed / 9 skipped`; the skips were limited to unavailable prepared-model and Windows symlink conditions.
The exact rc.6 main and tag GitHub Actions runs also passed on Windows and Ubuntu.

## Environment

| Field | Value |
|---|---|
| OS | Windows 11 Enterprise `10.0.26200` (build `26200`) |
| CPU | Intel Core i7-14700KF · 20 cores / 28 logical processors |
| PowerShell | 7.6.4; Windows PowerShell 5.1.26100.8457 |
| Python | 3.12.10 |
| OpenVINO | `2026.3.1-22476-759c5a6ab8c-releases/2026/3` |
| Model | `intfloat/multilingual-e5-small` |
| Model revision | `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| OpenVINO device reported by the Skill | `CPU` |

The tested Intel Core i7-14700KF is a desktop CPU. No NPU or GPU execution is claimed.

## Wrapper trajectory

The production `scripts/run.ps1` entry point analyzed a six-file synthetic incident directory with the task:

```text
定位支付服务超时根因并给出修复建议
```

The invocation used `--relevance-backend openvino --json`. Every measured response satisfied all of these
oracles:

- exit `0`;
- `decision=ALLOW_WITH_TRANSFORM`;
- `inference.mode=openvino_embedding`;
- `inference.device=CPU`;
- `inference.fallback_state=not_used`;
- `inference.chunks_processed=71`;
- six files inspected and eight facts returned;
- `privacy.raw_sensitive_spans_forwarded=0`;
- every fact retained relative `source` and 1-based `local_ref` provenance.

The representative capsule reported `3627` estimated original tokens and `888` estimated capsule tokens,
using `utf8_bytes_div_4_ceil_v1`, for a `0.75517` reduction ratio. This estimator is not a tokenizer-accurate
token count and the result applies only to this fixture.

## Warm latency sample

The model and Skill environment were prepared before timing. Seven sequential subprocess invocations were
measured end to end through the PowerShell wrapper. The inner process output was parsed as JSON and checked
against the response oracles above before the sample was accepted.

| Run | End-to-end latency |
|---:|---:|
| 1 | `5193.160 ms` |
| 2 | `4960.695 ms` |
| 3 | `5021.198 ms` |
| 4 | `5021.900 ms` |
| 5 | `5144.965 ms` |
| 6 | `5074.769 ms` |
| 7 | `4994.198 ms` |

| Aggregate | Value |
|---|---:|
| Sample count | `7` |
| Minimum | `4960.695 ms` |
| P50 | `5021.900 ms` |
| P95 | `5193.160 ms` |
| Maximum | `5193.160 ms` |
| Contract-valid runs | `7/7` |

The percentile calculation uses the nearest-rank index over this small seven-run sample. The numbers include
PowerShell and Python process startup, model load, tokenization, embedding, ranking, policy checks and JSON
serialization. They are useful as a deadline-candidate measurement, not as a general OpenVINO benchmark.

## Memory measurement

The same prepared Windows environment previously observed a peak process-tree working set of `0.702 GiB`
during OpenVINO analyze. `info.json.mem_need_gb` therefore reserves `1.0 GiB`. Sampling can miss brief peaks, so
hosts should retain additional headroom.

## Claim boundary

This evidence proves that the exact rc.6 package can execute its production wrapper on a named Intel CPU and
return a contract-valid OpenVINO Safe Context Capsule repeatedly. It does not prove TraeCode discovery,
Capsule-only Agent reasoning, host non-bypass, task-period network isolation, NPU/GPU acceleration, or unknown-
input leakage resistance. Those are independent acceptance claims.
