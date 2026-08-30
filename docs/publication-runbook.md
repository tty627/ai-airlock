# AI Airlock Publication Runbook

> 状态：GitHub candidate 发布已完成。公开 `tty627/ai-airlock` 使用 Apache-2.0、署名“谭天晔”，新的
> annotated、unsigned `v0.1.0-rc.5` 已发布并按流程保持不可变；既有 `v0.1.0-rc.1` 至
> `v0.1.0-rc.4` 不移动。用户已授权本轮发布 ModelScope Skill、研习社文章、比赛作品以及新的
> 不可变 GitHub tag/release；不授权移动 rc.1–rc.5，也不包含社交媒体发布。

当前项目状态以 [`../STATUS.md`](../STATUS.md) 为入口。tagged commit 不能安全地把自己的 commit/tree
哈希或 tag object 写回自身，因此这些值由 tag 解析，并在本文和
[Windows validation handoff](windows-validation-handoff.md) 这类 post-tag 文档中固化；tag 内 handoff
保留同一套解析与核对方法。

`v0.1.0-rc.3` 的正式 Windows verdict 是 `FAIL`：PowerShell 5.1 与 7 cold health 均返回
`AIRLOCK_MODEL_PREPARATION_FAILED`。诊断定位到 inference smoke 后缓存的 OpenVINO native handles
阻止 candidate model directory 原子 rename（`PermissionError` / WinError 5）。Qoder 为 `NOT_RUN`。

`v0.1.0-rc.4` 的早期 fresh-tag Windows functional subset 已通过，但同一 immutable exact tag 后续
orphan-pipe 必需 oracle `FAIL`：wrapper 返回后 external cleanup 前/后 residual 为 `1/0`。因此 rc.4
Windows candidate 与 overall verdict 均为 `FAIL`；不得用 prefilled cache、network `NOT_MEASURED`、
remaining faults `NOT_RUN`、Qoder 或 Intel 未执行项把决定性失败改写为 `INCONCLUSIVE`。

`v0.1.0-rc.5` 已通过 exact-tag PowerShell 5.1/7 orphan-pipe no-residual-process oracles 和指定
health/analyze controls，状态为 `RC5_WINDOWS_SCOPED_VALIDATION=PASS_WITH_SCOPE`。empty-cache、network、
remaining external faults、Qoder 与 Intel performance 尚未关闭，因此当前 candidate overall 为
`INCONCLUSIVE`，不是完整 Windows 或最终发布 `PASS`。

本 runbook 于 2026-08-30 复核以下一手资料：

