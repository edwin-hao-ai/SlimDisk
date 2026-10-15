# MacSlim → SlimDisk 重命名 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把产品从 `MacSlim` 全面改名成 `SlimDisk`，消除 App Store 5.2.5 拒审（应用名含 Apple 商标 "Mac"），并覆盖 app 仓库、官网仓库、GitHub 仓库三处。

**Architecture:** 纯重命名，无行为变更。唯一代码级例外是 `styles.css` 的深色修复（已单独提交 `d0dbfd8`，本计划不含）。改名分「名称映射」+「范围边界」两层；所有替换都要先按边界分类，**禁止全局无脑 sed**。

**Tech Stack:** Tauri v2 / Rust（crate `slimdisk`、bins `slimdisk`+`slimdisk-cli`）/ SolidJS 前端 / VGOAPP 官网（React + Vite）/ GitHub Pages（updater 端点）。

**Spec:** 本次会话决策 —— App Store 拒审原文（Guideline **5.2.5** 应用名含 "Mac"；**2.1a** 深色模式文本框不可见，已另修）；用户决策：新名 **SlimDisk**；CLI 一起改；官网目录名与产品名一起改；GitHub 仓库一起改；无存量用户，旧 updater 端点可直接弃用。

---

## Global Constraints

**名称映射（唯一权威表，全部任务据此执行）**

| 类别 | 旧 | 新 |
| :-- | :-- | :-- |
| 显示名 / 产品名（appName、productName、窗口标题、托盘、官网、i18n 文案） | `MacSlim` | `SlimDisk` |
| Rust package | `macslim` | `slimdisk` |
| Rust lib crate | `macslim_lib` | `slimdisk_lib` |
| Rust 主二进制 | `macslim` | `slimdisk` |
| Rust CLI 二进制 | `macslim-cli` | `slimdisk-cli` |
| npm package name | `macslim` | `slimdisk` |
| 数据目录（Application Support 下） | `MacSlim/` | `SlimDisk/` |
| 历史库文件 | `macslim.db` | `slimdisk.db` |
| localStorage key 前缀 | `macslim.*` | `slimdisk.*` |
| 临时废纸篓前缀 | `macslim-trash-` | `slimdisk-trash-` |
| updater 端点 | `…/edwin-hao-ai.github.io/MacSlim/updates/…` | `…/edwin-hao-ai.github.io/SlimDisk/updates/…` |
| release 资产名 | `MacSlim_<v>_<arch>.*` | `SlimDisk_<v>_<arch>.*` |
| `.app` / `dmg` 名 | `MacSlim.app` / `MacSlim_<v>_<arch>.dmg` | `SlimDisk.app` / `SlimDisk_<v>_<arch>.dmg` |
| GitHub 仓库 | `edwin-hao-ai/MacSlim` | `edwin-hao-ai/SlimDisk` |
| 官网路由目录 | `macslim/`、`/en/macslim/` | `slimdisk/`、`/en/slimdisk/` |
| 官网源文件 | `MacSlimPage.tsx` / `MacSlimPrivacyPage.tsx` / `macslimContent.ts` / `MacSlimIcon.tsx` / `macslim-main.tsx` / `macslim-privacy-main.tsx` | `SlimDisk*` 同名对应 |
| 官网下载目录 | `public/downloads/macslim/` | `public/downloads/slimdisk/` |
| 官网产品 id / i18n key | `macslim` | `slimdisk` |

**绝对不许改（误伤即破坏签名 / 数据 / 重复配置）**

- **Bundle ID**：`com.vgoapp.macslim` 保持不变（Apple 明确要求：改 bundle id 会导致无法升级）。→ 因此下列也保持原样：
  - 所有 `com.vgoapp.macslim` 字符串（含 `src-tauri/src/*_tests.rs`、`scripts/capture_story_pages.sh`、`scripts/create_mas_profile.py` 里的 `MAS_BUNDLE_ID` 默认值）
  - MAS 容器路径 `~/Library/Containers/com.vgoapp.macslim/Data`
