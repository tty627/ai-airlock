# AI Airlock release evidence protocol

## Purpose

本文件定义 release evidence 的生成和绑定规则，不保存某次运行的可变结果。正式 source RC
commit 必须先冻结；随后从该 SHA 的全新 clean checkout 执行验证，把结果写到 checkout 外：

```text
.release-evidence/<40-char-rc-sha>/
```

`.release-evidence/` 被 Git 忽略，避免“提交证据后 commit SHA 改变”的自引用。最终 evidence
manifest、benchmark JSON/Markdown 和任何 hash 必须全部声明同一个 40 字符 source RC SHA。
若创建 annotated tag 或 Git note，它也必须直接指向该 source RC commit。

## Source / generated boundary

必须进入 source RC：

- `src/airlock/`、`scripts/`、`SKILL.md`、配置与元数据；
- `.github/workflows/ci.yml`、`.qoderignore`；
- `benchmark/run_benchmark.py`、`variants.json`、固定 datasets 与 benchmark 文档；
- unit、integration、acceptance tests；
- 当前架构、安全边界、Qoder 验收和发布说明。

不得进入 source RC：

- `.venv*`、`models/`、下载缓存、egg-info、Python/pytest/Ruff cache；
- 临时 probe、临时 checkout、audit JSONL；
- `benchmark/results/latest.*` 或其他绑定旧/临时 SHA 的生成报告；
- 真实 secret、PII、凭证或可恢复它们的证据。

## Required clean-checkout sequence

下面的 `RC_CHECKOUT` 必须是从正式仓库 commit 新建的 clone；`EVIDENCE_ROOT` 必须位于其外部。

```bash
RC_CHECKOUT=/absolute/path/to/clean-checkout
EVIDENCE_ROOT=/absolute/path/to/.release-evidence/<rc-sha>

cd "$RC_CHECKOUT"
git rev-parse HEAD
git rev-parse HEAD^{tree}
git status --porcelain --untracked-files=all

python3.12 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -e '.[dev]'
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q

.venv/bin/python -m pip install --disable-pip-version-check -e '.[openvino]'
.venv/bin/python -m pip check

cd /tmp
env -u PYTHONPATH -u AI_AIRLOCK_EMBEDDING_MODEL_DIR \
  HF_HOME="$EVIDENCE_ROOT/hf-home" \
  HF_HUB_DISABLE_XET=1 \
  AI_AIRLOCK_MODEL_CACHE="$EVIDENCE_ROOT/model-cache" \
  "$RC_CHECKOUT/.venv/bin/python" \
  "$RC_CHECKOUT/scripts/prepare_embedding_model.py"

cd "$RC_CHECKOUT"
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
git diff --check

cd /tmp
"$RC_CHECKOUT/.venv/bin/python" -m airlock.cli analyze \
  --task '找到支付服务故障根因并给出修复建议' \
  --path "$RC_CHECKOUT/demo/incident" \
  --relevance-backend openvino \
  --json

cd "$RC_CHECKOUT"
.venv/bin/python benchmark/run_benchmark.py \
  --compare \
  --output-dir "$EVIDENCE_ROOT/benchmark"

git status --porcelain --untracked-files=all
```

首尾两次 status 都必须为空。模型准备必须从不存在的最终 target 开始并返回 `status=ready`；
`already_ready` 不能证明本次 clean-checkout 完成了 prepare。

## Required manifest fields

最终 `.release-evidence/<sha>/release-evidence.md` 至少记录：

- 完整 commit SHA、tree SHA、branch/tag、验证前后 clean status；
- Python、OS/build、architecture/CPU；
- OpenVINO、OpenVINO GenAI、OpenVINO Tokenizers、NumPy、Transformers；
- model id、固定 revision、model manifest SHA-256、device；
- base install、OpenVINO extra、`pip check`；
- base/full pytest 的 passed/failed/skipped 与 skip 原因；
- Ruff lint、Ruff format、`git diff --check`；
- 与 QP-01 使用同一 task 的 macOS public-CLI flagship decision、3/3 required facts、stderr、
  OpenVINO metadata；真实 Qoder QP-01 另行记录且不得由该项替代；
- benchmark run ID、总体/两 variant 状态、输入 hashes、JSON/Markdown SHA-256；
- 未验证边界，包括真实 Windows/PowerShell/Qoder、远端 CI 或 Intel device（如仍未执行）。

最终判定必须显式输出：

```text
OFFICIAL CLEAN CHECKOUT = PASS | FAIL
RELEASE CANDIDATE = YES | NO
```

本地 source RC 可以与比赛 submission readiness 分开判断；不得用 macOS/Python evidence 冒充
Windows/Qoder 或 Intel 实机验收。

Windows/Qoder 验收必须从不可变候选 Tag 开始，按
[`windows-validation-handoff.md`](windows-validation-handoff.md) 执行，并将
[`windows-validation-report-template.md`](windows-validation-report-template.md) 复制到仓库外的 evidence
目录填写。未经脱敏审阅的 Windows transcript、截图和录像不得提交到 source repository。
