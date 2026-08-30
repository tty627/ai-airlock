# Release Metadata Evidence

## Windows memory budget

On 2026-08-30, the production wrapper was measured on Windows 11 Enterprise with PowerShell 7.6.4, Python
3.12.10 and the prepared OpenVINO 2026.3.1 model. The measurement sampled the wrapper process and all observed
descendants through `Win32_Process` while running the repository's synthetic `demo/incident` fixture.

| Run | Exit | Observed peak process-tree working set | Result |
|---|---:|---:|---|
| `health --json` | 0 | 0.421 GiB | OpenVINO available |
| OpenVINO `analyze` | 0 | 0.702 GiB | `ALLOW_WITH_TRANSFORM`; `openvino_embedding`; stderr empty |

`info.json.mem_need_gb` is set to **1.0 GiB**, rounding above the largest observed model-plus-inference peak.
This is a Windows candidate budget, not a universal hardware guarantee. Sampling overhead can miss brief peaks;
hosts should retain additional system headroom.

## Runtime fields

- `server_alive_timeout=300` uses the documented default value. AI Airlock v0.1 is a short-lived client and
  does not keep its own model server resident.
- `models=[]` is intentional: the wrapper downloads the fixed
  `intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3` source files, verifies them, and
  converts them locally to OpenVINO IR. No public pre-converted ModelScope model repository exists, so the
  metadata does not invent one. Real upload preflight must confirm the platform accepts this self-managed model
  path.
- Non-template `info.json` fields were removed to minimize parser ambiguity.
- `meta.json.icon` points to the immutable public rc.5 asset; rc.6 does not change that image.

## Intel CPU warm latency

The exact `v0.1.0-rc.6` package was installed into a fresh TraeCode project Skill directory and exercised on
Windows 11 Enterprise with an Intel Core i7-14700KF. Seven sequential warm OpenVINO analyzes all returned the
same contract-valid result: `ALLOW_WITH_TRANSFORM`, CPU device, 71 chunks, eight facts, zero fallback and
`raw_sensitive_spans_forwarded=0`.

The seven-run end-to-end wrapper sample measured P50 `5021.900 ms` and P95 `5193.160 ms`, with a range of
`4960.695–5193.160 ms`. This is a small Intel CPU sample and includes process startup and model load; it is not
NPU/GPU evidence or a general OpenVINO benchmark. Exact identity, environment, per-run values and claim limits
are recorded in [windows-intel-rc6-evidence.md](windows-intel-rc6-evidence.md).