- **本地签名/凭据产物名**（在 `~/.config/mddock/`、`~/.tauri/`、Keychain，重命名要重新签发/导入，零收益）：
  - Keychain profile `macslim-notary`（`scripts/release.sh` / `sign.sh` 的默认值）
  - updater 私钥路径 `~/.tauri/macslim-updater.key`
  - `~/.config/mddock/MacSlim_MAS.mobileprovision`、`MacSlim_MAS_*.p12/.csr/.pem`、`MacSlim_MAS_installer_*`
- **历史记录文档**（是记录，不是活文档）：`docs/HANDOFF-*.md`、`docs/superpowers/plans/2026-*.md`、`docs/superpowers/specs/2026-*.md`、`CHANGELOG.md` 里的历史条目。**不改**。
  - 例外：本计划自身（`docs/superpowers/plans/2026-10-15-*`）与新写内容可用新名。
- **本机发布脚本 env 变量名**（非用户可见，改名只增加测试联动、零收益，2026-10-15 决策**不改**）：`MACSlim_NOTARY_PROFILE`（`release.sh`/`sign.sh`）、`MACSlim_PUBLISH_PREFLIGHT_ONLY`（`publish-update.sh`）—— 变量名保持原样，脚本内其它资产名/URL/文案照常改。
- 遗留代号 `macflow` / `macflow-YYYYMMDD`（AGENTS §4.2 提到的历史名）：本次**不动**（非 app 名，不在拒审范围，独立清理）。

**验收铁律**

- 每个 Task 结束跑该 Task 指定的最小验证集，**退出 0** 才提交。
- 每个 Task 单独 commit + push（AGENTS §8.1）。
- 收尾全局校验：全仓库（除上列白名单）不再有 `MacSlim` / `macslim`（bundle id / 本地凭据 / 历史文档除外）。

**Review Focus**（改名最容易漏、漏了会咬人的五处）

1. **大小写混拼的 env 变量**：`MACSlim_PUBLISH_PREFLIGHT_ONLY`（`publish-update.sh:204`）、`MACSlim_NOTARY_PROFILE`（`release.sh:15`、`sign.sh:15`）—— 这些是**故意保留**的本机变量（见 Global Constraints），盲替换会误伤。
2. **文件名/路径里的 `macslim`**：`macslim` 目录、`macslimContent.ts`、`macslim-main.tsx`、`public/downloads/macslim/` —— 只改文件内容不改文件/目录名 = 半拉子。
3. **测试断言里的旧名**：Rust `*_tests.rs`、Python `scripts/tests/*`、vitest 里断言旧字符串的用例，改名后必须同步，否则 CI 红。
4. **updater 端点**：必须与仓库新名一致，否则新版自更新永远 404（AGENTS §9 踩过一次）。
5. **官网路由**：`vite.config.ts` 的 input key、`public/downloads/macslim/`、`src/i18n` 的 `t.macslim.*`、`Footer.tsx`/`products.ts` 的 `/macslim/` 链接 —— 漏一处就是死链。

---

## Task 1: Rust crate / 二进制重命名

**Files:**
- Modify: `src-tauri/Cargo.toml`（`name`、`default-run`、`[lib] name`、两个 `[[bin]] name`、`description`）
- Modify: `src-tauri/src/main.rs`（`macslim_lib::run()` → `slimdisk_lib::run()`）
- Modify: `src-tauri/src/bin/cli.rs`（所有 `use macslim_lib::…` → `slimdisk_lib::…`；文件头注释里的 `macslim-cli` 示例）
- Modify: `src-tauri/tests/process_boundary.rs`（`use macslim_lib::…`）
- Modify: `scripts/operation_surface_checks.py`（`\bmacslim_lib\b` 正则与提示文案）
- Test: 复用现有 Rust 测试

**Interfaces:**
- Produces: crate `slimdisk`、lib `slimdisk_lib`、bins `slimdisk` / `slimdisk-cli`；后续 Task 4/5 脚本据此引用二进制名。

