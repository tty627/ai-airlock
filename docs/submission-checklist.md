# AI Airlock Submission Readiness Checklist

当前状态入口为 [`../STATUS.md`](../STATUS.md)。Windows 执行顺序与报告格式分别见
[Windows validation handoff](windows-validation-handoff.md) 和
[Windows validation report template](windows-validation-report-template.md)。

> 包装基线：`v0.1.0-rc.1` · `495f89c6349afbdd741576439b3b85369d26671a`
> 公开 `tty627/ai-airlock` 使用 Apache-2.0、署名“谭天晔”；annotated、unsigned、按流程不可变的
> `v0.1.0-rc.6` 候选已发布。既有 rc.1–rc.5 不移动；ModelScope Skill、文章、比赛作品与新的
> 不可变 GitHub tag/release 已获授权，社交媒体发布未授权。

## 当前结论

技术 RC 已具备 SHA 绑定的 macOS / Apple M4 / OpenVINO release evidence，rc.6 精确身份、Windows/Ubuntu
Python 3.12 CI、干净归档安装和 Intel CPU wrapper evidence 也已固化。exact rc.3 的正式 Windows cold
health `FAIL` 历史保持不变。
rc.4 fresh-tag Windows regression subset 曾通过，但随后精确 rc.4 的 orphan-pipe fault oracle 发现 wrapper
返回时仍有 `1` 个匹配后代进程存活，外部定向清理后才降为 `0`；因此 Windows candidate verdict 与 overall
均为 `FAIL`。exact rc.5 已通过 PowerShell 5.1/7 orphan-pipe no-residual-process oracles，以及两壳 scoped
health/analyze controls。source-artifact cache 预填、网络 `NOT_MEASURED`、其余 timeout/fault cases
`NOT_RUN` 与 Qoder host evidence unavailable/`NOT_RUN` 仍是独立缺口，因此完整 host acceptance 仍为
`INCONCLUSIVE`。exact rc.6 在 Intel Core i7-14700KF 上的七次 warm OpenVINO wrapper sample 为
`7/7` contract-valid，P50 `5021.900 ms`、P95 `5193.160 ms`；不包含 NPU/GPU 或 TraeCode host 声明。

```text
RC.1 CLEAN CHECKOUT                 PASS / HISTORICAL
RC.6 SOURCE CANDIDATE               PUBLISHED / ANNOTATED UNSIGNED
MAC OPENVINO CLI + A/B              PASS
PYTHON QODER STRICT RESPONSE GATE   PASS
WINDOWS POWERSHELL                  RC.3 FAIL / RC.4 EARLIER SUBSET PASS / ORPHAN FAULT FAIL
RC.4 CANDIDATE / OVERALL            FAIL
RC.5 WINDOWS SCOPED VALIDATION      PASS_WITH_SCOPE
RC.5 FULL MATRIX / OVERALL          INCONCLUSIVE
TRAE/QODER HOST CAPSULE-ONLY        NOT RUN
INTEL CPU WARM WRAPPER SAMPLE       PASS_WITH_SCOPE / 7 OF 7
RC.3 PRE-CANDIDATE PYTHON CI        PASS / WINDOWS + UBUNTU / HISTORICAL
EXACT RC.3 MAIN/TAG CI              PASS / WINDOWS + UBUNTU (HISTORICAL)
EXACT RC.4 MAIN/TAG CI              PASS / WINDOWS + UBUNTU / SCOPED PYTHON CI
EXACT RC.5 MAIN/TAG CI              PASS / WINDOWS + UBUNTU / SCOPED PYTHON CI
EXACT RC.6 MAIN/TAG CI              PASS / WINDOWS + UBUNTU
GITHUB SOURCE                       PUBLIC / AUTHORIZED
MODELSCOPE SKILL FORM               AUTHENTICATED / PREFILLED / FILE UPLOAD PENDING
ARTICLE / COMPETITION SUBMISSION    AUTHORIZED / PENDING
```

包装 readiness flag 已在本文末尾根据本地 QA 回填；它们不代表最终比赛提交 ready。

## 不可变事实

- [x] tag `v0.1.0-rc.1` 直接指向 source commit
  `495f89c6349afbdd741576439b3b85369d26671a`。
- [x] source tree 为 `4fe991ded88f38a6c1952c506d20005d2956a915`。
- [x] 外置 evidence 目录为
  `.release-evidence/495f89c6349afbdd741576439b3b85369d26671a/`。
