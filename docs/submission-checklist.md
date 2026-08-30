# AI Airlock Submission Readiness Checklist

当前状态入口为 [`../STATUS.md`](../STATUS.md)。Windows 执行顺序与报告格式分别见
[Windows validation handoff](windows-validation-handoff.md) 和
[Windows validation report template](windows-validation-report-template.md)。

> 包装基线：`v0.1.0-rc.1` · `495f89c6349afbdd741576439b3b85369d26671a`
> 公开 `tty627/ai-airlock` 使用 Apache-2.0、署名“谭天晔”；annotated、unsigned、按流程不可变的
> `v0.1.0-rc.4` 候选已发布。既有 rc.1/rc.2/rc.3 不移动；ModelScope、文章、视频和比赛表单尚未授权发布。

## 当前结论

技术 RC 已具备 SHA 绑定的 macOS / Apple M4 / OpenVINO release evidence，rc.4 精确身份和 scoped
Windows/Ubuntu Python 3.12 CI 也已固化。exact rc.3 的正式 Windows cold health `FAIL` 历史保持不变。
rc.4 fresh-tag Windows regression subset 已通过，但 source-artifact cache 预填、网络 `NOT_MEASURED`、
remaining timeout/fault matrix `NOT_RUN`，所以 Windows full matrix 仍为 `INCONCLUSIVE`。这一限制再加
Qoder 缺席/`NOT_RUN` 与 Intel performance `NOT_RUN`，使 overall 为 `INCONCLUSIVE`。这些缺口、release
metadata 和未授权平台动作仍阻断最终发布。