- [ ] **Step 1: 改 `Cargo.toml`**：`name = "slimdisk"`、`default-run = "slimdisk"`、`[lib] name = "slimdisk_lib"`、`[[bin]] name = "slimdisk"` / `"slimdisk-cli"`、`description = "SlimDisk - Mac developer and user system maintenance tool"`。
- [ ] **Step 2: 改 `main.rs` / `bin/cli.rs` / `tests/process_boundary.rs`** 里的 `macslim_lib` → `slimdisk_lib`（`cli.rs` 头部 `macslim-cli --…` 示例同步为 `slimdisk-cli`）。
- [ ] **Step 3: 改 `scripts/operation_surface_checks.py`** 的正则与报错文案 `macslim_lib` → `slimdisk_lib`。
- [ ] **Step 4: 验证**
  Run: `cargo test --manifest-path src-tauri/Cargo.toml --all-targets`
  Expected: PASS（0 failed）
- [ ] **Step 5: 提交**
  `git add -A && git commit -m "refactor: Rust crate/bin 重命名 macslim→slimdisk（App Store 5.2.5 去 Mac 商标）"`

## Task 2: Tauri 配置与 macOS 元数据

**Files:**
- Modify: `src-tauri/tauri.conf.json`（`productName`、`app.windows[0].title`、`bundle.longDescription`、updater endpoint URL）
- Modify: `src-tauri/Info.plist`（`MacSlim` → `SlimDisk`）
- Modify: `src-tauri/PrivacyInfo.xcprivacy`（注释内 `MacSlim`）
- Modify: `src-tauri/capabilities/default.json`（`description`）

**Interfaces:**
- Consumes: Task 1 的 `productName = "SlimDisk"` 决定打包出的 `SlimDisk.app` / dmg 名。
- Produces: updater 端点 `https://edwin-hao-ai.github.io/SlimDisk/updates/latest.json`（Task 6 据此写 `docs/updates/latest.json`）。

- [ ] **Step 1:** `productName:"SlimDisk"`、窗口 `title:"SlimDisk"`、`longDescription` 首词改 `SlimDisk`；`identifier` **保持** `com.vgoapp.macslim`。
- [ ] **Step 2:** updater `endpoints[0]` → `https://edwin-hao-ai.github.io/SlimDisk/updates/latest.json`。
- [ ] **Step 3:** `Info.plist` / `PrivacyInfo.xcprivacy` / `capabilities/default.json` 的用户可见 `MacSlim` → `SlimDisk`。
- [ ] **Step 4: 验证**
  Run: `grep -rn 'MacSlim' src-tauri/tauri.conf.json src-tauri/Info.plist src-tauri/PrivacyInfo.xcprivacy src-tauri/capabilities/default.json`
  Expected: 无输出；且 `grep -n identifiers src-tauri/tauri.conf.json` 仍是 `com.vgoapp.macslim`
- [ ] **Step 5: 提交**

## Task 3: Rust 运行时用户可见字符串

**Files:**
- Modify: `src-tauri/src/tray.rs`（`打开/退出/关于 MacSlim`、tooltip、菜单栏状态串）
- Modify: `src-tauri/src/whitelist.rs`（内置白名单里的 `"macslim"`/`"MacSlim"` → `"slimdisk"`/`"SlimDisk"`）
- Modify: `src-tauri/src/storage.rs:309`（`base.join("MacSlim").join("macslim.db")` → `"SlimDisk"` / `"slimdisk.db"`）
- Modify: `src-tauri/src/cache_cleaner.rs:672`（`macslim-trash-` → `slimdisk-trash-`；含注释里的 `[macslim]`）
- Modify: `src-tauri/src/process_ops.rs:179`（提示文案 `MacSlim`）
- Modify: `src-tauri/src/lib.rs:595`（注释，可选）
- Test: Rust 测试

**Interfaces:**
- Produces: 托盘菜单 / 白名单 / 数据目录均用新名；`slimdisk.db` 路由此确定。

