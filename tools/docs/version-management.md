# 版本维护

项目版本、MaaFramework、MFAA、MaaFwApp 和构建工具链的维护入口统一为根目录 `maa-project.json`。

| 字段 | 用途 |
| --- | --- |
| `project.version` | 项目版本；同步到 Interface、package、pyproject、更新日志首行和中英文窗口标题，发布 tag 必须匹配 |
| `maafw.version` | 桌面运行库、Python binding、本地环境检查、Android binding/runtime、maa-tools |
| `runtime.mfa.version` | 本地 MFAA 安装、桌面运行库 |
| `python.recommendedPython` / `requiresPython` | 开发与桌面 CI Python、Python 兼容范围 |
| `maintenance.pythonRuntime` | Windows 内置 Python 精确版本，Linux/macOS standalone 精确版本与构建 release |
| `maintenance.node` / `nodeMinimum` / `yarn` / `cmp` | Node CI 版本、最低版本、Yarn 和 CMP |
| `maintenance.android` | MaaFwApp 仓库/ref、Android Python 内核仓库/tag/版本、构建 Python、Java、NDK、CMake、SDK 与 build-tools |
| `maintenance.rcedit` / `rceditSha256` | Windows 图标工具与匹配的 SHA-256 |

`maintenance` 是项目自定义配置，CMP 3.5.2 的配置读取保留此字段。重新生成模板时需保留它及本项目的版本读取逻辑。Android 从 `maintenance.android.appRepository` / `appRef` 读取 MaaFwApp 上游；与桌面 MFAA 的版本独立。`agentCoreRepository` / `agentCoreTag` / `agentPython` 固定预编译内核，CI 将其中的 Python binding 替换为 `maafw.version` 对应源码并保留 Android 平台名适配，因此内核 tag 中的旧 MaaFramework 版本不代表 APK 的实际版本。

## 修改流程

仅替换项目版号时，在仓库根目录执行：

```sh
yarn version:set 1.2.3
```

也支持 `v1.2.3`，以及 `1.2.3-alpha.1`、`1.2.3-beta.1`、`1.2.3-rc.1` 预发布版。
命令修改 `maa-project.json` 的 `project.version`，随后自动执行现有的版本同步及一致性检查，
更新 `package.json`、`interface.json`、`pyproject.toml` 及 Python 锁文件/导出，
同时更新 `resource/Changelog.md` 的首行版号和 `locales/interface_zh.json`、`locales/interface_en.json` 的 `project_title` 版号。
更新日志的日期、正文和历史记录保持不变，窗口标题中的游戏版本文字保持不变。
这些字段也纳入 `yarn versions:sync` 和 `yarn versions:check`，遗漏同步时检查会报错。
需要已安装 Node.js、Yarn 和 uv，同步期间可能访问网络。重复传入当前版号也会执行同步检查。
同步会以 manifest 为准处理全部受管理的版本字段，因此其他尚未同步的版本修改也会一并生效。
失败时命令返回非零退出码并保留已发生的修改，修复原因后可重新执行。
该命令不安装本地 MFAA、不构建、不创建或推送 tag；实际发布仍单独使用 `yarn release`。

需要调整 MaaFramework、MFAA 或工具链版本时：

1. 修改 `maa-project.json` 中相关版本。
2. 执行 `yarn versions:sync`：同步派生版本文件、运行 `uv lock` 并导出 requirements；CMP 依赖版本变化时同步 Yarn 锁文件。
3. 执行 `yarn versions:check`：检查派生文件、Python 锁文件和导出是否一致，不下载运行库或启动程序。
4. 需要更新本地 Python 环境时再执行 `uv sync --frozen`；需要更换本地 GUI 时执行 `yarn dev:install`。

`yarn run check` 已包含版本检查。CI 读取 manifest 设置工具链，再校验派生文件。`versions:check` 需要 uv；Python 锁文件检查使用离线模式。同步声明不等于安装运行库，也不会自动更新已安装的 MFAA。

`yarn release` 按 `project.version` 创建并推送 `v<版本>` tag，执行前先检查版本一致性。该命令会发布 tag，不能当作检查命令使用。桌面正式发布拒绝与 manifest 不符的 tag；package-smoke 的显式测试 tag 保留。Android 普通手动构建的显示版本为 `v<项目版本>-ci.<运行号>.<重试号>-<提交>`，tag 构建使用发布 tag。

## 边界

推送 `v*` tag 时，Release 并行调用桌面与 Android 工作流，全部成功后统一发布。Android 使用 MaaFwApp 的资源配方、预编译 Python 内核和 Gradle，产出包含 ARM64/x64 的通用 APK、SHA-256 和 build-info。独立手动运行 Android APK 仅上传保留 7 天的 artifact；Release 手动入口仍是桌面 dry-run。

Android 要求 Android 9+、Shizuku 或 root。沿用应用 ID `com.kqcoxn.maadudul.ci` 和 `MFA_ANDROID_*` 签名 secrets，versionCode 继续采用自 2020 年起的秒数。上游配方不能指定完整包名，CI 通过 `tools/ci/android/identity.init.gradle` 设置包名与 versionCode，不修改客户端源码。重建旧 tag 也会产生更大的版本号，不应当作新版分发。

APK 校验覆盖签名、版本、启动入口、名称、图标、最低系统、双 ABI 和资源/agent 载荷；升级校验兼容原来的单架构 build-info。静态包检查不能代替真机覆盖安装验证。MFAA 与 MaaFwApp 的界面配置不自动迁移；自定义持久化数据通过配方中的 `MDDL_STATE_ROOT` 放在 PI 资源目录旁，避免新客户端升级重解包时清除。旧 MFAA 的自定义数据路径不会自动迁移。

Package Smoke 仅支持手动触发，日常提交和 PR 不执行打包 smoke，继续由 Check 执行常规检查。修改打包逻辑或升级 MaaFramework、MFAA、内置 Python 后，可在 GitHub Actions 的 Package Smoke 页面选择 Run workflow，对所选分支执行全部 6 个平台组合的打包及内置 Python 检查。正式发布仍保留全部平台构建。

普通第三方 Node/Python 库依赖继续由 package.json、pyproject.toml 及各自锁文件管理，GitHub Actions 的 `uses:` 版本继续留在工作流中。这里统一的是项目、Maa 运行库及显式构建工具链版本，没有把所有依赖再复制一份进 manifest。

Windows 内置 Python 保留原来的 3.13.14。Linux/macOS 原先跟随 python-build-standalone latest，本次固定为已查询到的 Python 3.13.15、release 20260901；它们的 minor 须与 recommendedPython 一致。Android 构建宿主 Python 和预编译内核 Python 分别维护。