```text
RC.1 CLEAN CHECKOUT                 PASS / HISTORICAL
RC.4 SOURCE CANDIDATE               PUBLISHED / ANNOTATED UNSIGNED
MAC OPENVINO CLI + A/B              PASS
PYTHON QODER STRICT RESPONSE GATE   PASS
WINDOWS POWERSHELL                  RC.3 FAIL / RC.4 SUBSET PASS / FULL MATRIX INCONCLUSIVE
QODER HOST CAPSULE-ONLY             NOT RUN
INTEL PERFORMANCE                   NOT RUN
RC.3 PRE-CANDIDATE PYTHON CI        PASS / WINDOWS + UBUNTU / HISTORICAL
EXACT RC.3 MAIN/TAG CI              PASS / WINDOWS + UBUNTU (HISTORICAL)
EXACT RC.4 MAIN/TAG CI              PASS / WINDOWS + UBUNTU / SCOPED PYTHON CI
GITHUB SOURCE                       PUBLIC / AUTHORIZED
OTHER PUBLICATION                   NOT AUTHORIZED
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

## GO / NO-GO 硬门

| Gate | 当前状态 | 发布前所需证据 |
|---|---|---|
| G0 · Source identity | **PASS_WITH_LIMITATION** | rc.4 annotated、unsigned tag object `2a50625aa95443e328573704cf42e9c633621ffe`；commit `52a215727115f32937cb78561e88a63fdae5adf2`；tree `46bc0f55eed58b7234338d4ff4e32bc71c348f8a`；rc.1/rc.2/rc.3 未移动；unsigned 状态必须随引用保留 |
| G1 · Evidence integrity | **PASS** | SHA256SUMS 与 JSON parse 持续通过 |
| G2 · Mac OpenVINO path | **PASS** | rc.1 evidence 已覆盖固定模型、CPU、无 fallback、A/B |
| G3 · Public claims | **PASS_WITH_UNPUBLISHED_WINDOWS_EVIDENCE** | 所有数字进入 [Claims Ledger](claims-ledger.md)，公开文本已扫描；rc.3 与 rc.4 Windows 外置脱敏 evidence 均尚无 public URL |
| G4 · Packaging assets | **PASS** | SVG/PNG 全部渲染、解码与逐图检查；未见敏感信息 |
| G5 · Article | **READY_WITH_LIMITATIONS** | 初稿已同步 rc.3 FAIL、rc.4 subset PASS / full matrix INCONCLUSIVE、Qoder/Intel NOT_RUN；尚未授权公开发布 |
| G6 · Project LICENSE / author | **PASS** | Apache-2.0；2026 谭天晔；公开 author/byline 已确认并同步 |
| G6B · Release metadata | **BLOCKED** | icon URL、实测 `mem_need_gb`、timeout 语义、`models=[]` 平台接受度、额外字段 parser 行为 |
| G7 · Windows PowerShell | **FAIL_RC3 / RC4_SUBSET_PASS / FULL_MATRIX_INCONCLUSIVE** | rc.4 fresh-tag regression subset 覆盖 5.1/7 独立 cold+warm、中文/空格路径、invalid/missing errors、cross-shell concurrent cold、covered residual `0`；source-artifact cache 预填、network NOT_MEASURED、remaining timeout/fault NOT_RUN，故 Windows full matrix 仍为 `INCONCLUSIVE` |
| G8 · Qoder host | **NOT_RUN** | discovery、12+12 triggers、Capsule-only non-bypass、最终回答 |
| G9 · Intel hardware | **PERFORMANCE_NOT_RUN** | rc.4 functional regression subset 不等于命名 Intel device、runtime telemetry、cold/warm latency、p50/p95、吞吐或失败数 evidence；不得从 CPU 字符串或功能通过推导性能结论 |
| G10 · GitHub source / Python CI | **RC4_PASS_WITH_SCOPE** | main run `33293985019`、tag run `33294040300` 均成功；Windows/Ubuntu 四个 Python 3.12 job 各 `212 passed / 8 skipped`，Ruff/format/benchmark smoke PASS；未覆盖 `.[openvino]`、wrapper、Qoder 或 Intel |
| G10B · ModelScope / media / submission | **NOT AUTHORIZED / NOT RUN** | 平台 preflight、公开页面、文章/视频发布与比赛提交回执 |

最终比赛发布必须等待 G6B–G10B 中仍未关闭的硬门；GitHub rc.4 候选已发布不等于最终比赛发布获准。

## 1. Diff 与冻结边界

- [x] rc.2 → rc.3 历史 diff 不包含模型准备逻辑改动；rc.3 的 scoped Python CI 与正式 Windows FAIL
  分别保留，不能互相覆盖。
- [x] rc.3 → rc.4 candidate diff 只包含审查后的 OpenVINO native-handle 生命周期修复、相应回归测试和
  候选文档；发布前已复核并冻结完整 diff。
- [x] 不修改、移动或重打 `v0.1.0-rc.1`、`v0.1.0-rc.2` 或 `v0.1.0-rc.3`。
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
- [x] Mac/OpenVINO rc.1 明确为 verified；Windows 明确记录 rc.3 FAIL / rc.4 regression subset PASS /
  full matrix INCONCLUSIVE；Qoder absent/NOT_RUN 与 Intel performance NOT_RUN 不写成已通过。
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
  FAIL、rc.4 regression subset PASS / full matrix INCONCLUSIVE 与 Qoder/Intel NOT_RUN，但尚未授权公开发布。
- [x] 包含真实生产问题、普通脱敏不足、Capsule、安全边界、OpenVINO、flagship、A/B、Qoder
  设计、verified/pending、复现、limitations、商用路线。
- [x] Mac/OpenVINO 数字来自 frozen evidence，并引用 Claims Ledger。
- [x] Windows/Qoder 截图、Agent 回答与 Intel/Windows 性能保留明确占位。
- [x] 不把合成结果写成通用安全或合规保证。
- [ ] 用户确认最终标题、署名、项目 LICENSE 和外部链接后再发布。

## 6. Qoder / Windows 回填

权威 oracle 为 [qoder_acceptance.md](qoder_acceptance.md)。rc.3 只执行到两个 shell 的 cold health，且
均失败。rc.4 从精确 fresh tag 执行了 regression subset；source-artifact cache、network 和 timeout/fault
限制使 Windows full matrix 为 `INCONCLUSIVE`。这一限制再加 Qoder host 缺席/`NOT_RUN` 与 Intel
performance `NOT_RUN`，使 overall 为 `INCONCLUSIVE`：

- [x] rc.3 PowerShell 5.1 cold health：`FAIL` / `AIRLOCK_MODEL_PREPARATION_FAILED`。
- [x] rc.3 PowerShell 7 cold health：`FAIL` / `AIRLOCK_MODEL_PREPARATION_FAILED`。
- [x] exact rc.4 PowerShell 5.1 独立 cold / warm health（source-artifact cache 预填）。
- [x] exact rc.4 PowerShell 7 独立 cold / warm health（source-artifact cache 预填）。
- [x] 中文 task 与带空格绝对路径 analyze。
- [x] fixed invalid/missing error JSON。
- [x] cross-shell concurrent cold；covered cases residual child-process count `0`。
- [x] known-marker scan：`252` markers × `26` stdout/stderr surfaces，`0 hits`；不构成通用零泄漏保证。
- [ ] cold-bootstrap / task-period network：`NOT_MEASURED`。
- [ ] remaining timeout/fault matrix：`NOT_RUN`。
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
- [ ] 保存完整 Qoder transcript、工具轨迹、环境、设置 hash 与未经剪辑原片。

如果无法证明 Qoder 在调用前没有从索引、附件或 editor context 获得 raw，本次结果只能为
`INCONCLUSIVE`，不能填 PASS。

## 7. 视频

- [x] [Demo script](demo-script.md) 分为 Mac 可拍、Windows/Qoder 替换、最终 60 秒、未剪辑证据原片。
- [x] Mac CLI 始终标 `not Windows/Qoder`。
- [x] 当前 End Card 保留 `rc.3 Windows FAIL · rc.4 subset PASS / full matrix INCONCLUSIVE · Qoder NOT_RUN`。
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
- [x] **版本展示**：package `0.1.0`；已发布 Windows 候选 Tag `v0.1.0-rc.4`；不移动 rc.1/rc.2/rc.3/rc.4。
- [ ] **用户确认模型托管**：继续固定上游 revision + 本地转换，或另建公开转换模型仓库。
- [ ] **只在 `meta.json` 填真实公开 icon URL**；不得使用本机路径或添加到 `info.json`。
- [ ] **实测 `mem_need_gb`**：必须覆盖模型驻留 + 推理峰值；当前 `0.25` 不构成发布依据。
- [ ] **确认 `server_alive_timeout=0` 的 host 语义**；官方说明只明确默认 `300` 和 `-1`。
- [ ] **确认 `models=[]` 被平台接受**，或完成公开转换模型 repo、固定 revision、required files、哈希与再分发复核。
- [ ] **确认 `info.json` 额外字段被目标 parser 接受**。
- [ ] **确认目标 host 接受 `ai-airlock` 命名**；OpenVINO 文件规范使用 `local-<function>` 约定，
  不可变 `skill_name` 必须在创建前由用户确认。
- [ ] **确认 `SKILL.md` 与目标 host 模板兼容**；当前没有与 wrapper 对齐的 `--continue` 支持，也未完整
  覆盖官方 Usage / Examples / unsupported-platform / no-cloud-fallback 结构，不能只靠文案宣称通过。
- [ ] 若发布 wheel/离线包，冻结完整 transitive dependency lock，并收集实际分发包的 LICENSE/NOTICE。

## 9. Submission fields 与 URL

- [x] [Submission fields](modelscope-submission-fields.md) 已准备标题、短简介、长简介、标签和 use cases。
- [x] 比赛硬门已写入 runbook：Skill 自定义标签必须为 `AI PC`；文章专题标签必须为 `Intel AI PC`。
- [x] 用户已批准 Apache-2.0，项目 `LICENSE` 已纳入 tracked-file allowlist 与发布 archive。
- [ ] 发布 Skill archive 同时包含代码、文档和测试用例，且根目录有且仅有一个 `SKILL.md`。
- [ ] 真实 API / CLI 上传预检已解决官方“根目录仅一个 `SKILL.md`”与比赛完整包要求之间的规范歧义。
- [x] GitHub / source repository URL：`https://github.com/tty627/ai-airlock`；远端 rc.4 tag、scoped CI 与 fresh-tag subset 已核对，不能外推为 full host PASS。
- [ ] ModelScope Skill URL：`[PENDING_AFTER_PUBLICATION]`。
- [ ] 研习社文章 URL：`[PENDING_AFTER_PUBLICATION]`。
- [ ] Demo / video URL：`[PENDING_AFTER_PUBLICATION]`。
- [ ] Icon URL：`[PENDING_AFTER_ASSET_HOSTING]`。
- [ ] 真实提交表单字段、字数限制、文件格式和 deadline 由用户在登录态复核。