- [ ] **Step 1:** `tray.rs` 全部用户可见 `MacSlim` → `SlimDisk`（`open/quit/about_prefix`、`tooltip`、状态串）。
- [ ] **Step 2:** `whitelist.rs` 内置自保白名单项改 `slimdisk` / `SlimDisk`。
- [ ] **Step 3:** `storage.rs` 数据目录与库文件名改 `SlimDisk` / `slimdisk.db`。
- [ ] **Step 4:** `cache_cleaner.rs` 废纸篓前缀改 `slimdisk-trash-`；`process_ops.rs` 文案改 `SlimDisk`。
- [ ] **Step 5: 验证**
  Run: `cargo test --manifest-path src-tauri/Cargo.toml --all-targets`
  Expected: PASS
- [ ] **Step 6: 提交**

## Task 4: 前端（SolidJS）

**Files:**
- Modify: `index.html`（`<title>`）
- Modify: `src/i18n/zh-CN.ts`、`src/i18n/en.ts`（`appName`、`health/cleanup/notify/permission/autostart/updates/about` 等处 `MacSlim`；`aboutDb`/`aboutCli` 路径示例）
- Modify: `src/i18n/index.tsx:18`（`STORAGE_KEY`）、`src/views/ScanView.tsx:38`、`src/views/SettingsView.tsx:25`、`src/views/CacheView.tsx:58`、`src/lib/cleanFeedback.ts:11`（`macslim.*` localStorage key）
- Modify: `src/views/ScanView.test.tsx`、`src/i18n/error-i18n.test.ts`（断言旧名同步）

**Interfaces:**
- Produces: 界面语言资源 `appName = "SlimDisk"`；localStorage 前缀 `slimdisk.*`。

- [ ] **Step 1:** `index.html` 标题 → `SlimDisk`。
- [ ] **Step 2:** `zh-CN.ts` / `en.ts` 用户可见 `MacSlim` → `SlimDisk`；`aboutDb` → `~/Library/Application Support/SlimDisk/slimdisk.db`；`aboutCli` → `…/slimdisk-cli`。
- [ ] **Step 3:** `macslim.*` localStorage key → `slimdisk.*`（含 `index.tsx`、`ScanView.tsx`、`SettingsView.tsx`、`CacheView.tsx`、`cleanFeedback.ts`）。
- [ ] **Step 4:** 同步两处测试里的旧名断言。
- [ ] **Step 5: 验证**
  Run: `bun run test`
  Expected: 275 passed（数字随改名后新增/不变）
- [ ] **Step 6: 提交**

## Task 5: 发布 / 签名 / 打包脚本 + CI

**Files:**
- Modify: `scripts/release.sh`、`scripts/sign.sh`（`APP_PATH`/`DMG_PATH`/`UPDATER_PATH` 的 `MacSlim.app`、`MacSlim_${VERSION}_${ARCH}.dmg`、`.app.tar.gz`；`MACSlim_NOTARY_PROFILE` 变量名**保持**）
- Modify: `scripts/publish-update.sh`（资产名 `MacSlim_…`、`MacSlim.app.tar.gz`、`…/MacSlim/releases/…`、`…/MacSlim` Pages URL、提示语；`MACSlim_PUBLISH_PREFLIGHT_ONLY` 变量名**保持**）
- Modify: `scripts/publish_assets.py`（`prefix`）
- Modify: `scripts/verify-security-config.py`（`MacSlim_…` 资产名断言与 `MacSlim.app.tar.gz` 正则）
- Modify: `scripts/capture_story_pages.sh`、`scripts/capture_mas_screenshots.sh`、`scripts/_prepare_shot_app.sh`、`scripts/create_screenshot_dev_profile.py`、`scripts/create_mas_installer_cert.py`、`scripts/e2e_gui.py`、`scripts/e2e_registry.py`、`scripts/annotate_screenshots.py`（`MacSlim.app`/`MacSlimShot.app`/`MacSlimE2E-*`/文案）
- Modify: `.github/workflows/ci.yml`（artifact 名 `macslim-arm64-unsigned`）
- Modify: `scripts/tests/*.py`（断言旧名同步）
- Keep: `MAC_APP_DEVELOPMENT`/`MacSlim_MAS.mobileprovision`/`macslim-notary` 等本地凭据名

**Interfaces:**
- Consumes: Task 1 的二进制名、Task 2 的产物名。
- Produces: `SlimDisk.app.tar.gz`/dmg 资产名；`SLIMDISK_NOTARY_PROFILE`。

