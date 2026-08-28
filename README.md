# AI Airlock

## Your data stays. Your Agent works.

AI Airlock 是面向 AI Agent 的本地上下文网关。它在本机检测受支持的敏感数据和 Prompt
Injection，并在配置预算内把任务相关证据编译成更小、可追溯的 **Safe Context Capsule**。
“更小”只适用于实际测得缩减的输入；短 micro-fixture 可能因 JSON 元数据而膨胀。

```text
Private workspace -> local Airlock + OpenVINO -> Safe Context Capsule -> Agent
```

当前正式 Skill 的 `analyze` 路径显式使用本地 OpenVINO embedding 做相关证据选择；Secret/PII 检测、脱敏、Prompt Injection 隔离和最终泄漏闸仍是确定性边界。第一次运行会安装锁定的 OpenVINO extra，并在缺少本地模型时准备固定 revision 的模型，因此 cold bootstrap 可能访问 Python 软件源和 Hugging Face；完成预热后，正式分析保持本地执行。若 runtime、模型或 metadata 不一致，wrapper 会 fail closed，不会退回 lexical。

## Qoder Production Skill

Qoder 需要安装完整包，而不只是 `SKILL.md`：用户级位置为 `~/.qoder/skills/ai-airlock/`，项目级位置为 `.qoder/skills/ai-airlock/`。安装后重启 Qoder，或在 Qoder CLI 中执行 `/skills reload`，并确认实际加载的是本次待测副本。

Windows/Qoder 的唯一正式入口是下列机器可读形式：

```powershell
& '<skill-root>\scripts\run.ps1' analyze `
  --task '<user task>' `
  --path '<absolute target path>' `
  --relevance-backend openvino `
  --json
```

Qoder 必须先调用该入口，再只依据返回的 `safe_context` 完成原任务。安装、正负触发、索引隔离、Windows/OpenVINO 和旗舰手工步骤见 [Qoder 验收规范](docs/qoder_acceptance.md)。本仓库的 `.qoderignore` 会把合成事故目录排除在 Qoder 自动索引之外；它不是 OS 访问控制。

wrapper 只接受文档列出的 `health`、`scan`、`analyze` JSON 参数形态：`--json` 必须且只能出现一次，`scan`/`analyze` 必须有唯一的绝对 Windows `--path`，`analyze` 还必须有唯一非空 `--task` 和唯一 `openvino` backend。正式入口拒绝额外 policy、audit、模型覆盖或其他参数，并在任何 bootstrap 前完成这些纯字符串检查。

## 快速开始

需要 Python 3.12：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m airlock.cli health --json
```

安全分析合成事故目录：

```bash
python -m airlock.cli scan --path demo/incident --json
python -m airlock.cli analyze \
  --task "分析支付服务失败原因，并给出修复建议" \
  --path demo/incident \
  --json
```

## OpenVINO production backend

Python CLI 为开发兼容仍默认 `lexical`；Qoder 的唯一正式 wrapper 则要求显式传入
`--relevance-backend openvino`。请求 OpenVINO 而 runtime、模型或返回 metadata 不可用时会固定失败，绝不会静默退回 lexical。

当前已在 Apple Silicon Mac、原生 arm64 Python 3.12.14 上验证以下流程：

```bash
python3.12 -m venv .venv-openvino
source .venv-openvino/bin/activate
python -m pip install -e ".[dev,openvino]"
python scripts/prepare_embedding_model.py
python -m airlock.cli health --json
python -m airlock.cli analyze \
  --task "找到支付服务故障根因并给出修复建议" \
  --path demo/incident \
  --relevance-backend openvino \
  --json