- [x] `SHA256SUMS` 中 manifest、benchmark JSON、benchmark Markdown 三项均校验通过。
- [x] full pytest 为 `212 passed / 6 skipped`；6 项均因 PowerShell unavailable。
- [x] macOS 26.5.2 / Apple M4 / OpenVINO CPU 的公开 CLI、flagship 与 full A/B 已实跑。
- [x] Python Qoder strict response gate 已通过；这不是实际 Qoder host 或 Windows wrapper E2E。
- [x] benchmark 是 synthetic fixtures；不能外推为通用安全保证。
- [x] 当前 qoder acceptance 定义 **12 positive + 12 negative** triggers；两组均
  `0/12 REAL_QODER_EXECUTED`。
- [x] exact rc.3 保持不可变；正式 Windows verdict 为 `FAIL`。PowerShell 5.1/7 cold health 均返回固定
  错误 `AIRLOCK_MODEL_PREPARATION_FAILED`；Qoder 为 `NOT_RUN`。
- [x] exact rc.4 为 annotated、unsigned tag object
  `2a50625aa95443e328573704cf42e9c633621ffe`，commit
  `52a215727115f32937cb78561e88a63fdae5adf2`，tree
  `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`。
- [x] rc.4 外置脱敏报告没有 public URL；记录的 manifest 校验为 `99/99`，顶层 `SHA256SUMS` 文件的 SHA-256 为
  `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`。
- [x] exact rc.4 orphan-pipe fault run 在 PowerShell 7.6.4 中于 `32.164s` 返回 wrapper exit `2`，stdout
  `0` bytes、单一固定错误 `AIRLOCK_INVALID_JSON`；wrapper 返回后、external cleanup 前匹配后代残留为
  `1`，外部定向清理后为 `0`，
  所以正式 contract 与 candidate verdict 均为 `FAIL`。
- [x] rc.4 failure bundle manifest 校验为 `29/29`；顶层 `SHA256SUMS` 文件的 SHA-256 为
  `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`。
- [x] exact rc.5 为 annotated、unsigned tag object
  `7d4034f9e8575658190dacef53f9ba749de8ed6c`，commit
  `9abf825943f8f68f2bc6cd3afc1baa8717e0c01a`，tree
  `88b914598de60fa385820860b13dc8bd6db26b7d`。
- [x] exact rc.5 PowerShell 5.1/7 orphan-pipe faults 分别为 `3.352s / 3.937s`，均以 fixed error 返回，
  residual `0`、`cleanup_performed=false`；两壳 health、post-fault health 与中文/空格路径 analyze controls
  通过。该 scoped bundle manifest 为 `55/55`，顶层 `SHA256SUMS` 文件 SHA-256 为
  `107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`，尚无 public URL。
- [x] exact rc.6 为 annotated、unsigned tag object
  `ce81652ad107c59c52184c33417d1e9922d44281`，commit
  `2ea713a99053dae5ff96f8e9927c300d36439c0e`，tree
  `3a1554d94892baf8b32dbbdaedbe6f334d6f952c`。
- [x] rc.6 archive SHA-256 为
  `8be21cf914a1488c09435e2c242c97e54fdb5cad63dbc783bed8c6e175055d09`；干净安装测试为
  `228 passed / 9 skipped`，真实 OpenVINO analyze 为 `ALLOW_WITH_TRANSFORM`、CPU、71 chunks、8 facts、
  zero fallback。
- [x] Intel Core i7-14700KF 七次 warm wrapper sample 全部 contract-valid；P50 `5021.900 ms`、P95
  `5193.160 ms`。不声称 NPU/GPU 或完整 Agent host acceptance。

## GO / NO-GO 硬门

