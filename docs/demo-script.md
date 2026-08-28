# AI Airlock 60 秒 Demo Script

> 目标：让评委在 60 秒内看到完整因果链，而不是只看到一次安全扫描。
> 主线：`Private Data → Airlock → Safe + Small Context → Qoder → Task Completed`。

## 拍摄门槛

最终比赛版只有在以下门槛全部通过后才能拍摄：

- **[O] OpenVINO**：Qoder 实际调用的同一条生产路径真实运行 OpenVINO；同一 evidence bundle 包含 model、OpenVINO runtime version、device、mode、参与阶段和本次延迟。不能用另一条终端实验路径代替，`openvino_available` 不得为 `false`。
- **[Q] Qoder**：真实 Windows / Intel 环境中自然语言触发 Skill；只使用 `safe_context`，没有直接读取原目录；最终完成诊断。
- **[B] Benchmark**：与视频完全相同的 task、目录、policy 和最终 commit 已重跑；展示数字来自机器可读结果。
- **[S] Safety**：同一次运行与回归检查没有在规定输出面观察到 ground-truth 敏感值；画面也不展示任何敏感原文。

任一门槛失败，只能拍“当前进展版”，不能用剪辑、静态卡片或后期字幕冒充最终端到端结果。

## 当前可复现的合成 fixture 快照

以下只用于设计画面，最终录制前必须在 release commit 上重新生成。观察命令为：

```bash
.venv/bin/python -m airlock.cli analyze \
  --task '分析支付服务失败原因，并给出修复建议' \
  --path demo/incident \
  --json
```

当时 HEAD 为 `0ae0ae2`，但工作树不是冻结发布态，也没有保存完整 evidence bundle，因此这些数值不可直接进入正式成片。

| 字段 | 2026-08-27 本地复验快照 | 展示边界 |
|---|---:|---|
| Files inspected | 6 | 实际文件名是 `.env.example`，不是 `.env` |
| Risk | HIGH | 来自同一次 JSON |
| API key findings | 3 | 全部为合成 fixture |
| Database credential findings | 1 | 全部为合成 fixture |
| Detector-classified PII-like findings | 248 | 243 email、3 phone、2 IPv4；这是 detector taxonomy，不是法律意义上的 PII 判定 |
| Quarantined instruction spans | 1 | 同一条 span 同时命中 Prompt Injection 和外传意图，不能讲成两次独立攻击 |
| Safe facts | 5 | 带 `source` 与 `local_ref` |
| Ground-truth sensitive markers observed in checked surfaces | 0 | 必须报告 marker 分母与明确输出面，不能外推为全局“零泄漏” |
| Context reduction | `[REAL RESULT REQUIRED]` | 当前单例 token estimator 不是最终 benchmark，不进入正式字幕 |
| OpenVINO | PENDING | 当前输出仍是 `deterministic_rules` |
| Qoder task completion | PENDING | 当前黑盒验收状态仍待真实 Windows/Qoder 执行 |

## 最终比赛版逐秒脚本

### 0–8s：真实问题

**画面**

Windows 文件树快速展开 `demo/incident/`：

```text
.env.example
application.yaml
customers.csv
payment-service.log
production.log
README.md
```

左下角始终保留：`Synthetic incident fixture`。

**旁白**

> 定位支付故障需要本地日志和配置，但同一个目录里还有凭证、客户信息，甚至藏着给 Agent 的恶意指令。

**字幕**

> AI Agent 需要这些数据才能工作，但你敢把整个目录直接交给云端吗？

**证据要求**

- 展示真实目录，不用后期伪造文件名。
- 不打开 `.env.example`、`customers.csv` 或恶意指令原文。

### 8–15s：自然语言触发 Qoder

**画面**

在全新 Qoder 对话中输入：

```text
用 AI Airlock 安全分析 demo/incident，找到支付服务故障根因并给出修复建议。不要把敏感数据暴露到不必要的上下文里。
```

**旁白**

> Qoder 从用户任务开始；在经验证的演示路径中，它先调用本机 Airlock，回答只引用 Capsule。

**证据要求 [Q]**

- 连续录屏自然语言触发，不预先手动运行 CLI。
- Qoder 通过 `scripts/run.ps1` 调用公开入口。
- 轨迹中不得出现对 `demo/incident` 的直接 Read、Grep 或其他绕过访问。