## 10. 本地 QA

- [x] 七个 SVG XML 合法，且 ImageMagick 兼容性栅格化逐项返回成功。
- [x] 七个 PNG 从修正后的 SVG 以标准浏览器 SVG renderer 重新导出并可解码；icon 为
  `1024×1024 RGBA`，其余六张为 `1600×900`。
- [x] `meta.json`、`info.json`、evidence `benchmark/latest.json` 与本项目其他 JSON 均可解析。
- [x] tracked diff 与未跟踪 Markdown/SVG 的 whitespace check 均通过。
- [x] 本地 Markdown 链接目标全部存在；rc.3 精确身份只作为不可变历史失败证据保留，rc.4 owner
  handoff 已回填精确 tag object / commit / tree。
- [x] 公开文本无本机用户名、账号、远程主机、真实 endpoint、机器特定绝对路径或未限定“零泄漏”；
  handoff 仅保留泛化且带唯一 run ID 的 Windows 验收模板路径。
- [x] Secret / PII 扫描覆盖 submission-facing Markdown；SVG 做文本扫描，7 个 PNG 做逐图目检与字符串扫描。
- [x] rc.1/rc.2/rc.3 tag、commit 与 tree 未变化；不得移动旧标签来承载修复。
- [x] exact rc.4 tag CI 只算 scoped Python evidence；fresh-tag regression subset 不等于 Windows full matrix
  或 Qoder PASS，且 post-tag 文档提交不改变 candidate identity。