| Gate | 当前状态 | 发布前所需证据 |
|---|---|---|
| G0 · Source identity | **PASS_WITH_LIMITATION** | rc.6 annotated、unsigned tag object `ce81652ad107c59c52184c33417d1e9922d44281`；commit `2ea713a99053dae5ff96f8e9927c300d36439c0e`；tree `3a1554d94892baf8b32dbbdaedbe6f334d6f952c`；rc.1–rc.5 未移动；unsigned 状态必须随引用保留 |
| G1 · Evidence integrity | **PASS** | SHA256SUMS 与 JSON parse 持续通过 |
| G2 · Mac OpenVINO path | **PASS** | rc.1 evidence 已覆盖固定模型、CPU、无 fallback、A/B |
| G3 · Public claims | **PASS_WITH_UNPUBLISHED_WINDOWS_EVIDENCE** | 所有数字进入 [Claims Ledger](claims-ledger.md)，公开文本已扫描；rc.3、rc.4 与 rc.5 Windows 外置脱敏 evidence 均尚无 public URL |
| G4 · Packaging assets | **PASS** | SVG/PNG 全部渲染、解码与逐图检查；未见敏感信息 |
| G5 · Article | **READY_WITH_HOST_PLACEHOLDER** | [提交稿](modelscope-article-submission.md) 已纳入 rc.6、Intel CPU 实测、Hybrid AI、优化与限制；发布前必须回填真实 TraeCode 截图/轨迹和 Skill URL |
| G6 · Project LICENSE / author | **PASS** | Apache-2.0；2026 谭天晔；公开 author/byline 已确认并同步 |
| G6B · Release metadata | **PASS_WITH_PLATFORM_PREFLIGHT** | icon、实测 `mem_need_gb=1.0`、`server_alive_timeout=300` 与 extra fields 已关闭；`models=[]` 仍需上传 parser 实测 |
| G7 · Windows PowerShell | **FAIL_RC3 / FAIL_RC4 / RC5_SCOPED_PASS / FULL_MATRIX_INCONCLUSIVE** | rc.4 的 required orphan-pipe fault 与 candidate 保持 `FAIL`。exact rc.5 PS5.1/PS7 orphan-pipe residual 均为 `0`，health/analyze controls 通过；empty-cache、network 与 remaining external faults 未关闭，故只能写 scoped PASS |
| G8 · Production Agent host | **NOT_RUN** | TraeCode 已安装 exact rc.6 Skill 并预热，但登录、discovery、wrapper-first、Capsule-only non-bypass 与最终回答仍待真实轨迹 |
| G9 · Intel hardware | **CPU_FUNCTIONAL_AND_WARM_LATENCY_PASS_WITH_SCOPE** | 命名 Intel Core i7-14700KF；7/7 contract-valid；P50 `5021.900 ms`、P95 `5193.160 ms`。无 NPU/GPU、冷启动或通用性能声明 |
| G10 · GitHub source / Python CI | **RC6_PASS** | main run `33304754194` 与 tag run `33304834373` 均成功；Windows 与 Ubuntu jobs 全绿；CI 不替代 TraeCode host 验收 |
| G10B · ModelScope / media / submission | **AUTHORIZED / FORM_PREFILLED** | 登录态 owner `Ararag1`；名称、Apache-2.0、公开、开发工具、`AI PC` 与描述已预填。Chrome 本地文件访问未开启，archive upload、创建、文章和比赛回执未完成 |

最终比赛发布必须等待 G6B–G10B 中仍未关闭的硬门；GitHub rc.6 候选已发布不等于最终比赛发布获准。

## 1. Diff 与冻结边界

- [x] rc.2 → rc.3 历史 diff 不包含模型准备逻辑改动；rc.3 的 scoped Python CI 与正式 Windows FAIL
  分别保留，不能互相覆盖。
- [x] rc.3 → rc.4 candidate diff 只包含审查后的 OpenVINO native-handle 生命周期修复、相应回归测试和
  候选文档；发布前已复核并冻结完整 diff。
- [x] rc.4 → rc.5 candidate diff 包含审查后的 gated launcher、Windows Job Object process-tree containment、
  production wrapper integration 与回归测试；exact-tag scoped evidence 已独立复核。
- [x] rc.5 → rc.6 candidate diff 包含 TraeCode 安装说明、ModelScope release metadata、archive builder 与
  对应测试；exact-tag CI、干净 archive install 和 Windows Intel CPU wrapper sample 已独立复核。
- [x] 不修改、移动或重打 `v0.1.0-rc.1` 至 `v0.1.0-rc.5` 的任何已发布 tag。
- [x] 不修改 fixture、冻结期望值、detector、pipeline、token estimator 或安全边界；冻结前逐项确认。
- [x] `meta.json` 与 `info.json` 仍可解析；`meta.json` 只收窄能力描述，未猜测 author、icon URL、
  model hosting、内存、timeout 或版本策略。
