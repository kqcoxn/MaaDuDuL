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
yarn migrate 1.2.3
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

Windows 内置 Python 固定为 3.13.17，Linux/macOS 固定为 3.13.18，使用 python-build-standalone release 20261026；它们的 minor 须与 recommendedPython 一致。Python 3.13.18 已进入仅源码发布阶段，没有官方 Windows 嵌入式包，因此不能直接把 Windows 下载版本同步为 3.13.18。Android 构建宿主 Python 和预编译内核 Python 分别维护，当前内核为 `3.13.15-maafw5.16.0`；APK 中的 MaaFramework binding/runtime 由 manifest 另行对齐到 5.16.1。

## 2026-11-15 依赖维护

- MaaFramework 与 Python binding：5.15.0 → [5.16.1](https://github.com/MaaXYZ/MaaFramework/releases/tag/v5.16.1)，同步 pyproject、uv.lock、requirements 及 Android requirements。Python 依赖锁定结果仅变更 maafw，六种桌面 wheel 和两种 Android 原生资产齐全。
- maa-tools：1.3.0 → 1.3.1；由其精确依赖带入 maa-pipeline-manager 1.2.0 和 maa-locale 1.3.0。使用 `yarn install --ignore-scripts --non-interactive` 更新 Yarn 锁文件，未重新生成模板。
- MaaFwApp：`c2449d8` → [`f29a0b0`](https://github.com/Aliothmoon/MaaFwApp/commit/f29a0b0d5e5ebdc845368f0e98e8104911765c1a)，仅修改取消运行后的 Tasker 停止等待；配方和构建脚本未变化。
- Android 内核：`3.13.15-maafw5.15.0` → [`3.13.15-maafw5.16.0`](https://github.com/Aliothmoon/MaaAgentCoreAndroid/releases/tag/3.13.15-maafw5.16.0)，解释器仍为 3.13.15。MFAA、CMP、排序插件及 OCR 模型保持原版本。

### 兼容性与适配结论

核对范围为 [MaaFramework 5.15.0 → 5.16.1 的完整差异](https://github.com/MaaXYZ/MaaFramework/compare/v5.15.0...v5.16.1)，目标提交 `ea944bd7b75f649851dc4807295966b3676bc821`；官方文档与源码导航使用 MaaLLMWiki v0.1.39。

- **Schema 已适配**：四份上游 Schema 全部回源到目标提交，URL 与 SHA-256 更新到 `tools/schema/schema-manifest.json`。其中 Interface 和 Interface Config 仅新增 iOS 控制器定义；Pipeline 和 Interface Import 内容及哈希不变，现有任务配置通过新 Schema 校验。
- **Custom 无需改写**：Python 的 `custom_action.py`、`custom_recognition.py`、`context.py`、`agent/agent_server.py` 均未变化。绑定新增 iOS 控制器、枚举和发现接口，`Tasker.clear_cache()` 的说明随上游缓存修复更新；项目没有调用该方法，也没有依赖控制器动作事件的业务回调。
- **流程无需迁移**：`jump_back` / `on_error` 的变化是文档澄清，相关流程处理未改动。识别轮次新增推理缓存、OCR override 清理旧 expected 等均在框架内部完成，现有 Custom 和 Pipeline 不需要增加开关或修改节点。
- **PlayCover 配置可沿用**：上游新增应用启停支持。项目当前 PlayCover UUID 与基础资源 StartApp 的 package 均为 `com.bilibili.trickcalcn`；本次不引入新的 iOS 控制器或修改任务入口。
- **Android binding 继续显式对齐**：核实两种 ABI 内核资产的官方 SHA-256、`agent-core.json`、Python/ABI、`bin/python3` 以及不含 `libMaa*.so` 的布局。内核原始 binding 是普通 `site-packages/maa`，上游 `build_agent_bundle.py` 随后将其收进 `pure.zip`，现有 `align_binding.py` 再整体替换为 5.16.1；[目标版本加载器](https://github.com/MaaXYZ/MaaFramework/blob/ea944bd7b75f649851dc4807295966b3676bc821/source/binding/Python/maa/library.py) 中 Android 平台适配标记未变，继续保留 Android → Linux 的局部映射。
- **Android 原生库收集规则可沿用**：两种 5.16.1 Android zip 均已校验官方 SHA-256 并检查 ELF 依赖。新增 `libMaaIOSControlUnit.so` 依赖的 `libxdb_client.so` 与其一起位于 `bin/`，现有上游 `.so` 收集规则会同时纳入，不需要修改构建参数或硬编码库列表。

验证结果：`yarn versions:sync`、`yarn run check`（版本一致性、格式与全部 Interface/Pipeline Schema）通过；Schema 内容与记录的 SHA-256 一致。没有运行 maa-tools 资源加载检查、设备任务或跨平台构建，因此不将静态核对视为运行验收。未安装 Python/MFAA 运行环境、未改动现有 `MFAAvalonia` 测试目录、未发布。

## 2026-11-05 依赖维护

- MaaFramework 与 Python binding：5.14.3 → [5.15.0](https://github.com/MaaXYZ/MaaFramework/releases/tag/v5.15.0)。Custom 识别仍兼容现有单结果回调，无需改写业务 Custom；Android 继续执行 binding 对齐及 Android 平台名适配。
- MFAA：v2.16.2 → [v2.16.4](https://github.com/MaaXYZ/MFAAvalonia/releases/tag/v2.16.4)，已核实六种桌面平台/架构资产齐全。
- MaaFwApp：`de65f7a` → [`c2449d8`](https://github.com/Aliothmoon/MaaFwApp/commit/c2449d8030644386e1a9e3ba7cb21037c2bcdbdf)。资源配方、内核打包参数和身份覆盖接口保持兼容；Android 内核同步为 `3.13.15-maafw5.15.0`，ARM64/x64 资产齐全。
- CMP：3.7.3 → 3.7.4；maa-tools：1.1.3 → 1.3.0。仅更新依赖，不重新生成 Agent 或工作流模板。
- Linux/macOS 内置 Python：3.13.17 → [3.13.18](https://www.python.org/downloads/release/python-31318/)，核实 standalone 四种目标资产及 SHA-256；Windows 和 Android 解释器分别保持 3.13.17、3.13.15。

本地四份上游 schema 使用 MaaFramework 5.15.0 的提交 `172ec7b97df3e5b10adf69e36df01f8dc495b6f6`，来源与实际文件 SHA-256 记录于 `tools/schema/schema-manifest.json`。CMP 的 `--update schema` 当前写入其随包携带的 main 基线；刷新后须与目标版本回源核对，不能用开发分支 schema 代替发布版本契约。

适配中删除采购选项对四个已不存在的“周期组合检查”节点的覆盖，保留实际周期检查节点的覆盖。繁中资源层此前只有 `.gitkeep`，加载时 `to_load=false`；增加 `pipeline/placeholder.json` 空对象，保留继承基础资源的行为并使资源层可加载。

验证结果：`yarn versions:sync`、`yarn versions:check`、`yarn run check` 通过；maa-tools 检查中的三组资源全部加载成功。`yarn check:maa` 仍返回非零：pipeline-manager 1.1.0 将同一节点的 `next` 和 `on_error` 引用合并去重，误报 `清红糖_指定关卡作战`、`购买糖果_点击购买`、`购买糖果_紫糖点击购买` 的三条重复路由。成功与失败分支有意指向同一收尾节点，保留这些恢复路径及原检查级别。MPE 元数据警告属于有意保留的编辑器配置。

CMP doctor 的 pnpm 文件、固定写法的 Node CI、默认 Agent 文件和 maa-tools 配置检查不适配本项目的 Yarn、manifest 动态读取、自定义 Agent 布局，未按模板建议覆盖现有配置。此次未安装或修改 MFAAvalonia 测试环境、未启动任务、未构建或发布。