- [ModelScope 比赛页](https://www.modelscope.cn/events/289/summary)；
- [ModelScope Skills Center 发布与安装规范](https://github.com/modelscope/modelscope-skills/blob/main/skills/ms-hub/references/skills-center.md)；
- [OpenVINO Local AI Skill 文件规范](https://github.com/openvino-dev-samples/local-ai-skill-authoring/blob/main/references/file-reference.md)；
- [OpenVINO `meta.json` 模板](https://raw.githubusercontent.com/openvino-dev-samples/local-ai-skill-authoring/main/assets/meta.template.json)
  与 [`info.json` 模板](https://raw.githubusercontent.com/openvino-dev-samples/local-ai-skill-authoring/main/assets/info.template.json)。

官方页面可能变化；真正提交前必须在登录态重新核对，不把本文的日期或页面快照当成永久规则。

## 0. 发布身份

```text
Core source tag:    v0.1.0-rc.1
Core source commit: 495f89c6349afbdd741576439b3b85369d26671a
Core source tree:   4fe991ded88f38a6c1952c506d20005d2956a915
Local evidence:     .release-evidence/495f89c6349afbdd741576439b3b85369d26671a/
Candidate tag:      v0.1.0-rc.5 (annotated, unsigned, published)
Candidate tag object: 7d4034f9e8575658190dacef53f9ba749de8ed6c
Candidate commit:   9abf825943f8f68f2bc6cd3afc1baa8717e0c01a
Candidate tree:     88b914598de60fa385820860b13dc8bd6db26b7d
Packaging source:   exact reviewed post-tag commit or immutable packaging tag (required before archive)
```

不要移动、重打或修改 rc.1 至 rc.5 的任何已发布 tag。rc.5 含候选代码，但不含验证完成后的状态文档；
因此最终 archive 不得直接从 rc.5 tag 生成。先冻结一个只含已审查 post-tag 文档回填的精确 packaging
commit/tag，并记录 packaging identity 与 rc.5 candidate identity 的映射。rc.1 evidence 只能支持未被
包装修改改变的 core claims，不能冒充后续源码的完整 evidence。

## 1. 比赛与平台强制门

以下是发布 gate，不是建议：

1. **Skill 包必须同时包含代码、文档和测试用例。** 缺任一类即停止。
2. **ModelScope Skill 必须添加自定义标签 `AI PC`。** 精确保留大小写与空格。
3. **比赛文章必须添加专题标签 `Intel AI PC`。** 该标签是比赛归类，不得写成 Intel 实机已验证。
4. Skill 必须发布到 ModelScope Skills Center，并在最终指定的生产力 Agent 中完成调用验证；AI Airlock
   当前 Windows 状态是 `rc.3 FAIL / rc.4 CANDIDATE FAIL / rc.5 SCOPED PASS / FULL MATRIX
   INCONCLUSIVE`，Qoder 仍为 `NOT_RUN`。
5. ModelScope zip 根目录必须有且仅有一个 `SKILL.md`；若采用 CLI 发布路径，还要满足其 frontmatter
   与 5 MB 限制。官方同页对 frontmatter 的 `version` 要求存在表述差异，必须在真实上传路径的预检中
   解决，不能假设当前包一定被接受。

这里还有一个必须通过真实上传预检解决的规范歧义：Skills Center 文档一处写 zip 根目录“有且仅有
一个 `SKILL.md` 且无其他内容”，同页又给出可含 `scripts/`、`references/`、`examples/` 的 Skill
目录结构，而比赛要求作品同时包含代码、文档和测试。当前 runbook 按比赛完整包准备，但在目标 API / CLI
接受完整目录前，不能把本地 zip 判定为平台兼容。

任何 gate 失败都不得通过删除测试、缩短 limitation、改写 fixture 或伪造 host evidence 绕过。

## 2. 用户决策与元数据阻断

```text
Project LICENSE:          Apache-2.0
Copyright holder/year:    谭天晔 / 2026
Public author/byline:     谭天晔
Version display strategy: package 0.1.0 / published immutable candidate tag v0.1.0-rc.7
ModelScope owner:         [RESOLVE FROM AUTHENTICATED /users/me; immutable after create]
ModelScope skill_name:    ai-airlock (confirmed; immutable after create)
Category:                 developer-tools (confirmed)
Public repository:        https://github.com/tty627/ai-airlock
Model hosting strategy:   fixed upstream revision + verified local OpenVINO conversion
Publication scope/date:   authorized for the 2026-08-31 competition deadline
```

许可证依据见 [license-decision.md](license-decision.md)，第三方边界见
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。不得猜测身份、版权主体、URL 或 ModelScope owner。

元数据已关闭的项目与剩余 preflight：

- `meta.json.icon` 已指向 rc.5 不可变 tag 下可匿名访问的 PNG；未把 `icon` 添加到 `info.json`。
- Windows 实测 OpenVINO analyze 进程树工作集峰值为 `0.702 GiB`，`mem_need_gb` 向上配置为
  `1.0`；方法、范围与限制见 [release-metadata.md](release-metadata.md)。
- `server_alive_timeout` 已改为官方明确的默认值 `300`。Airlock v0.1 是短生命周期 client，
  不声称存在常驻 server。
- `info.json.models=[]` 是否被平台接受尚未确认。AI Airlock 当前实际方案是固定 Hugging Face revision、
  逐文件校验、本地转换 OpenVINO IR；若改为平台托管，必须先有公开 `model_id`、固定 revision、
  `dir_name`、含核心 `.xml/.bin` 的 `required_files`、转换物 SHA-256、来源归属与再分发授权。
- `info.json` 中非模板的 `name`、`version`、`stage`、`inference_mode` 已移除，降低 parser 歧义。
- OpenVINO 文件规范给出的 Skill 目录命名约定为 `local-<function>`，官方 `meta.json` 模板也把 `name`
  写为 `local-<skill-name>`；当前 `SKILL.md.name`、Python package、`meta.json.name` 与 `info.json.name`
  标识为 `ai-airlock`；公开源码仓库和用户确认的不可变 ModelScope `skill_name` 也使用
  `ai-airlock`。TraeCode 官方名称约束允许该形式；真实自动发现仍需登录后验证。
- OpenVINO 文件规范要求 `SKILL.md` 正文包含 `Usage`、Examples 表、`--continue` resume protocol、输出
  解释、失败处理，以及“不直调其他脚本 / 首次下载耗时 / 不支持平台报错 / 无云端 fallback”等重要说明。
  `SKILL.md` 现已包含 Usage、Examples、输出/失败解释、unsupported-platform/no-cloud-fallback
  以及与短生命周期 wrapper 对齐的“重复同一命令”resume 语义；不伪造未实现的 `--continue`。
  文档兼容已关闭，真实 TraeCode 自动发现与调用仍必须实跑。

## 3. 从受控文件构建发布包

以下步骤在用户批准的 candidate commit 与不可变 tag 创建后执行。commit 哈希不能安全地自写入同一个
commit，因此由 tag 解析，并在外部 handoff prompt 与 post-push 验证记录中固化。

### 3.1 冻结 allowlist

从 release commit 的 Git tree 构建，不从工作目录、ignored 文件或 glob 全盘打包。审核后的显式
allowlist 至少包含：

```text
.qoderignore
STATUS.md
README.md
SKILL.md
LICENSE
THIRD_PARTY_NOTICES.md
meta.json
info.json
pyproject.toml
requirements.txt
src/
scripts/
config/
demo/
tests/
benchmark/README.md
benchmark/run_benchmark.py
benchmark/variants.json
benchmark/datasets/
assets/competition/
docs/architecture.md
docs/claims-ledger.md
docs/competition-story.md
docs/demo-script.md
docs/license-decision.md
docs/modelscope-article.md
docs/modelscope-submission-fields.md
docs/publication-runbook.md
docs/qoder_acceptance.md
docs/release-evidence.md
docs/release-metadata.md
docs/submission-checklist.md
docs/threat-model.md
docs/trae-acceptance.md
docs/windows-validation-handoff.md
docs/windows-validation-report-template.md
```

`PROJECT_SPEC.md` 是历史设计草案；`docs/final-integrator-report.md`、
`docs/relevance-closure-report.md` 是内部历史审计。三者都不进入公开 Skill 包。若 README 或其他入包
文档链接到被排除文件，必须先修正链接。

### 3.2 生成 archive

在 packaging identity 的 clean detached checkout 中设置未来真实值，并逐项核对。`PACKAGING_REF` 必须是
完整 commit SHA 或新的 immutable packaging tag，不得使用 floating `main`，也不得设为
`v0.1.0-rc.5`（该 tag 内仍是验证前文档）：

```bash
set -euo pipefail
CANDIDATE_COMMIT="$(git rev-list -n 1 v0.1.0-rc.5)"
: "${PACKAGING_REF:?set PACKAGING_REF to the reviewed post-tag commit or immutable packaging tag}"
RELEASE_COMMIT="$(git rev-parse "${PACKAGING_REF}^{commit}")"
PACKAGE_OUT="$(mktemp -d)"
ARCHIVE="$PACKAGE_OUT/ai-airlock-skill.zip"

git diff --quiet
git diff --cached --quiet
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git rev-parse HEAD)" = "$RELEASE_COMMIT"
test "$RELEASE_COMMIT" != "$CANDIDATE_COMMIT"
git merge-base --is-ancestor "$CANDIDATE_COMMIT" "$RELEASE_COMMIT"
git cat-file -e "${RELEASE_COMMIT}^{commit}"
git diff --exit-code "$CANDIDATE_COMMIT" "$RELEASE_COMMIT" -- \
  .qoderignore SKILL.md LICENSE THIRD_PARTY_NOTICES.md \
  meta.json info.json pyproject.toml requirements.txt \
  src scripts config demo tests \
  benchmark/README.md benchmark/run_benchmark.py benchmark/variants.json benchmark/datasets \
  assets/competition
git archive --format=zip --output="$ARCHIVE" "$RELEASE_COMMIT" -- \
  .qoderignore STATUS.md README.md SKILL.md LICENSE THIRD_PARTY_NOTICES.md \
  meta.json info.json pyproject.toml requirements.txt \
  src scripts config demo tests \
  benchmark/README.md benchmark/run_benchmark.py benchmark/variants.json benchmark/datasets \
  assets/competition \
  docs/architecture.md docs/claims-ledger.md docs/competition-story.md docs/demo-script.md \
  docs/license-decision.md docs/modelscope-article.md docs/modelscope-submission-fields.md \
  docs/publication-runbook.md docs/qoder_acceptance.md docs/release-evidence.md \
  docs/submission-checklist.md docs/threat-model.md \
  docs/windows-validation-handoff.md docs/windows-validation-report-template.md
```

`git archive` 只读取 packaging commit 中已跟踪且在 allowlist 内的对象。上面的 scoped `git diff` 必须
证明 runtime、policy、tests、metadata 与 assets 和 rc.5 candidate 完全相同；若不同，停止并形成新的
候选/证据，不能把代码变化伪装成文档包装。任何仍未提交的包装文件都会缺失，因此必须检查 archive
清单，不能从当前 dirty working tree 补拷。最终 manifest 同时记录 packaging commit/tree 和 rc.5 tag
object/commit/tree。

### 3.3 archive denylist 与结构检查

发布包必须排除：`.venv*`、`models/`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/`、`*.egg-info/`、
`benchmark/results/`、本机 `.release-evidence/`、下载 cache、编辑器状态、未审计日志、临时录屏和其他
Git-ignored 内容。`demo/incident/payment-service.log` 与 `demo/incident/production.log` 是 allowlist 中
明确审核的合成演示输入；除这两项外，archive 内不得出现其他 `.log`。

```bash
MEMBERS="$PACKAGE_OUT/archive-members.txt"
zipinfo -1 "$ARCHIVE" > "$MEMBERS"
test "$(awk '$0 == "SKILL.md" {n++} END {print n+0}' "$MEMBERS")" -eq 1
test "$(awk '/(^|\/)SKILL\.md$/ {n++} END {print n+0}' "$MEMBERS")" -eq 1

if rg -i '(^|/)(\.venv[^/]*|models|__pycache__|\.pytest_cache|\.ruff_cache|[^/]+\.egg-info|benchmark/results|\.release-evidence|cache)(/|$)' "$MEMBERS"; then
  exit 1
fi

if rg '\.log$' "$MEMBERS" | rg -v '^(demo/incident/payment-service\.log|demo/incident/production\.log)$'; then
  exit 1
fi

test "$(wc -c < "$ARCHIVE")" -le 5242880
```

5 MB 检查是当前 CLI 规范 gate；若实际走 API，仍保留该检查，直到登录态确认新的精确上限。

## 4. 全新解压目录复验

不得在开发工作区直接把“本机能跑”当成发布包证据。每个候选 archive 都必须解压到新的临时目录：

```bash
QA_BASE="$(mktemp -d)"
QA_ROOT="$QA_BASE/package"
mkdir "$QA_ROOT"
unzip -q "$ARCHIVE" -d "$QA_ROOT"
cd "$QA_ROOT"
```

依次完成并保存日志：

1. 解析 `meta.json`、`info.json`、所有入包 JSON；验证所有 SVG XML。
2. 检查 Markdown 内部链接、图片链接和锚点；禁止依赖开发工作区外文件。
3. 对解压后的文件做 Secret、本机绝对路径、用户名、账号、远端 host 与个人信息扫描。
4. 创建位于 `QA_BASE`、不写入包内容的全新 Python 3.12 venv，安装 package；先跑 deterministic
   `health --json`、正向/负向触发、flagship 和错误路径。
5. 安装 `.[dev,openvino]`，按固定 revision 准备模型；模型与下载 cache 仅用于 QA scratch，不进入
   archive。跑 OpenVINO `health --json`、full pytest、flagship、benchmark 与 response gate。
6. 重新运行 `git diff --check` 等价的 whitespace 检查、所有 SVG 的 ImageMagick 栅格化和 PNG 解码。
7. 确认代码、文档、测试三类均存在；确认 `SKILL.md`、`scripts/run.ps1`、`src/`、`tests/` 不缺失。

在运行会生成 cache/model 的 QA 之前，先为原始解压内容生成 per-file manifest；archive 自身另存
SHA-256：

```bash
cd "$QA_ROOT"
find . -type f -exec shasum -a 256 {} \; | LC_ALL=C sort -k 2 > "$QA_BASE/package-contents.sha256"
cd "$QA_BASE"
shasum -a 256 "$ARCHIVE" > "$ARCHIVE.sha256"
shasum -a 256 package-contents.sha256 > package-contents.sha256.sha256
```

复验失败即废弃该 archive，回到源 commit 修复并重新生成；不得在 zip 内手工替换单个文件。

## 5. 公开 evidence 方案

本机 `.release-evidence/...` 是私有构建输入，不是公众可访问的证据 URL。未来必须生成脱敏 evidence
bundle，并作为 source release asset 或独立公开制品发布。公开 index 至少记录：

```text
public_evidence_url:
evidence_bundle_sha256:
core_commit: 495f89c6349afbdd741576439b3b85369d26671a
release_commit:
release_archive_sha256:
package_contents_manifest_sha256:
benchmark_run_id:
benchmark_json_sha256:
redaction_review:
anonymous_download_verified_at:
```

公开前再次扫描 evidence，移除本机路径、用户名、cache 位置、原始 Secret/PII/Injection 文本和未经
授权的日志；不得删除 claim 所需的环境、样本范围、commit、run ID、输出面与限制条件。

上传后必须在未登录/无缓存环境下载公开 bundle，复核 bundle SHA-256 和内部 manifest，并确认 URL
无需作者账号权限。URL、bundle SHA、core commit 和 release commit 四项必须同时进入公开索引。

## 6. Windows / Qoder evidence 插入门

rc.3 已产生正式 Windows `FAIL`，不能再写成“从未运行”，也不能剪辑成 PASS。rc.4 annotated、unsigned
tag 已发布并完成 exact-SHA CI：[main run `33293985019`](https://github.com/tty627/ai-airlock/actions/runs/33293985019)
与 [tag run `33294040300`](https://github.com/tty627/ai-airlock/actions/runs/33294040300) 的 Windows/Ubuntu
四个 Python 3.12 job 各为 `212 passed / 8 skipped`，Ruff、format、benchmark smoke 通过；8 个 skip 均为
prepared OpenVINO model/runtime unavailable。CI 未安装/运行 `.[openvino]`、真实模型 bootstrap、
`scripts/run.ps1`、Qoder 或 Intel performance，因此只算 scoped Python evidence。

rc.4 fresh-tag 回传结果必须拆分记录：

- `PASS_REGRESSION_SUBSET`：PowerShell 5.1/7 各自 cold + warm health、中文 task + 带空格路径 analyze、
  固定 invalid/missing errors、cross-shell concurrent cold、covered cases residual process count `0`；
- `PASS_WITH_SCOPE`：`252` markers × `26` stdout/stderr surfaces 为 `0 hits`，不得外推为无范围“零泄漏”；
- `FAIL`（rc.4 orphan-pipe）：`32.164s`、exit `2`、stdout `0`、单一 `AIRLOCK_INVALID_JSON`，external
  cleanup 前/后 residual `1/0`；因此 rc.4 Windows candidate 与 overall 均为 `FAIL`；
- `NOT_RUN`：empty source-cache 与 remaining timeout/fault cases；Qoder（host 缺席）和 Intel
  performance 也分别为 `NOT_RUN`；
- `NOT_MEASURED`：cold-bootstrap/task-period network；这些未知项不是 rc.4 FAIL 的原因。

外置脱敏报告没有 public URL；其记录的 manifest 校验为 `99/99`，顶层 `SHA256SUMS` 文件的 SHA-256 为
`3f0a17919118a858a29724752b5e68807b15a7ebadddbfdd9d81fa521ef29f3b`。在匿名发布并复验前，公众不能
独立下载该报告。后续 failure bundle 与早期 subset bundle 分离：manifest `29/29`，顶层
`SHA256SUMS` 文件 SHA-256 为
`00b336f9193ba3fd4bad4aa3df157d5d08132c46e64c6ae3d4418c05dca5677a`，同样无 public URL。

rc.5 annotated、unsigned tag 已发布；tag object
`7d4034f9e8575658190dacef53f9ba749de8ed6c`，commit
`9abf825943f8f68f2bc6cd3afc1baa8717e0c01a`，tree
`88b914598de60fa385820860b13dc8bd6db26b7d`。exact-SHA [main run
`33298393856`](https://github.com/tty627/ai-airlock/actions/runs/33298393856) 与 [tag run
`33298491017`](https://github.com/tty627/ai-airlock/actions/runs/33298491017) 均通过：Windows 各
`225 passed / 8 skipped`，Ubuntu 各 `213 passed / 14 skipped`，Ruff、format、benchmark smoke 通过。

rc.5 exact-tag external Windows scoped evidence 必须拆分记录：

- `PASS`：PowerShell 5.1/7 orphan-pipe faults 分别为 `3.352s / 3.937s`、固定
  `AIRLOCK_INVALID_JSON`、residual `0`、`cleanup_performed=false`；
- `PASS_WITH_SCOPE`：两壳 health、post-fault health 与中文/空格路径 analyze controls；
- `NOT_RUN`：empty source-cache、remaining external faults、Qoder 与 Intel performance；
- `NOT_MEASURED`：network；
- `INCONCLUSIVE`：rc.5 full Windows/candidate acceptance，不得写成 complete matrix PASS。

rc.5 外置 bundle 也没有 public URL；manifest `55/55`，顶层 `SHA256SUMS` 文件 SHA-256 为
`107ae4a8954e0a7965a48e3b9248b74789850e1a2b6793ac422a4d7b62cc82bb`。仍需完成的 Qoder 证据包括
自动发现、12+12 triggers、首次内容访问 non-bypass、Capsule-only 最终回答、`source:local_ref` 与未经
剪辑 trajectory。

按 [qoder_acceptance.md](qoder_acceptance.md) 执行，先判断 `PASS / FAIL / INCONCLUSIVE`。无法证明
non-bypass 时只能是 `INCONCLUSIVE`。新数字先进入 [Claims Ledger](claims-ledger.md)，绑定新的
commit/evidence/environment，再替换文章与视频占位。Mac CLI rehearsal 永远不能写成 Qoder Task
Completed。

exact rc.4 tag CI 与早期 fresh-tag Windows functional subset 已存在，但后续 required fault 已决定 rc.4
candidate `FAIL`。exact rc.5 关闭了该 orphan-pipe defect，但 source-artifact cache、网络、remaining
faults 和 host non-bypass 的未知状态仍须随每次引用保留；Intel CPU 被识别不等于 Intel inference 或
性能已通过。

## 7. 文章、视频与表单

1. 从 [modelscope-article.md](modelscope-article.md) 生成文章发布稿，并强制添加专题标签
   `Intel AI PC`；正文仍保留 Intel evidence `NOT RUN`。
2. 从 [modelscope-submission-fields.md](modelscope-submission-fields.md) 填写字段；Skill 强制添加自定义
   标签 `AI PC`。
3. 按 [demo-script.md](demo-script.md) 制作视频。Mac 镜头标 `not Windows/Qoder`；Windows/Qoder
   镜头只能来自真实连续会话。
4. 所有 benchmark 画面保留 `Synthetic benchmark · Apple M4 CPU · v0.1.0-rc.1`，并同时展示
   Mean Recall@K、estimated-token context reduction 与 P95 latency。
5. 仅在托管真实完成后填写 repository、Skill、article、video、icon 与 public evidence URL。
6. 登录态重新核对表单必填、字数、格式、截止时间和标签；保存真实页面截图/回执，但本轮不执行。

## 8. 未来发布顺序与发布后复验

仅在用户确认第 2 节所需身份与范围、并明确授权相应外部动作后：

1. 创建/确认公开 source repository，应用用户批准的 LICENSE、author、version；跑远端 CI。
2. 上传受控 archive，创建 ModelScope Skill；记录上传 archive SHA、owner、skill_name、category、license、
   tags、source URL 和返回的真实 Skill URL。
3. 发布脱敏 evidence、文章与视频；匿名复核全部 URL 和 checksum。
4. 提交比赛表单并保存真实作品 ID、时间戳与成功回执。

平台发布后必须从 ModelScope 重新下载**平台实际提供的 Skill 包**，不能复用本地 archive：

1. 记录下载 URL、时间与平台包 SHA-256；若平台重新打包导致 archive hash 与上传包不同，同时保留
   两个 hash，并用 per-file manifest 核对内容差异。
2. 解压到新的临时目录，确认 denylist、唯一根级 `SKILL.md`、代码/文档/测试齐全。
3. 在新的 Python 环境从下载包安装。
4. 至少重跑 deterministic 与 OpenVINO health、一个正向 trigger、一个负向 non-trigger、flagship、
   参数错误/无权限/模型不可用等错误路径；保存 exit code、stdout/stderr schema 和 checksum。
5. 若平台包、安装或复验与本地候选不一致，立即停止文章/比赛提交并修复，不把本地 PASS 冒充平台
   下载包 PASS。

## 9. 回滚与最终授权

- 数字错误：撤下或标记更正，定位 Claim ID 与源 JSON path。
- Secret/PII/路径泄露：停止传播，撤下资产并私下保留 incident record；不在公开 issue 复制泄漏。
- tag/source/evidence 不一致：停止发布，创建新 source identity 与完整 evidence，不修改旧 tag。
- Windows/Qoder 失败或 inconclusive：保留真实结果与 limitation，不剪辑成 PASS。
- URL 失效或需登录：修复托管后从未登录环境重新验证。

以下门槛只约束 ModelScope、研习社、视频、比赛表单和其他最终公开动作；用户已单独授权本轮 GitHub
rc.5 candidate commit、push 与不可变 tag。只有用户明确说“可以发布/提交”，且以下摘要全部处理后，
才允许执行这些最终公开动作：

```text
LICENSE / copyright / author confirmed   YES
Metadata blockers closed                 YES
AI PC Skill tag confirmed                YES
Intel AI PC article tag confirmed        YES
Controlled archive + manifests verified  YES
Public evidence anonymous check          YES
Public URLs verified                     YES
Remote CI verified                       YES
Windows full-matrix evidence             PASS
Qoder evidence                           PASS or explicitly accepted NOT_RUN limitation
Intel evidence                           PASS or explicitly accepted NOT_RUN limitation
Claims Ledger final review               YES
Secret / PII review                      YES
User publication authorization           YES
```

本轮状态：`GitHub rc.5 candidate publication = COMPLETE`；`RC5 overall = INCONCLUSIVE`；
`User final publication authorization = NO`。