- [x] 候选 diff 已按功能、CI、测试与文档逐项公开记录；不再沿用“packaging-only”范围断言。

## 2. Claims Ledger 与 frozen results

- [x] [Claims Ledger](claims-ledger.md) 记录每项公开数字的定义、commit、evidence path、JSON path、
  环境、样本范围、限制与渠道准入。
- [x] 固定限定语为 `Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1`。
- [x] Test claim：`212 passed / 6 skipped`；注明 6 项 PowerShell unavailable，且原始 pytest log
  不在 evidence bundle。
- [x] Flagship utility：rules-only / OpenVINO 均 `3/3 required facts retained`；不写成 Agent Task
  Success。
- [x] Secret P/R：两 variant 均 `1.0/1.0`；6 positive source files + 2 negative source files。
- [x] Injection P/R：两 variant 均 `1.0/1.0`；13 malicious + 12 benign；OpenVINO 不参与该分类。
- [x] Mean Recall@K：`0.583333 → 0.9375`；12 tasks、`K=4` 的算术平均。
- [x] Cross-lingual Mean Recall@K：`0.4375 → 1.0`；4 tasks、`K=4` 的算术平均。
- [x] Flagship estimated-token context reduction：`66.5564% → 75.3515%`；estimator 为
  `utf8_bytes_div_4_ceil_v1`，不称作 byte reduction，不外推到 micro-fixtures 或其他输入。
- [x] CLI P95：`103.052 ms → 1204.529 ms`；每 variant 42 次混合 CLI subprocess 调用。
- [x] 安全表述使用 `0/252 frozen known-fixture forbidden values observed in analyze stdout, stderr and audit log`，
  不使用无范围“零泄漏”。
- [x] `raw_sensitive_spans_forwarded=0` 不作为独立泄漏证明。
- [x] 当前图片、文章与视频脚本中的数字逐项与 ledger 复核。

## 3. README 与叙事

- [x] README 首屏顺序：Hero → 当前验证状态 → 架构 → 三张结果卡 → Flagship → Why Airlock →
  Quick Start → limitations → Evidence。
- [x] 定位为 `Local Context Gateway / Context Compiler for AI Agents`，不回退成 scanner 故事。
- [x] Hero 使用 `Your data stays. Your Agent works.`，并同时注明品牌语只覆盖 Airlock-controlled path、
  真实宿主 non-bypass 待验收。
- [x] Mac/OpenVINO rc.1 明确为 verified；Windows 明确记录 rc.3 FAIL、rc.4 candidate FAIL，以及 rc.5
  scoped PASS / full matrix INCONCLUSIVE；rc.6 Intel CPU wrapper sample 与 TraeCode host NOT_RUN 分开，
  不把 CPU 小样本写成 NPU/GPU 或完整 host 通过。
- [x] Python Qoder response gate 与真实 Qoder host 分开。
- [x] 合成 benchmark 的范围、负面结果和延迟代价可见。
- [x] 所有 README 相对链接目标存在，引用的 SVG/PNG 已在本地渲染复核。
- [ ] 公开上传后在 ModelScope/GitHub 目标渲染器做最终预览。

## 4. 视觉资产

- [x] `assets/competition/ai-airlock-icon.svg`
- [x] `assets/competition/hero-banner.svg`
- [x] `assets/competition/architecture.svg`
- [x] `assets/competition/benchmark-results.svg`
- [x] `assets/competition/capsule-example.svg`
- [x] `assets/competition/flagship-flow.svg`
- [x] `assets/competition/video-end-card.svg`
- [x] 对应 PNG 全部生成且能解码。
- [x] 逐图人工检查中文、字号、对齐、裁切、色彩和 16:9 安全区。
- [x] 架构图只允许 Capsule 跨越边界，Qoder 标为 `Host acceptance pending`。
- [x] benchmark 图同时展示 Mean Recall@K / estimated-token context reduction 与 P95 latency 代价。
- [x] 没有虚假 Qoder/Windows UI、用户名、绝对路径、账号、远程主机或敏感信息。

## 5. 文章

- [x] [ModelScope article draft](modelscope-article.md) 是完整中文初稿，不是提纲；已同步 rc.3 Windows
  FAIL、rc.4 candidate FAIL、rc.5 scoped PASS / overall INCONCLUSIVE 与 Qoder/Intel NOT_RUN，但尚未
  授权公开发布。
