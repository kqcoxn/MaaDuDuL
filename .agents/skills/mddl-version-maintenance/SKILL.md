---
name: mddl-version-maintenance
description: 维护 MaaDuDuL 的项目、MaaFramework、MFAA 和构建工具链版本，核对 maa-project.json、派生配置、锁文件以及本地与 CI 的一致性。用于升级、降级、锁定版本、准备版本号或排查版本漂移；不用于一般 Pipeline 功能开发，也不因修改版本而自动发布或安装测试环境。
---

# MaaDuDuL 版本维护

本 skill 属于当前仓库。版本事实来自工作区，不把某次升级的版本号写成永久默认值。

## 先确定维护范围

读取根目录 `maa-project.json`、`package.json` 的 scripts，以及 [版本维护说明](../../../tools/docs/version-management.md)。执行前查看 Git 状态，保留已有暂存和未提交改动。

- 询问“现在用哪个版本、从哪里读取”：只读核对声明与调用链，不执行同步或安装。
- 指定升级、降级或版本号修改：只修改用户要求的版本及必需的兼容字段，再同步派生配置。
- 请求“最新版”：从对应官方 release、包索引或仓库核实当前版本及发布渠道；未指定预发布渠道时不要自动切到 beta/nightly。
- 请求“修复漂移”：以 manifest 为准；若用户明确要将现有依赖版本作为新目标，先修改 manifest，再同步。

## 唯一维护入口与边界

以 `maa-project.json` 为项目和显式工具链版本入口：

- `project.version`：不带 `v` 的项目版本；Interface 和正式发布 tag 派生为 `v<版本>`。
- `maafw.version`：桌面运行库、Python binding、Android 与本地检查共同使用。
- `runtime.mfa.version`：MFAA 本地安装、桌面 CI 和 Android 源码 tag 共同使用；渠道字段也需匹配。
- `python`：推荐解释器和兼容范围；`maintenance.pythonRuntime`：内置 Python 精确版本及 standalone release。
- `maintenance`：项目自定义的 Node、Yarn、CMP、Android 工具链、rcedit 版本及校验值。

`interface.json`、版本文件、相关 package/pyproject 字段和 requirements 是派生结果，不能只改它们来完成版本升级。不要手工伪造锁文件或下载校验值。

普通第三方库依赖仍在 package.json / pyproject.toml 及锁文件中维护；GitHub Actions 的 `uses:` 版本仍在工作流中。不要把它们批量搬入 manifest，也不要顺手升级无关依赖。

## 修改与验证

1. 根据目标字段核对对应的实际消费者；必要时阅读 [同步脚本](../../../tools/versions.mjs)、[运行库下载](../../../tools/sync-runtime.mjs)、[发布打包](../../../tools/build-release.mjs) 和相关 `.github/workflows/`。文档与代码冲突时先查明，不依据文档猜测已实现的能力。
2. 修改 manifest 后，在仓库根目录执行 `yarn versions:sync`。它更新派生文件、调用 uv lock/export，并在需要时更新 CMP 的 Yarn 锁定依赖；可能访问网络，不是只读命令。
3. 检查实际 diff，确认目标版本、Python/Node 锁文件和导出一致，且未夹带无关升级。不通过恢复整个文件或重置工作区来清除用户改动。
4. 执行 `yarn versions:check`；需要检查受影响的格式或 Interface schema 时执行 `yarn run check`。Yarn 1 的 `yarn check` 是内置命令，不能替代项目检查。
5. 同步失败时保留并说明已发生的修改，定位失败步骤；不使用 `--frozen` 绕过锁文件漂移，也不降低 CI 门禁来宣称完成。缺少 uv 或离线缓存时，区分环境问题和版本不一致。

修改同步脚本本身时检查其幂等性、检查模式是否只读，以及 CI 初始化顺序：`--ci` 在依赖安装前读取 manifest，不能依赖尚未安装的项目 Python/Node 包。

## 按需兼容性核对

- **MFAA**：核实目标 tag 有所需平台/架构资产；Android 的 `maintenance.android.mfaRepository` 必须有同一 tag。不能只确认桌面压缩包存在就宣称 Android 可构建；也不能静默回退 master 或旧仓库变量。
- **MaaFramework**：核实 Python binding、原生运行库和 Android 源码 tag 对应。涉及 API 或 Pipeline 语义变化时按项目要求查 `tools/docs/maafw-guide/`，必要时使用可用的 Maa 文档 skill。
- **Python**：内置解释器 minor 与 recommendedPython 一致；Windows 版本和 standalone 的 Python 版本/release 分别核实。Android 构建宿主 Python 是独立配置，不强行改成桌面版本。
- **CMP**：升级 npm 版本不等于重新生成模板。保留 `maintenance`、Yarn、版本读取脚本和自定义工作流；只有用户要求刷新模板时才走对应 CMP 维护流程。
- **rcedit**：版本与官方资产的 SHA-256 配套更新，不能沿用旧版本校验值。

## 安装、运行与发布是独立动作

版本同步不代表已安装、已运行或已发布。遵循项目“不自动构建测试”和不改动现有 MFAAvalonia 测试环境的约束：普通版本维护不执行 `yarn dev`、prepare/start、运行库下载、设备任务或构建。

用户明确要求更新本地环境时，参考 [本地开发管理](../../../tools/docs/local-development.md)，区分 `uv sync --frozen` 与 `yarn dev:install`；已有授权足够时不重复询问。

`yarn release` 会创建并推送 tag。修改版本或“准备发版”不自动授权执行它；只有明确要求发布/推送时才执行相应操作。不要把 release 或 release:dry-run 当作普通静态检查。

完成时简要报告目标与旧版本、变更范围、同步/检查结果，以及没有执行的安装、构建或发布。静态检查通过不等于跨平台运行或 Android 构建验证通过。