## 11. 发布 Runbook

[Publication runbook](publication-runbook.md) 已包含 tracked/allowlist 打包、denylist、全新目录复验、
SHA-256 manifest、公开 evidence 与 ModelScope 下载后复验。GitHub candidate commit/push/tag 已获授权；
仍不得在没有单独授权和相应硬门证据时执行：

- 移动、删除或重打任何既有 RC 标签；
- ModelScope、研习社、视频平台、比赛表单或社交媒体发布；
- 捏造或提前回填尚不存在的公开 URL、平台回执或实机证据；
- 用 Mac 结果替代 Windows/Qoder/Intel；
- 改写已确认的 LICENSE、author 或 candidate identity。

GitHub candidate 同步已经完成；这不自动授权 ModelScope、文章、视频或比赛提交。

## 本轮最终 readiness flags

本轮本地 QA 结论：

```text
MAC_DOCS_AND_ASSETS_READY = YES
CLAIMS_TRACEABLE = YES
RC3_WINDOWS_PUBLIC_EVIDENCE_READY = NO
RC4_WINDOWS_PUBLIC_EVIDENCE_READY = NO
VISUAL_RENDERING = PASS
RELEASE_METADATA_READY = NO
FINAL_PUBLICATION_READY = NO

ARTICLE_DRAFT_READY = YES
WINDOWS_HANDOFF_MATERIAL_READY = YES
WINDOWS_CANDIDATE_IDENTITY_READY = YES
```

`RELEASE_METADATA_READY=NO` 是因为未测内存、icon URL、timeout、模型托管与 parser 接受度尚未关闭；
`FINAL_PUBLICATION_READY=NO` 还包括 release metadata、未授权平台发布、rc.4 Windows full matrix、Qoder
与 Intel 性能缺口。rc.4 scoped CI 和 Windows regression subset 都不能写成完整 host PASS。
`CLAIMS_TRACEABLE=YES` 只表示本地 claim-to-evidence 映射完整；rc.3 与 rc.4 Windows 脱敏 evidence 尚未
公开，公众当前不能独立下载复核。