- [x] 包含真实生产问题、普通脱敏不足、Capsule、安全边界、OpenVINO、flagship、A/B、Qoder
  设计、verified/pending、复现、limitations、商用路线。
- [x] Mac/OpenVINO 数字来自 frozen evidence，并引用 Claims Ledger。
- [x] Windows/Qoder 截图、Agent 回答与 Intel/Windows 性能保留明确占位。
- [x] 不把合成结果写成通用安全或合规保证。
- [ ] 用户确认最终标题、署名、项目 LICENSE 和外部链接后再发布。

## 6. Qoder / Windows 回填

权威 oracle 为 [qoder_acceptance.md](qoder_acceptance.md)。rc.3 只执行到两个 shell 的 cold health，且
均失败。rc.4 从精确 fresh tag 执行了 regression subset，随后正式 orphan-pipe fault oracle 在 wrapper
返回后、external cleanup 前观察到匹配后代残留 `1`，因此 exact rc.4 Windows candidate 与 overall 均为
`FAIL`。exact rc.5 已通过
两壳 orphan-pipe no-residual-process oracle 与 scoped health/analyze controls。source-artifact cache 预填、
network `NOT_MEASURED`、其余 timeout/fault cases `NOT_RUN`、Qoder host evidence unavailable 与 Intel performance
`NOT_RUN` 均是独立未知项：

- [x] rc.3 PowerShell 5.1 cold health：`FAIL` / `AIRLOCK_MODEL_PREPARATION_FAILED`。
- [x] rc.3 PowerShell 7 cold health：`FAIL` / `AIRLOCK_MODEL_PREPARATION_FAILED`。
- [x] exact rc.4 PowerShell 5.1 独立 cold / warm health（source-artifact cache 预填）。
- [x] exact rc.4 PowerShell 7 独立 cold / warm health（source-artifact cache 预填）。
- [x] 中文 task 与带空格绝对路径 analyze。
- [x] fixed invalid/missing error JSON。
- [x] cross-shell concurrent cold；covered cases residual child-process count `0`。
- [x] known-marker scan：`252` markers × `26` stdout/stderr surfaces，`0 hits`；不构成通用零泄漏保证。
- [x] exact rc.4 orphan-pipe fault：deadline/fixed-error oracle PASS；wrapper 返回后、external cleanup 前匹配后代残留 `1`，
  no-residual oracle FAIL，外部定向清理后残留 `0`；candidate verdict `FAIL`。
- [x] exact rc.5 PowerShell 5.1 orphan-pipe fault：`3.352s`、fixed error、residual `0`、
  `cleanup_performed=false`。
- [x] exact rc.5 PowerShell 7 orphan-pipe fault：`3.937s`、fixed error、residual `0`、
  `cleanup_performed=false`。
- [x] exact rc.5 两壳 health、post-fault health 与中文/空格路径 analyze controls：`PASS_WITH_SCOPE`。
- [ ] cold-bootstrap / task-period network：`NOT_MEASURED`。
- [ ] remaining timeout/fault cases（不含已执行的 rc.5 orphan-pipe case）：`NOT_RUN`。
- [ ] Qoder Skill 安装、版本、实际加载路径与自动发现。
- [ ] 12/12 positive triggers 正确触发。
- [ ] 12/12 negative triggers 不误触发。
- [ ] 第一次内容访问是 wrapper，不存在 raw/index/attachment/tool bypass。
- [ ] `ALLOW_WITH_TRANSFORM` 后只消费 `safe_context`。
- [ ] `BLOCK` 后停止。
- [ ] 最终回答引用 `source:local_ref` 并保留三项根因事实。
- [ ] 任务期非预期网络调用和 workspace bypass 均有真实计数。
- [x] 外置脱敏报告已返回：无 public URL；manifest `99/99`；顶层 `SHA256SUMS` 文件 SHA-256
  `3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`。
- [x] rc.4 failure bundle 已返回：无 public URL；manifest `29/29`；顶层 `SHA256SUMS` 文件 SHA-256
  `00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`。
- [x] rc.5 scoped bundle 已返回：无 public URL；manifest `55/55`；顶层 `SHA256SUMS` 文件 SHA-256
  `107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`。
- [ ] 保存完整 Qoder transcript、工具轨迹、环境、设置 hash 与未经剪辑原片。