- [ ] **Step 1:** `release.sh` / `sign.sh` 产物路径改新；`MACSlim_NOTARY_PROFILE` 变量名**保持不动**，默认 `macslim-notary` 也保持。
- [ ] **Step 2:** `publish-update.sh` 资产名 / Pages&release URL / 提示语全改；`MACSlim_PUBLISH_PREFLIGHT_ONLY` 变量名**保持不动**。
- [ ] **Step 3:** `publish_assets.py`、`verify-security-config.py` 同步。
- [ ] **Step 4:** 截图 / e2e / MAS 脚本的用户可见名与临时包名同步（`MacSlimShot.app` → `SlimDiskShot.app` 等）。
- [ ] **Step 5:** `ci.yml` artifact 名、`bash -n` 关注的脚本保持可解析。
- [ ] **Step 6:** 同步 `scripts/tests/*` 断言。
- [ ] **Step 7: 验证**
  Run: `bash -n scripts/release.sh scripts/sign.sh scripts/publish-update.sh && bun run security:check && bun run test:python`
  Expected: 全部通过；`security:check` 退出 0
- [ ] **Step 8: 提交**

## Task 6: updater 清单与用户可见文档

**Files:**
- Modify: `docs/updates/latest.json`、`docs/updates/darwin-aarch64/*.json`（`url` 指向新 release；`notes` 里的名）
- Modify: `docs/index.html`（GitHub Pages 首页跳转目标 `/macslim/` → `/slimdisk/`）
- Modify: `README.md`、`docs/INSTALL.md`、`docs/privacy.html`、`docs/support.html`、`docs/release-plan.md`、`docs/release-identity-and-asc.md`、`docs/dual-release-decision.md`、`docs/mas-capability-matrix.md`、`docs/mas-sandbox-findings.md`、`VIDEO_SCRIPT.md`（用户/贡献者可见名）
- Modify: `.gitignore`（注释里的端点 URL）
- **不改**: `CHANGELOG.md` 历史条目、`docs/HANDOFF-*`、`docs/superpowers/plans|specs/2026-*`

**Interfaces:**
- Consumes: Task 2 的端点 URL、Task 8 的仓库名。
- Produces: 对外文档统一 `SlimDisk`。

- [ ] **Step 1:** `docs/updates/*.json` 的 release `url` 换成 `…/SlimDisk/releases/…`（资产名同步 `SlimDisk_…`）。
- [ ] **Step 2:** `docs/index.html` 跳转目标改 `/slimdisk/`。
- [ ] **Step 3:** 上列用户可见文档里的 `MacSlim` → `SlimDisk`（历史文档跳过）。
- [ ] **Step 4: 验证**
  Run: `rg -i 'macslim' docs/updates docs/index.html README.md docs/INSTALL.md docs/privacy.html docs/support.html VIDEO_SCRIPT.md`
  Expected: 无输出
- [ ] **Step 5: 提交**

## Task 7: VGOAPP 官网重命名（另一个仓库）

**Files（仓库 `/Users/edwinhao/VGOAPP`）:**
- Rename: `macslim/` → `slimdisk/`（含 `privacy/`）
- Rename: `src/pages/MacSlimPage.tsx` → `SlimDiskPage.tsx`、`src/pages/MacSlimPrivacyPage.tsx` → `SlimDiskPrivacyPage.tsx`
- Rename: `src/i18n/macslimContent.ts` → `slimdiskContent.ts`
- Rename: `src/components/icons/MacSlimIcon.tsx` → `SlimDiskIcon.tsx`
- Rename: `src/macslim-main.tsx` → `slimdisk-main.tsx`、`src/macslim-privacy-main.tsx` → `slimdisk-privacy-main.tsx`
- Rename: `public/downloads/macslim/` → `public/downloads/slimdisk/`
- Modify: `vite.config.ts`（input key `macslim`/`macslimPrivacy` 与路径）
- Modify: `src/data/products.ts`（`id/t.macslim/link '/macslim/'`、icon import）
- Modify: `src/components/Footer.tsx`（`MacSlim`/`/macslim/`）
- Modify: `src/i18n/translations.ts`、`src/pages`、`src/components` 内 `macslim` 引用
- Modify: `scripts/i18n-routes.py`、`scripts/prerender.sh`、`scripts/deploy.sh`（路由清单 / 路径）
- Modify: `index.html`、`docs/`（如站点内引用）

