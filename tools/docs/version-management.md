# 版本维护

项目版本、MaaFramework、MFAA 和构建工具链的维护入口统一为根目录 `maa-project.json`。

| 字段 | 用途 |
| --- | --- |
| `project.version` | 项目版本；同步到 Interface、package 和 pyproject，发布 tag 必须匹配 |
| `maafw.version` | 桌面运行库、Python binding、本地环境检查、Android binding/runtime、maa-tools |
| `runtime.mfa.version` | 本地 MFAA 安装、桌面运行库、Android MFAA 源码 tag |
| `python.recommendedPython` / `requiresPython` | 开发与桌面 CI Python、Python 兼容范围 |
| `maintenance.pythonRuntime` | Windows 内置 Python 精确版本，Linux/macOS standalone 精确版本与构建 release |
| `maintenance.node` / `nodeMinimum` / `yarn` / `cmp` | Node CI 版本、最低版本、Yarn 和 CMP |
| `maintenance.android` | MFAA 源码仓库、p4a、NDK、Avalonia、构建 Python、Java、.NET、SDK 与 build-tools |
| `maintenance.rcedit` / `rceditSha256` | Windows 图标工具与匹配的 SHA-256 |

`maintenance` 是项目自定义配置，CMP 3.5.2 的配置读取保留此字段。重新生成模板时需保留它及本项目的版本读取逻辑。Android 不再读取旧的 `MFA_ANDROID_MFA_REPOSITORY`、`MFA_ANDROID_MFA_REF` 仓库变量；使用 fork 时修改 manifest 的 `maintenance.android.mfaRepository`，该仓库须存在 `runtime.mfa.version` 对应 tag。

## 修改流程

1. 修改 `maa-project.json` 中相关版本。
2. 执行 `yarn versions:sync`：同步派生版本文件、运行 `uv lock` 并导出 requirements；CMP 依赖版本变化时同步 Yarn 锁文件。
3. 执行 `yarn versions:check`：检查派生文件、Python 锁文件和导出是否一致，不下载运行库或启动程序。
4. 需要更新本地 Python 环境时再执行 `uv sync --frozen`；需要更换本地 GUI 时执行 `yarn dev:install`。

`yarn run check` 已包含版本检查。CI 读取 manifest 设置工具链，再校验派生文件。`versions:check` 需要 uv；Python 锁文件检查使用离线模式。同步声明不等于安装运行库，也不会自动更新已安装的 MFAA。

`yarn release` 按 `project.version` 创建并推送 `v<版本>` tag，执行前先检查版本一致性。该命令会发布 tag，不能当作检查命令使用。桌面正式发布拒绝与 manifest 不符的 tag；package-smoke 的显式测试 tag 保留。Android 普通手动构建的显示版本为 `v<项目版本>-ci.<运行号>-<提交>`，tag 构建使用发布 tag。

## 边界

推送 `v*` tag 时，Release 会复用 Android APK 工作流，与桌面端并行构建 ARM64 和 x64 APK，待所有平台成功后统一上传到 GitHub Release（包含 APK、SHA-256 和构建信息）。Android 构建失败会阻止本次发布。沿用现有 `MFA_ANDROID_*` 签名 secrets 和应用 ID；内部 versionCode 使用自 2020 年起的秒数，避免不同工作流的运行序号导致版本倒退。tag 构建的显示版本和文件名使用发布 tag，普通手动构建保留 CI 标记。

Android APK 仍可单独手动运行，此时只上传保留 7 天的 Actions artifacts，不发布 Release。Release 的手动入口仍仅执行桌面 dry-run，不构建 Android。

Android 以 GitHub 下载和覆盖安装为分发目标。包名 `com.kqcoxn.maadudul.ci` 和现有签名密钥保持稳定，正式包与手动测试包共用应用数据。CI 校验 APK 的签名、版本、名称、图标、启动入口、非调试状态、最低 Android 8.0、ABI 和 ZIP 对齐，并将证书 SHA-256、versionCode、ABI 写入随包发布的 build-info。随后与最近 100 个 Release 中最近一个其他 tag 的同架构 build-info 比对包名、证书和递增版本号；首次没有基线时明确提示尚未验证跨版本升级。该比对不覆盖未发布的手动安装包，也不能代替真机验证。

首次发布后应在同一设备上验证旧版安装、修改配置、新版直接覆盖安装、启动及配置保留；不要先卸载旧版。上游资源引导器保留已有 config，但仍需通过真实升级确认。不要更换签名 secrets 中的密钥；如需调整签名，须另行设计密钥迁移。时间 versionCode 按构建先后排序，重建旧 tag 也会得到更大的序号，因此不应把旧源码重建包当作新版分发。

Package Smoke 仅支持手动触发，日常提交和 PR 不执行打包 smoke，继续由 Check 执行常规检查。修改打包逻辑或升级 MaaFramework、MFAA、内置 Python 后，可在 GitHub Actions 的 Package Smoke 页面选择 Run workflow，对所选分支执行全部 6 个平台组合的打包及内置 Python 检查。正式发布仍保留全部平台构建。

普通第三方 Node/Python 库依赖继续由 package.json、pyproject.toml 及各自锁文件管理，GitHub Actions 的 `uses:` 版本继续留在工作流中。这里统一的是项目、Maa 运行库及显式构建工具链版本，没有把所有依赖再复制一份进 manifest。

Windows 内置 Python 保留原来的 3.13.14。Linux/macOS 原先跟随 python-build-standalone latest，本次固定为已查询到的 Python 3.13.15、release 20260901；它们的 minor 须与 recommendedPython 一致。Android 构建宿主 Python 仍独立为 3.11，不与桌面宿主版本强行合并。

已做静态版本/格式/schema/语法检查，未执行桌面或 Android 构建，也未下载运行库。Android 从 master 改为与桌面一致的 MFAA tag 后，具体构建兼容性仍需 CI 验证。