### 15–30s：Local Airlock Preflight

**画面**

由同一次 evidence bundle 生成一张卡片：CLI JSON、独立 output-surface marker 检查与 OpenVINO trace 必须通过 run ID 或 timestamp 关联。

```text
AIRLOCK PREFLIGHT

Files / Risk                    [REAL RESULT REQUIRED]
Credential / PII-like findings [REAL RESULT REQUIRED]
Instruction spans quarantined   [REAL RESULT REQUIRED]
Ground-truth markers observed   [REAL RESULT REQUIRED: 0 / N across named surfaces]
OpenVINO                        [MODEL] · [DEVICE] · [MODE] · [LATENCY]
```

**旁白**

> Airlock 在本机识别并变换敏感内容，把文件里的指令当作不可信数据隔离；OpenVINO 在边界内参与语义相关性判断。

**屏幕角标**

> Local processing · Synthetic fixture · Same-run evidence

**证据要求 [O][S]**

- counts、latency 与输出 hash 必须来自同一次录屏运行；model/revision、OpenVINO runtime 和 device 必须来自同环境证据；所有证据用 run ID 或 timestamp 关联。
- `raw_sensitive_spans_forwarded: 0` 自报字段不能单独作为证据；展示用语必须限定为规定输出面上的 ground-truth marker 检查。
- 不展示任何原始 secret、PII 或被隔离指令，即使它们是合成的。

### 30–42s：从“脱敏整篇”到“编译最小上下文”

**画面 A（前 4 秒）**

```text
Simple Redaction
Whole document with masks ───────────────→ Agent
```

**画面 B（后 8 秒）**

```text
PRIVATE ZONE
Raw Context + Task
        ↓
AI Airlock
Detect → Transform → Isolate → Rank → Minimize → Package
        ↓
Safe Context Capsule
        │  safe facts + source + local_ref
        └────────────────────────────────────────→ Qoder

Context reduced: [REAL RESULT REQUIRED]
```

边界上用醒目文案：

> Only the Safe Context Capsule crosses the Airlock-controlled boundary.

**旁白**

> 在我们定义的 simple-redaction baseline 中，脱敏后仍保留全文结构。Airlock 则在配置预算下选择 task-ranked 证据，并保留来源和行号。

**证据要求 [B]**

- 缩减率必须使用视频同一 task、同一 policy、同一 commit 的结果。
- 同时保留 estimator、样本数和 task success；不得把单一 fixture 写成通用 benchmark。
- 如果 Capsule 在该输入上变大，必须如实展示，不能只挑漂亮任务。

### 42–55s：Agent 真正完成任务

**画面**

从真实 Qoder 最终答案中放大三行，不改写其含义；以下只是预期信息形状，必须用真实输出替换：

```text
EXPECTED OUTPUT SHAPE — REPLACE WITH REAL QODER HIGHLIGHTS

ROOT CAUSE  [REAL RESULT REQUIRED]
FIX         [REAL RESULT REQUIRED]
EVIDENCE    [REAL RESULT REQUIRED: source + local_ref]
```

预期验收内容是：Redis pool 达到 100/100，acquire timeout 与密集重试放大争用形成 retry storm；建议应覆盖退避/抖动、熔断或 load shedding、连接释放审计和负载测试后的容量调整。该预期来自现有 Capsule 证据，不是 Qoder 已生成结果。

**旁白**

> Qoder 仅凭 Capsule 定位了连接池耗尽与重试风暴，并给出退避、熔断、连接释放审计和容量验证建议。

**证据要求 [Q]**

- 结论必须由 Qoder 在真实会话中生成，不是预先写好的静态卡片。
- 引用必须对应本次 Capsule 的 `source` 与 `local_ref`。
- “Task Completed” 只表示完成诊断和建议，不暗示已经修改或部署生产系统。

### 55–60s：End Card

**画面与旁白**

```text
AI AIRLOCK

Your data stays.
Your Agent works.

OpenVINO × Local AI × Hybrid Agent
```

**最终小字**

> Synthetic workflow · Measured results and limitations in the article

`OpenVINO × Local AI × Hybrid Agent` 只有在 [O]、[Q]、[B]、[S] 四门全部通过后才可出现；否则删掉，改成：

