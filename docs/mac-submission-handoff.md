# macOS Submission Handoff · AI Airlock

> Use this page only if the Windows browser session is unavailable. It preserves the exact rc.7 runtime
> candidate and the current post-tag documentation on `main`. Never recreate, move or overwrite an existing
> `v0.1.0-rc.*` tag.

## 1. Restore the project on the Mac

```bash
git clone https://github.com/tty627/ai-airlock.git
cd ai-airlock
git fetch --tags --force
git checkout main
git pull --ff-only origin main
git rev-parse HEAD
```

The documentation checkout should be at or after commit
`0acb911661d4bb4cf8fca6b1066c9b66f519b76e`. The immutable runtime package remains bound to:

```text
tag:        v0.1.0-rc.7
tag object: 98c9dc9c7710a631b066415d2605d7b6bcbb0eba
commit:     9ec87e72843299779bf8788acf24e563aeff334e
tree:       430446f531e30dce6caff4af83359d49468d4a00
```

Verify the identity without changing it:

```bash
test "$(git rev-parse v0.1.0-rc.7)" = "98c9dc9c7710a631b066415d2605d7b6bcbb0eba"
test "$(git rev-parse 'v0.1.0-rc.7^{commit}')" = "9ec87e72843299779bf8788acf24e563aeff334e"
test "$(git rev-parse 'v0.1.0-rc.7^{tree}')" = "430446f531e30dce6caff4af83359d49468d4a00"
```

## 2. Download and verify the exact Skill archive

Download URL:

```text
https://github.com/tty627/ai-airlock/releases/download/v0.1.0-rc.7/ai-airlock-skill-9ec87e728432.zip
```

```bash
mkdir -p "$PWD/.submission-download"
curl --fail --location \
  --output "$PWD/.submission-download/ai-airlock-skill-9ec87e728432.zip" \
  'https://github.com/tty627/ai-airlock/releases/download/v0.1.0-rc.7/ai-airlock-skill-9ec87e728432.zip'
shasum -a 256 "$PWD/.submission-download/ai-airlock-skill-9ec87e728432.zip"
```

Required SHA-256:

```text
961a0f6b07637f5e404b8fac836886ca3a5419b3681d81898815fe434a97b0a1
```

The archive is `1,309,273` bytes, contains `140` entries, and contains exactly one root `SKILL.md`.

## 3. Publish the ModelScope Skill

Preferred web form:

```text
https://www.modelscope.cn/skills/create?template=custom
```

Use these exact values:

| Field | Value |
|---|---|
| Owner | `Ararag1` |
| English name | `ai-airlock` |
| Display name | `AI Airlock` |
| Source URL | `https://github.com/tty627/ai-airlock` |
| License | `Apache License 2.0` |
| Visibility | Public |
| Category | Developer tools / `developer-tools` |
| Custom tag | `AI PC` |
| File | the verified rc.7 zip above |
| Description | `在本地用 OpenVINO 先扫描并脱敏私有日志、配置和 CSV，再向生产力 Agent 提供可追溯的 Safe Context Capsule，支持 Windows Trae/Qoder 集成。` |

Before selecting **Create**, verify the uploaded filename, owner and immutable skill name. After creation, record
the resulting public URL; it should identify `@Ararag1/ai-airlock`. Do not guess the URL before the platform
returns it.

The official alternative is the two-step OpenAPI flow documented by ModelScope: upload the zip to
`POST /openapi/v1/files/upload` with `type=skill`, then pass the returned `data.id` as `skill_file` to
`POST /openapi/v1/skills`. Obtain the access token on the Mac and keep it out of shell history, files, chat and
screenshots. Do not paste the token into this repository.

## 4. Publish the ModelScope Learn article

Open:

```text
https://www.modelscope.cn/learn/create
```

Use:

- title: `AI Airlock：在 Intel PC 上给生产力 Agent 加一道本地上下文气闸`;
- author/byline: `谭天晔`;
- required topic tag: `Intel AI PC`;
- body source: [`modelscope-article-submission.md`](modelscope-article-submission.md).

Replace only `[PENDING_MODELSCOPE_SKILL_URL]` with the public Skill URL returned by ModelScope. Keep the
TraeCode limitation intact: the authenticated host trajectory is `NOT_RUN`; the CLI wrapper evidence is not a
host pass. Publish, then record the public article URL and verify it in a signed-out browser window.

## 5. Submit the competition form

Open:

```text
https://alidocs.dingtalk.com/notable/share/form/v01Q35O85pPVW83Al9V_dv19yqvsgs3oebp3pcjys_1qX0QQ0?source=link
```

Use the public work fields from
[`competition-submission-fields.md`](competition-submission-fields.md). Required public values include:

- author: `谭天晔`;
- work name: `AI Airlock：本地安全上下文气闸`;
- ModelScope Learn URL: the newly published article;
- ModelScope Skill URL: the newly created public Skill;
- Xiaohongshu URL: blank unless the user separately authorizes social posting.

The registrant must personally fill or confirm phone, organization/school, delivery address, WeChat, email,
business type, profession, acquisition source and the Intel/ModelScope customer-database consent. These values
must not be inferred from the repository or written back to it.

Before the final **Submit** action, confirm both public URLs load without authentication. After submission, save
the success page or receipt, submission time in Asia/Shanghai, and any returned entry identifier.

## 6. Final evidence checklist

- [ ] ModelScope Skill public URL works when signed out.
- [ ] Platform-provided Skill download installs with one root `SKILL.md` and expected package members.
- [ ] Article public URL works when signed out; images render; `Intel AI PC` is present.
- [ ] Article contains no placeholder and does not claim TraeCode host acceptance.
- [ ] Competition form success receipt is saved.
- [ ] GitHub `v0.1.0-rc.7` tag object, commit and tree remain unchanged.
- [ ] No access token or personal submission data was added to Git, terminal transcripts or screenshots.