**Interfaces:**
- Consumes: Task 6 里新官网路由 `/slimdisk/`。
- Produces: 官网路由 `/slimdisk/`、`/en/slimdisk/`、`/slimdisk/privacy/`。

- [ ] **Step 1:** `git mv` 全部文件/目录改名（保留 git 历史）。
- [ ] **Step 2:** `vite.config.ts` 的 input key 与路径、`products.ts`、`Footer.tsx`、`i18n` key（`t.macslim.*` → `t.slimdisk.*`）、页面内文案。
- [ ] **Step 3:** `scripts/i18n-routes.py` / `prerender.sh` / `deploy.sh` 的路由与路径清单。
- [ ] **Step 4: 验证**
  Run: `npm run build`
  Expected: 构建成功；`dist/slimdisk/`、`dist/en/slimdisk/` 生成，且 `dist/macslim/` 不再生成
- [ ] **Step 5:** 部署（`scripts/deploy.sh`，注意 AGENTS §9 的 `VGOAPP_SSH_BIND` 绕 TUN）。
- [ ] **Step 6: 提交 + push**

## Task 8: GitHub 仓库改名

**Files:**
- 本地 remote、`tauri.conf.json` 端点（与 Task 2 一致，勿回退）

**Interfaces:**
- Consumes: Task 2/5/6 已写入新 URL。
- Produces: 仓库地址 `edwin-hao-ai/SlimDisk`。

- [ ] **Step 1:** `gh repo rename SlimDisk --repo edwin-hao-ai/MacSlim`（会更新 Pages URL 与旧链接 301）。
- [ ] **Step 2:** 更新本地 remote：`git remote set-url origin https://github.com/edwin-hao-ai/SlimDisk.git`。
- [ ] **Step 3:** 确认 `https://edwin-hao-ai.github.io/SlimDisk/updates/latest.json` 可访问（Pages 重建需 1–2 分钟）。
- [ ] **Step 4: 验证**
  Run: `git remote -v && curl -fsS https://edwin-hao-ai.github.io/SlimDisk/updates/latest.json | head`
  Expected: remote 指向 SlimDisk；JSON 正常返回
- [ ] **Step 5: 提交（如 remote/.gitignore 有变更）+ push**

## Task 9: 版本号与重新提审（发布动作，最后做）

**Files:**
- Modify: `package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml`（版本号 bump，如 `1.0.1` → `1.0.2`）
- 使用: `scripts/publish_mas_metadata.py`（ASC 应用名改 SlimDisk）、`scripts/release-mas.sh`、AGENTS §8.5 打包命令

- [ ] **Step 1:** 三处版本号同步 bump。
- [ ] **Step 2:** 用 AGENTS §8.5 的签名+公证命令重新打包 MAS 构建。
- [ ] **Step 3:** 经 ASC API 更新 App Info 名称 → 上传新构建 → 挂版本 → 写 Review Notes → 新建提审单（AGENTS §9 的 `DEVELOPER_REJECTED` 需新单）。
- [ ] **Step 4: 验证**：ASC 版本 state 回到 `WAITING_FOR_REVIEW`。
- [ ] **Step 5: 提交 + push**

---

## 收尾全局校验（全部 Task 完成后）

- [ ] `rg -i 'macslim' --hidden -g '!node_modules' -g '!.git' -g '!target' -g '!dist'` 的命中，**只应剩**：bundle id `com.vgoapp.macslim`、本地凭据名（`macslim-notary`/`macslim-updater.key`/`MacSlim_MAS.*`）、历史文档（`HANDOFF-*`/`superpowers/2026-*`）、`CHANGELOG.md`。
- [ ] `bun run verify`（前端 + Rust 全量）退出 0。
- [ ] VGOAPP `npm run build` 通过、`dist/macslim/` 不复存在。
