# AI Airlock Submission Readiness Checklist

> 本清单以“可提交、可复现、可追溯”为完成标准，不以“文件存在”为完成标准。
> 官方要求最后核对：2026-08-27，Asia/Shanghai；仓库与 release evidence 状态须按对应 RC SHA 刷新。

## 当前结论

**当前状态：NO-GO。**

确定性本地 MVP 已能生成 Safe Context Capsule，但 Competition Story 的两个关键承诺仍缺真实闭环：

1. OpenVINO 已在 macOS 公开 CLI 中实际参与本地语义排序，但尚未进入正式 Qoder/Windows 路径，
   也没有 release-frozen evidence bundle；
2. Qoder 还没有被证明只靠 Capsule 完成任务且不绕过 Airlock。

在这两项完成前，继续写更强的营销文案不会提高提交可信度。

## 官方要求快照

2026-08-27 实时核对 [Production AI Skills 大赛官方页](https://www.modelscope.cn/events/289/summary) 得到：

- 官方来源当前出现冲突：登录态活动页实时界面显示**报名截止**为 **2026-08-31 23:59**，搜索/抓取摘要曾显示 **15:59**。两者都不能证明作品提交截止；必须向组织方或真实表单确认报名、作品提交与修改锁定三个时刻，并在确认前按更早的 15:59 管理风险。
- 作品应面向 Qoder、WorkBuddy、TRAE Work 等生产力级 Agent，稳定调用一项本地 AI 工具。
- Skill 涉及的 AI 模型必须支持 Localhost 纯本地运行。
- Client/Server 模型服务是官方推荐部署方式，不是页面文字中的唯一强制方式；当前实现若仍是单进程，必须如实说明并用启动延迟、稳定性与 fallback 证明其可用性。
- OpenVINO / Optimum-intel 是官方推荐的推理框架，不是页面文字中的强制唯一框架；但 AI Airlock 已把 OpenVINO 写进核心比赛故事，因此它是本项目自己的提交门槛。
- 生产力 Agent 工具必须作为 Skill 稳定调用的基准测试环境。
- 作品包需发布到 ModelScope Skills，添加 `AI PC` 自定义标签，并包含代码、文档与测试用例。
- 技术文章需发布到魔搭研习社，添加 `Intel AI PC` 专题标签，并包含在生产力 Agent 中跑通 Skill 的完整截图/录屏、优化心得与 Hybrid AI 思考。
- 评分：场景价值 30%、商用生产力 30%、工具使用 20%、文章质量 10%、创新性 10%；另有传播附加分 5%。

当前账号没有进入可见的作品提交表单，因此**精确表单字段尚未验证**。本清单不会猜测必填项；正式提交前必须打开实际表单逐项抄录、填写并复核。

在官方确认作品提交截止后，应设置至少提前一天的内部截止，为链接、权限、转码和表单问题留出缓冲。

## 当前仓库快照

该表区分源码能力与比赛实机门槛；可复现性状态必须读取对应 RC SHA 的 checkout 外 release evidence，
不得从旧的 dirty-tree 或 `latest.*` 报告推断。

| 项目 | 当前状态 | 判断 |
|---|---|---|
| Python core / CLI | 已存在 | 能证明 deterministic local compiler，不等于 Local AI 已完成 |
| Opt-in OpenVINO challenger | macOS 公开 CLI 已实跑 | model/device/mode/chunks 可见；source RC 是否 clean-reproduced 以对应外置 evidence 为准，Qoder/Windows 仍缺 |
| Formal Qoder → OpenVINO path | 代码已连通，实机未验收 | Skill 命令已显式选择 OpenVINO，wrapper 会准备固定模型并 fail closed；仍缺真实 Windows/Qoder Agent 路径证据 |
| `SKILL.md` | 已存在 | 有 Capsule-only contract；真实 Qoder trigger 仍待验收 |
| `scripts/run.ps1` | 已存在 | 尚缺真实 Windows / Intel 干净机证据 |
| README / requirements / policy / audit / schema | 已存在 | README Hero 仍缺真实架构图与 Demo 资产 |
| Cross-doc status | 已区分实现与验收 | architecture/threat model 已区分 opt-in challenger 与尚未完成的 Windows/Qoder 验收 |
| Decision contract | 已注明保留态 | `REQUIRE_CONFIRMATION` 在 SKILL/Qoder 文档中标为 v0.1 reserved/unreachable |
| Unit / integration tests | 本地可运行 | source RC 必须从 clean checkout 重跑；远端 CI 状态单独记录 |
| Black-box benchmark | rules/OpenVINO full A/B 可运行 | source RC 的冻结结果读取外置 evidence；总体 `PASS` 仍不代表 Agent Task Success |
| OpenVINO A/B | 本地 synthetic A/B 已测 | 正式 Qoder/Windows、held-out 稳健性与 frozen evidence 仍是提交门槛 |
| Evidence identity | runner 已记录 provenance | 正式报告必须在 checkout 外保存、共享 run ID、Git/环境/输入 hash，并绑定同一个 clean source RC SHA |
| Qoder acceptance | `PENDING_REAL_QODER_WINDOWS` | 提交阻断项 |
| Visual assets | 未见正式架构图、GIF、截图或视频 | 提交阻断项 |
| Competition story / demo / checklist | 已形成独立草案 | 待 Integrator 与最终证据同步 |
| ModelScope Skill / article / submission | 未见发布证据 | 提交阻断项 |

审校期间的未冻结运行曾暴露低 injection recall；本轮已将新失败样本加入回归并增加预注册质量门，
但 25 个合成样本的满分仍不能外推为普适防护。跨语言 relevance 压力测试仍不稳定，小文本集合上
Capsule 元数据也可能造成上下文膨胀。`latest.*` 会被后续运行覆盖，最终文章只能从带 run ID、
scope、commit 和完整性记录的冻结结果读取准确数字，不能只截取旗舰单例的漂亮比例，也不能把
总体 `PASS` 写成 Agent Task Success 或通用安全保证。

## GO / NO-GO 硬门

任何一项为否，最终提交状态保持 NO-GO：

- [ ] **G1 · Local boundary**：Airlock 控制路径不主动上传原始文件，运行期网络行为和首次安装网络行为已分别说明。
- [ ] **G2 · OpenVINO**：真实模型推理、device、mode、版本、阶段与 A/B 可追溯；不是 import/health-only。
- [ ] **G3 · Qoder**：真实自然语言触发、Capsule-only、零 workspace bypass、Agent 完成诊断。
- [ ] **G4 · Reproducible evidence**：最终 commit、数据集、命令、环境、结果文件与所有数字一一对应。
- [ ] **G5 · Safe publication**：代码、结果、截图、视频、文章与发布包中无真实 secret / PII / 私人路径。
- [ ] **G6 · Delivery**：Skill、文章与 Demo 可由未登录访问；比赛 submission 保存明确的成功状态、作品 ID、时间戳或组织方确认，不要求登录态回执本身公开。

## 1. Code 与发布包

- [ ] 冻结 release commit，记录完整 SHA、tag 和工作树状态。
- [ ] 确认代码目录与 ModelScope 发布包完全一致，不从另一个未记录工作树打包。
- [ ] `src/airlock/` 中不存在临时代码、debug 输出、硬编码本机路径或真实 endpoint。
- [ ] `SKILL.md`、`scripts/run.ps1`、`README.md`、`requirements.txt`、`info.json`、`meta.json`、配置、测试与 benchmark 全部进入版本控制。
- [ ] 不把 `.venv/`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/`、本机日志或临时结果打进发布包。
- [ ] 补齐并核对项目 LICENSE、第三方依赖许可证、模型许可证、模型来源与允许的分发方式。
- [ ] 所有默认路径为项目相对路径；Windows、中文路径和带空格路径至少各有一次实测。
- [ ] 所有 stdout/stderr/exit code 与公开 JSON schema 和 README 一致。
- [ ] backend 选择与失败行为可观察且 fail-closed；不得静默从 OpenVINO 降级后仍伪装成 OpenVINO 成功。
- [ ] 不声称未实现的 server、policy state、模型或 detector 能力。

## 2. `SKILL.md` 与 Agent 契约

- [ ] frontmatter 的 `name`、`description` 与发布信息一致；若存在 `version` 字段，再与 `info.json`、`meta.json` 和 release tag 对齐。
- [ ] 中英文触发语义覆盖“私有日志分析”“安全上下文”“Prompt Injection 检查”“Safe Context Capsule”。
- [ ] 明确规定下游只能消费 `safe_context`，不能直接读取原始目录作为 fallback。
- [ ] 明确 `ALLOW`、`ALLOW_WITH_TRANSFORM`、`BLOCK` 和任何实际支持的 decision 行为；不描述仅存在于枚举、未实现的状态。
- [ ] 明确失败条件：无效 JSON、非零退出、输入不完整、无安全上下文，以及 OpenVINO 不可用时的真实 fail-closed 行为或用户显式选择的 rules-only baseline。
- [ ] Agent 的最终答案保留 Capsule `source` 与 `local_ref` 引用。
- [ ] 真实 Qoder 安装/发现 Skill 的步骤已在干净环境复现。
- [ ] 公开入口只有文档约定的单一调用方式；无隐藏手工步骤。
- [ ] 任何 “Skill validator passed” 主张都有 validator 名称、版本、完整命令与结果工件；否则降级为静态人工审查。

## 3. `run.ps1`、本地运行与 OpenVINO

- [ ] 在真实 Windows / Intel AI PC 的干净用户环境运行 `scripts/run.ps1 health --json`。
- [ ] 首次安装、模型下载、warm run 三种状态分别录制和计时。
- [ ] 明确首次安装是否访问软件源；“运行期本地”不被写成“安装全过程绝不联网”。
- [ ] 推理在本地进程完成；若使用模型服务，只绑定 localhost；断网 warm-run 成功。
- [ ] 结构化输出包含真实 model id/revision、mode 和实际参与阶段；同一 evidence bundle 另含 OpenVINO runtime version、device 与本次 latency。当前 metadata 不足的字段必须由受控外部 trace 补齐或在实现中增加。
- [ ] CPU/GPU/NPU 选择与失败行为真实可观察；不把自动设备名当成实际 NPU 使用证明。
- [ ] 模型下载可恢复、校验完整性并有清晰错误码。
- [ ] 记录 cold start、warm p50/p95、总调用数、错误数与超时数。
- [ ] OpenVINO 路径仍经过 deterministic transform 与最终 leak guard。
- [ ] `rules-only` 与 `OpenVINO` 通过同一公开契约可选择、可复现、可归因。
- [ ] 正式 Qoder wrapper 已显式选择 OpenVINO backend；仍需同一真实 Windows/Qoder tool trace 证明 OpenVINO 实际参与且无 raw bypass。
- [ ] Qoder 实际运行环境具备全部 OpenVINO 依赖和模型；基础包安装成功不能替代可选推理依赖验收。
- [ ] `health` 与 `analyze` 解析同一个模型目录；若 runner 先用 `health` 判定 availability，模型路径必须通过二者共享的配置（如 variant environment）提供，不能只给 `analyze --model-dir`。

## 4. Tests 与 CI

- [ ] 最终 release SHA 执行 `pytest`，记录 passed/failed/skipped 和耗时。
- [ ] 执行 `ruff check .`，结果为零错误。
- [ ] CI 在远端 release commit 上完成，不用本机通过替代远端证据。
- [ ] `python benchmark/run_benchmark.py --smoke` 在 CI 和 Windows 本地均通过。
- [ ] 安全回归覆盖 stdout、stderr、Capsule、audit、受控异常和生成报告。
- [ ] 测试不只断言自报的 `raw_sensitive_spans_forwarded: 0`，还搜索 ground-truth marker。
- [ ] symlink、路径越界、畸形编码、输入上限、敏感文件名与任务中 secret 有回归测试。
- [ ] Qoder 正负触发用例在全新会话中执行，避免上下文污染。
- [ ] 测试结果文件不含原始 secret sentinel、PII 或被隔离指令原文。

最终签字栏：

```text
Commit:                 [REAL RESULT REQUIRED]
pytest:                 [REAL RESULT REQUIRED: valid / passed / failed / skipped]
ruff:                   [REAL RESULT REQUIRED]
CI run URL:             [REAL RESULT REQUIRED]
Windows smoke evidence: [REAL RESULT REQUIRED]
```

## 5. Benchmark 与真实结果

- [ ] 数据集版本、生成方式、人工标签、样本量、split 和去重规则已冻结。
- [ ] 预注册指标和阈值，不在看到结果后只挑好看的指标。
- [ ] 至少比较 `rules-only` 与 `OpenVINO`；如时间允许，再加入 raw-context 与 simple-redaction 作为披露基线。
- [ ] Injection 报 TP/FP/TN/FN、Precision、Recall 和失败案例，不只报“检测到”。
- [ ] Relevance 报 Recall@K、Precision@K、MRR、跨语言指标和空结果。
- [ ] Privacy 明确 ground-truth 单位是 span、unique marker 还是 unique value，并报告相同单位的分母、观察泄漏数、检查输出面和漏检边界；不得混称。
- [ ] Context 报真实字符数、明确 estimator/tokenizer、Capsule 元数据开销和负缩减案例。
- [ ] Utility 报 **Capsule-only Agent Task Success**，不能用“3/3 预设事实存在”替代 Agent 完成任务。
- [ ] Performance 报硬件、OS、模型、OpenVINO、冷/热状态、调用数、失败数、p50/p95。
- [ ] 每个表格数字能回溯到机器可读结果 JSON 的准确 JSON path。
- [ ] 结果文件由最终 release commit 重跑生成，并保存 SHA-256 或等价完整性记录。
- [ ] JSON 与 Markdown 报告具有相同 run ID、scope、commit、生成时间和结果摘要，不存在 stale `latest.*`。
- [ ] 建立 evidence manifest，记录结果 JSON、未剪辑录像、60 秒成片、截图与文章源文件的 SHA-256。
- [ ] 文章明确总体 `PASS` 的实际 acceptance gate，不把“完成测量”误写成“质量达标”。

文章结果占位：

```text
[REAL RESULT REQUIRED: n / repeats / failures]
[REAL RESULT REQUIRED: Capsule-only Agent Task Success]
[REAL RESULT REQUIRED: observed sensitive leakage / denominator / surfaces]
[REAL RESULT REQUIRED: context reduction at fixed utility]
[REAL RESULT REQUIRED: rules-only vs OpenVINO uplift]
[REAL RESULT REQUIRED: cold / warm p50 / p95 on Intel device]
```

## 6. Qoder 黑盒验收

以 [`docs/qoder_acceptance.md`](qoder_acceptance.md) 为准：

- [ ] 当前验收矩阵中的 12/12 Positive triggers 全部正确触发公开入口；release freeze 时重新统计总数。
- [ ] 当前验收矩阵中的 10/10 Negative triggers 全部不误触发；release freeze 时重新统计总数。
- [ ] 每条用例使用全新对话并记录原始输入、tool trace、stdout/decision 和最终答案。
- [ ] `ALLOW_WITH_TRANSFORM` 后 Qoder 只使用 `safe_context`。
- [ ] workspace bypass 次数为 0。
- [ ] 观察到的 ground-truth 敏感值泄漏次数为 0。
- [ ] `BLOCK` 后 Qoder 停止，不继续推断或外传。
- [ ] 旗舰案例最终答案定位 Redis pool exhaustion、retry storm 与 timeout，并给出建议。
- [ ] 最终答案引用实际 Capsule `source/local_ref`。
- [ ] 截图或录像能看出是 Qoder 真实界面、真实 Skill 调用和真实最终答案。
- [ ] 保存一次未经剪辑的完整验收录像，60 秒成片可回溯到它。

验收摘要：

```text
Environment / versions: [REAL RESULT REQUIRED]
Positive triggers:      [REAL RESULT REQUIRED]
Negative triggers:      [REAL RESULT REQUIRED]
Workspace bypasses:     [REAL RESULT REQUIRED]
Observed leaks:         [REAL RESULT REQUIRED]
Task completions:       [REAL RESULT REQUIRED]
Evidence directory:     [REAL RESULT REQUIRED]
```

## 7. README 与架构图

- [ ] README 首屏顺序为：项目名 → 一句话 → Demo → 架构图 → Why Airlock → Quick Start。
- [ ] 使用 `Your data stays. Your Agent works.` 和 Context Compiler 定位，不回退成 scanner 叙事。
- [ ] 核心架构图明确区分 `PRIVATE ZONE` 与 `AGENT ZONE`。
- [ ] 只有 Safe Context Capsule 跨越 Airlock 控制边界。
- [ ] 图中顺序与真实实现一致；当前单进程实现不冒充 client/server。
- [ ] OpenVINO 节点只在真实接入后移除 `PENDING` 标记。
- [ ] Qoder 箭头最终落到 `Task Completed`，并有真实视频证据。
- [ ] README 的 Demo GIF、架构图、文章和 Skill 链接全部真实存在。
- [ ] Quick Start 在干净 clone 中逐字执行通过。
- [ ] Current limitations 明写未知 Secret、规避式 injection、PDF/OCR、Host bypass 和 benchmark 范围。

README Hero 草案与架构图信息设计见 [`docs/competition-story.md`](competition-story.md)。

## 8. 60 秒 Demo 与截图

- [ ] 完整结构为 0–8s 问题、8–15s Qoder、15–30s Preflight、30–42s Capsule、42–55s Task Completed、55–60s End Card。
- [ ] 文件树使用真实 `.env.example`，并标注 synthetic fixture。
- [ ] Preflight 数字由同一次 evidence bundle 派生，并明确区分 CLI 自报字段、独立 marker 检查和 OpenVINO trace。
- [ ] 不展示 raw secret、PII 或恶意指令原文。
- [ ] OpenVINO mode/model/device/latency 为真实 trace。
- [ ] Context reduction 来自视频同一 task、policy 和 commit。
- [ ] Qoder 最终答案只引用 Capsule facts。
- [ ] 字幕明确“完成诊断与建议”，不暗示已部署修复。
- [ ] End Card 只有在 OpenVINO、Qoder、benchmark 追溯和 safety 四门全部通过后才出现 `OpenVINO × Local AI × Hybrid Agent`。
- [ ] 另存未经剪辑的原始录像、同次 JSON、结果文件和最终成片。
- [ ] 输出 16:9 主视频、README GIF/静态封面和文章关键截图。
- [ ] 视频在无声状态下仍可理解，配音与字幕也没有数值冲突。
- [ ] 核对实际时长、容器/codec、分辨率、字幕安全区，并在目标平台转码后完整回放。

完整脚本见 [`docs/demo-script.md`](demo-script.md)。

## 9. 比赛文章

- [ ] 文章标题不含未验证数字或未完成技术。
- [ ] 先讲真实生产矛盾，再讲架构，不从安装步骤开场。
- [ ] 对比 Fully Cloud、Fully Local、Simple Redaction，解释适用条件与局限。
- [ ] 解释 Safe Context Capsule、Prompt Injection isolation 与 task-conditioned minimization。
- [ ] OpenVINO 章节包含真实角色、模型、设备、A/B 和 fallback。
- [ ] Qoder 章节包含连续截图/录屏与 Capsule-only 证据。
- [ ] Benchmark 章节包含方法、数据、阈值、失败案例和可复现命令。
- [ ] Real Results 从机器可读结果生成；不手填漂亮数字。
- [ ] Limitations 正面呈现负结果、Host bypass 和合成数据边界。
- [ ] Future 只讲 selective disclosure 等未来方向，不混入当前完成态。
- [ ] 添加 `Intel AI PC` 专题标签。
- [ ] 所有外部依赖、模型、数据集、图标、音乐、字体、录像素材和 AI 生成资产来源正确署名。
- [ ] 文章中的每张图、每个表和每条 claim 都有证据来源。

文章十二节骨架见 [`docs/competition-story.md`](competition-story.md)。

## 10. ModelScope Skill 发布

- [ ] 发布包包含代码、文档和测试用例。
- [ ] 添加 `AI PC` 自定义标签。
- [ ] Skill 名称、版本、描述、封面和 README 与 release 一致。
- [ ] 安装与调用命令在公开页面可复制。
- [ ] 公开页面没有失效的相对链接或本机绝对路径。
- [ ] 公开页面可由未登录访问，并从发布产物在干净环境完成安装与一次真实调用。
- [ ] 保存公开 Skill URL、发布时间、版本与页面截图。
- [ ] 发布后不要再用未记录的内容热修；若修改，更新版本和证据。

## 11. Competition Submission Fields

已由官方页面确认的交付物：

- [ ] ModelScope Skill 公开链接，含 `AI PC` 标签。
- [ ] 魔搭研习社文章公开链接，含 `Intel AI PC` 专题标签。
- [ ] 文章内有生产力 Agent 跑通 Skill 的完整截图/录屏。
- [ ] 代码、文档和测试可访问。

为表单预先准备、但**尚未确认是否为必填字段**的材料：

- [ ] 作品标题。
- [ ] 一句话定位与短简介。
- [ ] Skill URL。
- [ ] 文章 URL。
- [ ] 代码仓库 URL。
- [ ] 60 秒 Demo URL / 封面图。
- [ ] 团队与联系信息。
- [ ] 技术栈、OpenVINO 模型和设备摘要。

表单现场核对：

- [ ] 登录比赛页并打开真实“提交作品”表单。
- [ ] 将所有必填字段、字数限制、文件格式和 URL 校验规则逐项记录到本节。
- [ ] 两人复核标题、简介、链接、标签、团队信息与授权声明。
- [ ] 提交前在未登录窗口测试全部公开 URL。
- [ ] 正式提交后保存明确的成功提示、作品状态、作品 ID、时间戳、作品页 URL 或组织方确认。
- [ ] “我的队伍/成绩”只作辅助截图，不作为系统已接收最终版本的唯一证据。

## 12. Numerical Claims Ledger

任何数字进入 README、视频、图片、文章或表单前，都必须登记：

| Claim ID | 对外文案 | 数据集 / n / repeats | 指标定义 | 命令 | 结果文件 + JSON path | Commit | 环境 / 设备 | 审核人 |
|---|---|---|---|---|---|---|---|---|
| `[ID]` | `[TEXT]` | `[REAL RESULT REQUIRED]` | `[DEFINITION]` | `[COMMAND]` | `[PATH#JSON_PATH]` | `[SHA]` | `[ENV]` | `[SIGN-OFF]` |

检查：

- [ ] 分子、分母、失败数、无效数与置信区间/重复波动在适用时一并报告。
- [ ] 单次 fixture 结果明确写 `single synthetic run`。
- [ ] estimator 与真实 tokenizer 严格区分。
- [ ] `0` 与 `100%` 均有分母和检查范围。
- [ ] A/B 使用同一数据、阈值、环境和任务，不混用不同 run。
- [ ] 图表由结果文件生成或逐项交叉核对，不凭记忆抄数。
- [ ] 任何无法追溯的数字从提交物删除。

## 13. Claims 与安全发布

发布前逐项确认所有提交物均不含：

- [ ] 已确认不含 `100% secure`。
- [ ] 已确认不含 `prevents all prompt injection`。
- [ ] 已确认不含 `zero risk`。
- [ ] 已确认不含 `enterprise compliant`。
- [ ] 已确认不含 `GDPR compliant`。
- [ ] 已确认不含未验收的 `OpenVINO-powered`、`Qoder integration completed` 或 `semantic minimization`。
- [ ] 已确认不含无范围的“原始数据绝不会出机”。

以下措辞若被使用，已附明确范围与证据：

- [ ] `In our tested workflow...`
- [ ] `Measured on [dataset/version/commit/device]...`
- [ ] `Raw source files are processed locally by Airlock.`
- [ ] `Only the Safe Context Capsule is intended for downstream Agent use.`
- [ ] `No ground-truth marker was observed in [explicit output surfaces]...`
- [ ] `OpenVINO comparison not available.` / `Qoder integration pending acceptance.`

安全扫描：

- [ ] 代码、git history、结果 JSON、Markdown、图片 OCR、视频字幕和终端画面均扫描真实 secret / PII。
- [ ] 不出现用户名、私人绝对路径、通知内容、浏览器账号、可用 endpoint 或真实组织信息。
- [ ] 合成 secret 明确标注 synthetic / reserved，且不能命中真实服务。
- [ ] Prompt Injection 原文不进入公开证据；只展示类型、计数和隔离状态。
- [ ] 审计日志、错误信息和 benchmark 报告不回显任务中的 secret。

## 14. 最终 30 分钟复核

- [ ] release commit/tag 未变化；结果与视频仍对应同一 SHA。
- [ ] GitHub/ModelScope CI 为绿；无 pending 或被取消的必要 job。
- [ ] README Hero、GIF、架构图、Quick Start 在公开页面正确渲染。
- [ ] 60 秒 Demo 能在无声状态下讲清问题、本地边界、差异、OpenVINO 和任务完成。
- [ ] 文章数字与 Numerical Claims Ledger 一致。
- [ ] README、SKILL、benchmark 文档、示例命令、CLI flags、schema 和 limitations 的状态表述一致。
- [ ] Skill、文章、代码、视频均可未登录访问。
- [ ] 比赛表单字段和 URL 完成双人复核。
- [ ] 保存提交成功回执与作品公开页。
- [ ] 记录提交时间，并再次核对官方截止时间。

## 15. 可选传播附加分

若决定争取官方 5% 传播附加分：

- [ ] 在小红书发布作品架构图、流程图或 Skill 成果，并附魔搭研习社文章链接和 Skill 链接。
- [ ] 正确 @ `OpenVINO中文社区` 与 `魔搭ModelScope社区`。
- [ ] 添加 `#英特尔`、`#openvino`、`#魔搭`、`#agentic`、`#skills`。
- [ ] 保存发布时间、公开 URL、未登录截图和阅读量证据。
- [ ] 当前官方口径为截至 8 月 31 日，研习社文章、Skills 与小红书累计阅读量超过 1000 次可得 5 分；只有达到并留存证据时才申报，不得估算或提前宣称。
- [ ] 再次核对官方页面对统计截止时间与累计范围的最新说明。

传播是可选项，不能挤占 OpenVINO、Qoder、benchmark 与安全发布的硬门时间。

## 若时间不足，优先级

1. **先补 OpenVINO 真实核心路径与 A/B。** 这是“Local AI”与“不是 scanner”的最短证明。
2. **再补 Qoder Capsule-only Task Completed。** 没有它，故事会停在“生成了一个 JSON”。
3. **冻结 benchmark 与数值追溯。** 正面和负面结果都要可复现。
4. **最后制作架构图、60 秒成片、README Hero 与文章。** 视觉资产必须建立在前三项事实之上。

不要用时间换取未经验证的安全或合规主张。