```

准备脚本锁定 `intfloat/multilingual-e5-small` 的固定 revision，逐文件校验源 SHA-256，
转换为 FP16 OpenVINO IR 和 OpenVINO tokenizer IR，通过真实推理 smoke test 后才原子发布。
转换产物的实际 bytes 和逐文件 SHA-256 写入 `model_manifest.json`，并受代码强制的
`500,000,000` bytes 上限约束；模型目录被 Git 忽略，不进入源码包。Windows wrapper 会从
自身位置解析固定模型目录，并在 cold bootstrap 缺模型时调用同一准备流程；Qoder 正式入口
不接受任意模型目录覆盖。开发用 Python CLI 的 `analyze` 仍可用 `--model-dir` 选择其他已准备目录；若要让
`health` 和 `analyze` 共同使用该目录，应设置 `AI_AIRLOCK_EMBEDDING_MODEL_DIR`；
`AI_AIRLOCK_MODEL_CACHE` 仅用于模型准备时复用可信本地下载缓存。
`info.json.models` 仍刻意保持空数组：上游 Hugging Face repo 不是可直接运行的最终转换包，当前不会
让 Host 把“下载了源模型”误判成“OpenVINO backend 已就绪”。发布独立、已验证的转换模型仓库后
才能把它登记为 Host-managed model。

这一 challenger 使用 OpenVINO GenAI Tokenizer 进行本地分词、OpenVINO Runtime CPU 执行
embedding IR，再做 attention-mask mean pooling 和 L2 normalization。OpenVINO 只接收已经
完成 Secret/PII 变换和 Prompt Injection 隔离的文本，输出仍必须通过同一个最终泄漏闸门。

Windows 的标准入口会在缺少 `.venv` 时用 Python 3.12 创建隔离环境，安装 `.[openvino]`，准备并验证固定模型，然后才写 ready marker。`--json` 模式会捕获安装/模型准备日志，只保留机器可解析结果或固定错误。正式 Qoder 会话前先在会话外运行一次 `health --json` 完成预热；cold bootstrap 可能联网，warm runtime 的正式分析不联网。

```powershell
.\scripts\run.ps1 health --json
$Target = [IO.Path]::GetFullPath((Join-Path $PWD 'demo\incident'))
.\scripts\run.ps1 analyze `
  --task "Analyze why the payment service failed" `
  --path $Target `
  --relevance-backend openvino `
  --json
```

可用命令仅为 `health`、`scan`、`analyze`。成功结果（包括合法 `decision=BLOCK`）退出码为 `0`；输入、参数、策略或内部安全失败为 `1`；bootstrap/runtime/JSON gate 失败为 `2`；`3` 保留给未来 service/backend transport unavailable。正式 wrapper 只接受 `--json` 模式：非零时 stdout 为空，stderr 为固定且不回显输入内容的错误 JSON；缺少 `--json` 会在运行任何 child/bootstrap 前以固定参数错误退出。

## Capsule 契约

`analyze --json` 的 stdout 只包含一个 JSON 文档。Agent 必须遵守以下边界：

- 下游分析只消费 `safe_context`，不能绕过 Airlock 读取原始文件；
- `safe_context.summary` 在 v0.1 中为 `null`，诊断依据来自带相对路径与 1-based 行号的 `facts`；
- Secret 只能被类型化标签替代，PII 只在单次运行内一致伪名化；映射不会持久化；
- 顶层 `decision`、`risk_level`、计数和指标只用于安全状态展示；
- `BLOCK`、不完整输入、无安全上下文或最终泄漏闸门失败时，不得继续推断原始内容。

启用审计日志时必须把路径放在扫描目录之外：

```bash
python -m airlock.cli analyze \
  --task "Analyze the incident" \
  --path demo/incident \
  --audit-log /tmp/ai-airlock-audit.jsonl \
  --json
```

审计事件只包含版本、时间、计数、决策、模式和耗时，不包含任务、原文、路径或 finding preview。

## 验证

```bash
python -m pip check
python -m pytest
python -m ruff check .
python -m ruff format --check .
python benchmark/run_benchmark.py --compare --output-dir /tmp/airlock-benchmark
git diff --check
git status --porcelain --untracked-files=all
```

Demo 中的 API key、数据库凭证、邮箱、电话和 IP 全部是合成或保留范围数据，不可用于任何真实系统。

## 当前边界

- 正式 Skill 的 `analyze` 路径要求 OpenVINO；只有 `ALLOW`/`ALLOW_WITH_TRANSFORM` Capsule 同时报告 `openvino_available=true` 与 `mode=openvino_embedding` 时才能声称本次运行了模型。合法 `BLOCK` 在 relevance 前终止，不声称 embedding 已运行。
- 当前只处理允许列表内的 UTF-8 文本；不支持 PDF/OCR，不跟随 symlink。
- macOS 已验证 deterministic 安全核心与 Apple Silicon CPU 上的公开 OpenVINO CLI 路径；本仓库尚未在真实 Windows/Intel AI PC 上运行 `scripts/run.ps1`，也尚未完成 Qoder 端到端调用验证。
- `SKILL.md` 与 Qoder 权限设置是行为约束，不是强制沙箱；正式验收必须同时阻止自动索引、附件和 raw 读取旁路。
- 当前 A/B 只覆盖合成 micro-fixture：它能证明公开 CLI、泄漏门和局部相关性指标可测，不能证明跨领域、跨硬件或真实 Agent 的通用 utility retention。OpenVINO 阈值 `0.74` 来自该合成集校准，应在独立 held-out 数据上重新验证。

架构与安全边界见 [docs/architecture.md](docs/architecture.md) 和 [docs/threat-model.md](docs/threat-model.md)。历史设计草案保存在 [PROJECT_SPEC.md](PROJECT_SPEC.md)，不作为当前运行合同。