如果无法证明 Qoder 在调用前没有从索引、附件或 editor context 获得 raw，本次结果只能为
`INCONCLUSIVE`，不能填 PASS。

## 7. 视频

- [x] [Demo script](demo-script.md) 分为 Mac 可拍、Windows/Qoder 替换、最终 60 秒、未剪辑证据原片。
- [x] Mac CLI 始终标 `not Windows/Qoder`。
- [ ] 最终 End Card 剪辑层加入 `rc.3/rc.4 Windows FAIL · rc.5 scoped PASS / overall INCONCLUSIVE · Qoder
  NOT_RUN`；当前冻结 SVG/PNG 只有通用 `Windows / Qoder evidence pending`，尚未渲染该状态 overlay。
- [ ] Mac 原片记录 tag/commit/tree/clean、SHA256、OpenVINO metadata、benchmark run ID。
- [ ] Windows/Qoder 原片连续覆盖第一次目标访问到最终回答。
- [ ] 60 秒成片无声可理解；字幕安全区、codec、分辨率和目标平台转码已检查。
- [ ] 成片与原片 SHA-256 进入最终 evidence manifest。

## 8. License、第三方与元数据

- [x] [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md) 列出直接依赖、已知 extras、模型来源和许可。
- [x] [License decision](license-decision.md) 比较 MIT 与 Apache-2.0，并保留用户决策。
- [x] **项目 LICENSE**：Apache-2.0；根目录标准文本已创建。
- [x] **版权主体与年份**：谭天晔 / 2026。
- [x] **公开 author**：谭天晔；`pyproject.toml` 与 `meta.json` 已同步。
- [x] **版本展示**：package `0.1.0`；已发布候选 Tag `v0.1.0-rc.6`；不移动 rc.1–rc.5。
- [x] **模型托管策略**：继续固定上游 revision + 本地验证与转换；不虚构预转换 ModelScope 模型仓库。
- [x] **只在 `meta.json` 填真实公开 icon URL**：使用 rc.5 不可变 tag 下 PNG；未添加到 `info.json`。
- [x] **实测 `mem_need_gb`**：Windows OpenVINO analyze 观察峰值 `0.702 GiB`，配置向上取整为 `1.0`。
- [x] **`server_alive_timeout`**：使用官方明确默认值 `300`；不再使用未定义的 `0`。
- [ ] **确认 `models=[]` 被平台接受**，或完成公开转换模型 repo、固定 revision、required files、哈希与再分发复核。
- [x] **移除 `info.json` 额外字段**：只保留官方模板字段。
- [x] **确认 `ai-airlock` 命名决策**：用户已确认 ModelScope `skill_name`，TraeCode 名称语法兼容。
- [x] **对齐 `SKILL.md` host 模板**：加入 Usage / Examples、真实 retry resume、unsupported-platform
  与 no-cloud-fallback；真实宿主调用仍由 TraeCode acceptance 单独判定。
- [ ] 若发布 wheel/离线包，冻结完整 transitive dependency lock，并收集实际分发包的 LICENSE/NOTICE。

## 9. Submission fields 与 URL

- [x] [Submission fields](modelscope-submission-fields.md) 已准备标题、短简介、长简介、标签和 use cases。
- [x] 比赛硬门已写入 runbook：Skill 自定义标签必须为 `AI PC`；文章专题标签必须为 `Intel AI PC`。
- [x] 用户已批准 Apache-2.0，项目 `LICENSE` 已纳入 tracked-file allowlist 与发布 archive。
- [x] rc.6 Skill archive 含代码、文档和测试用例，共 138 个条目；根目录有且仅有一个 `SKILL.md`。
- [ ] 真实 API / CLI 上传预检已解决官方“根目录仅一个 `SKILL.md`”与比赛完整包要求之间的规范歧义。
- [x] GitHub / source repository URL：`https://github.com/tty627/ai-airlock`；远端 rc.4 历史失败身份、
  rc.5 scoped evidence 与 rc.6 tag/CI/Intel CPU evidence 均已核对；真实 Agent host acceptance 仍未完成。