```text
Local processing × Safe Context Capsule
```

## 60 秒总览

| 时间 | 评委此时必须明白什么 | 核心视觉 |
|---|---|---|
| 0–8s | 问题真实：工作所需目录同时含隐私与恶意内容 | 私有事故目录 |
| 8–15s | Agent 发起真实任务 | Qoder 自然语言输入 |
| 15–30s | 决定什么能离开本机的步骤发生在本地 | Preflight + OpenVINO trace |
| 30–42s | Airlock 不是普通脱敏器，而是按任务编译 Capsule | 边界架构 + 真实指标 |
| 42–55s | Agent 不是只看安全报告，而是完成诊断 | 根因、建议、Capsule 引用 |
| 55–60s | 记住产品名与价值 | End Card |

## 当前可诚实拍摄的进展版

在 OpenVINO 或 Qoder 尚未验收时，只能作以下替换：

| 最终版镜头 | 当前进展版替换 | 禁止表述 |
|---|---|---|
| Qoder 自然语言触发 | 直接展示公开 CLI，并标 `CLI rehearsal · Qoder acceptance pending` | “Qoder 已集成” |
| OpenVINO model/device | 显示真实 `deterministic_rules` 与 `OpenVINO pending` | “OpenVINO accelerated” |
| Qoder 最终回答 | 展示 Capsule 保留了根因证据，并写 `Agent task completion pending` | “Agent 已完成任务” |
| Hybrid Agent End Card | `Local processing × Safe Context Capsule` | `OpenVINO × Local AI × Hybrid Agent` |
| Context benchmark | `[REAL RESULT REQUIRED]` 或明确标注“single synthetic run estimate” | 无范围的通用缩减结论 |

## 拍摄与证据 Runbook

### 拍摄前

1. 冻结 release commit；记录完整 SHA，确认工作树与发布包一致。
2. 在真实 Windows / Intel AI PC 上记录 OS、CPU/GPU/NPU、OpenVINO、模型、Qoder 和 Python 版本。
3. 先完成环境安装；60 秒成片使用 warm run，并在文章中另报 cold start。
4. 使用与成片完全相同的 task、path、policy 跑 benchmark 和 Qoder acceptance。
5. 清空 Qoder 对话；开启能审计 tool call 的录制视图。
6. 准备一段不剪切的完整验收录像；60 秒视频只做其故事剪辑。

### 拍摄中

1. 从 Qoder 输入开始连续录到最终答案，保留原始时间线。
2. Preflight 卡片必须从同一次 evidence bundle 派生，并明确区分 CLI 自报字段、独立 marker 检查和 OpenVINO trace；不得手工重打计数。
3. 只展示类型、计数、decision、Capsule facts 和 provenance，不展示原始敏感值。
4. 显示 OpenVINO mode/model/device 的真实 trace。
5. 显示 Qoder 没有直接读取原工作区的轨迹证据。

### 拍摄后

1. 保存未剪辑原片、60 秒成片、同次运行 JSON、benchmark 结果和 Qoder 验收记录。
2. 记录每个画面数字对应的结果文件、JSON path、commit 和命令。
3. 扫描字幕、终端、窗口标题、绝对路径、用户名和通知，避免真实 PII 泄漏。
4. 无登录窗口复查视频、GIF、文章与 Skill 链接。

## 一票否决式剪辑错误

- 文件树写 `.env`，但实际仓库只有 `.env.example`。
- 把同一隔离 span 的 Prompt Injection 与外传命中讲成两次攻击。
- 把自报的 `raw_sensitive_spans_forwarded: 0` 当作独立、全面的零泄漏证明。
- 把 UTF-8 bytes/4 估算称为真实模型 tokenizer 数字。
- 把单次 fixture 缩减率称为 benchmark 总结论。
- 把 benchmark runner 的总体 `PASS` 称为 Agent 任务完成或安全质量通过。
- 健康检查显示 `openvino_available: false`，End Card 却写 OpenVINO。
- Qoder 在 Airlock 后又直接读取原文件。
- 把“给出修复建议”讲成“已修复生产事故”。
- 视频或截图中出现真实 secret、PII、个人绝对路径或可用 endpoint。
