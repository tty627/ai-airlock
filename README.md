# AI Airlock

## Your data stays. Your Agent works.

AI Airlock 是面向 AI Agent 的本地上下文网关。它不会把整个私有工作区直接交给远端模型，而是在本机检测敏感数据和 Prompt Injection，将任务真正需要的证据编译成最小、可追溯的 **Safe Context Capsule**。

```text
Private workspace -> deterministic local Airlock -> Safe Context Capsule -> Agent
```

当前版本的**分析运行期**完全离线且无模型：支持文本摄取、Secret/PII 检测、确定性脱敏与伪名化、启发式 Prompt Injection 隔离、任务相关证据选择、策略决策和可选审计日志。首次创建环境并安装 PyYAML 时可能访问 Python 软件源；可在预装依赖的环境中避免联网。

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

Windows 的标准入口会在缺少 `.venv` 时用 Python 3.12 创建隔离环境，并将初始化信息写入 stderr：

```powershell
.\scripts\run.ps1 health --json
.\scripts\run.ps1 analyze `
  --task "Analyze why the payment service failed" `
  --path ".\demo\incident" `
  --json
```

可用命令仅为 `health`、`scan`、`analyze`。成功退出码为 `0`；输入、策略或内部安全失败为 `1`。退出码 `2`、`3` 为后续通信及模型下载阶段保留。

## Capsule 契约

`analyze --json` 的 stdout 只包含一个 JSON 文档。Agent 必须遵守以下边界：

- 下游分析只消费 `safe_context`，不能绕过 Airlock 读取原始文件；
- `safe_context.summary` 在 deterministic v0.1 中为 `null`，诊断依据来自带相对路径与 1-based 行号的 `facts`；
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
pytest
ruff check .
```

Demo 中的 API key、数据库凭证、邮箱、电话和 IP 全部是合成或保留范围数据，不可用于任何真实系统。

## 当前边界

- 尚未接入 OpenVINO、Embedding、LLM、常驻服务或 benchmark；输出会如实标记 `deterministic_rules` 和 `openvino_available: false`。
- 当前只处理允许列表内的 UTF-8 文本；不支持 PDF/OCR，不跟随 symlink。
- macOS 可验证 Python 核心，但本仓库尚未在真实 Windows/Intel AI PC 上运行 `scripts/run.ps1`，也尚未完成 Qoder 端到端调用验证。
- deterministic 证据选择不能替代语义模型；真实 Agent 的 utility retention 必须在后续独立评测中证明。

架构与安全边界见 [docs/architecture.md](docs/architecture.md) 和 [docs/threat-model.md](docs/threat-model.md)。完整原始设计要求保存在 [PROJECT_SPEC.md](PROJECT_SPEC.md)。