- [ ] ModelScope Skill URL：`[PENDING_AFTER_PUBLICATION]`。
- [ ] 研习社文章 URL：`[PENDING_AFTER_PUBLICATION]`。
- [ ] Demo / video URL：`[PENDING_AFTER_PUBLICATION]`。
- [x] Icon URL：使用 rc.5 不可变 tag 下的公开 PNG，已写入 `meta.json`。
- [x] 登录态 ModelScope 表单已确认 owner `Ararag1`、名称、License、公开状态、描述、类型、标签、
  文件上传与创建按钮；deadline 页面已核对为 `2026-08-31 23:59`。

## 10. 本地 QA

- [x] 七个 SVG XML 合法，且 ImageMagick 兼容性栅格化逐项返回成功。
- [x] 七个 PNG 从修正后的 SVG 以标准浏览器 SVG renderer 重新导出并可解码；icon 为
  `1024×1024 RGBA`，其余六张为 `1600×900`。
- [x] `meta.json`、`info.json`、evidence `benchmark/latest.json` 与本项目其他 JSON 均可解析。
- [x] tracked diff 与未跟踪 Markdown/SVG 的 whitespace check 均通过。
- [x] 本地 Markdown 链接目标全部存在；rc.3/rc.4 精确身份只作为不可变历史失败证据保留，rc.5 owner
  handoff 已回填精确 tag object / commit / tree。
- [x] 公开文本无本机用户名、账号、远程主机、真实 endpoint、机器特定绝对路径或未限定“零泄漏”；
  handoff 仅保留泛化且带唯一 run ID 的 Windows 验收模板路径。
- [x] Secret / PII 扫描覆盖 submission-facing Markdown；SVG 做文本扫描，7 个 PNG 做逐图目检与字符串扫描。
- [x] rc.1–rc.5 tag、commit 与 tree 未变化；不得移动旧标签来承载修复。
- [x] exact rc.5 tag CI 只算 scoped Python evidence；exact-tag Windows bundle 只覆盖指定 fault 与 controls，
  不等于 complete matrix 或 Qoder PASS；post-tag 文档提交不改变 candidate identity。

## 11. 发布 Runbook

[Publication runbook](publication-runbook.md) 已包含 tracked/allowlist 打包、denylist、全新目录复验、
SHA-256 manifest、公开 evidence 与 ModelScope 下载后复验。GitHub candidate、ModelScope Skill、文章和
比赛提交均已获授权；仍不得执行：

- 移动、删除或重打任何既有 RC 标签；
- 未授权的社交媒体发布，或超出比赛交付所需范围的外部发布；
- 捏造或提前回填尚不存在的公开 URL、平台回执或实机证据；
- 用 Mac 结果替代 Windows/Qoder/Intel；
- 改写已确认的 LICENSE、author 或 candidate identity。

本轮目标授权覆盖 ModelScope Skill、研习社文章、比赛作品和新的不可变 GitHub tag/release。

## 本轮最终 readiness flags

本轮本地 QA 结论：

```text
MAC_DOCS_AND_ASSETS_READY = YES
CLAIMS_TRACEABLE = YES
RC3_WINDOWS_PUBLIC_EVIDENCE_READY = NO
RC4_WINDOWS_PUBLIC_EVIDENCE_READY = NO
RC5_WINDOWS_PUBLIC_EVIDENCE_READY = NO
VISUAL_RENDERING = PASS
RELEASE_METADATA_READY = YES_WITH_PLATFORM_PREFLIGHT
FINAL_PUBLICATION_READY = NO

ARTICLE_DRAFT_READY = YES
WINDOWS_HANDOFF_MATERIAL_READY = YES
WINDOWS_CANDIDATE_IDENTITY_READY = YES
INTEL_CPU_EVIDENCE_READY = YES
TRAE_HOST_EVIDENCE_READY = NO
```

`RELEASE_METADATA_READY=YES_WITH_PLATFORM_PREFLIGHT` 表示内存、icon、timeout 与 self-managed fixed-model
策略已有证据，但 `models=[]` 仍必须由真实平台上传 parser 决定。`FINAL_PUBLICATION_READY=NO` 还包括
TraeCode 登录/host evidence、ModelScope archive upload、文章和比赛提交回执；rc.6 CI 与 Intel CPU sample
都不能写成完整 host PASS。
`CLAIMS_TRACEABLE=YES` 只表示本地 claim-to-evidence 映射完整；rc.3、rc.4 与 rc.5 Windows 脱敏
evidence 尚未公开，公众当前不能独立下载复核。
