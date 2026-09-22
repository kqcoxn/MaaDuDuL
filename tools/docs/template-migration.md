# CMP 架构迁移与维护

本项目从 MaaPracticeBoilerplate 迁移至 create-maa-project 3.5.2 的 Agent、dev-tools、VS Code 和 GitHub 模板。官方模板由 CLI 在独立目录生成后合并，保留本项目的 Custom 注册、Prompter、多语言资源、Android 工作流和 MirrorChyan 发布链路。

## 目录

| 原路径 | 当前路径 |
| --- | --- |
| `assets/interface.json` | `interface.json` |
| `assets/resource/tasks/` | `tasks/` |
| `assets/resource/` 其余内容 | `resource/` |
| `assets/locales/` | `locales/` |
| `public/logo.ico`、`public/logo.png` | 统一复用 public 中的图标；Interface 使用 `public/logo.png` |
| `tools/install.py` | 桌面改用 `tools/build-release.mjs`；Android 适配器为 `tools/package_android.py` |
| `.github/versions.json` | `maa-project.json` |

`assets/MaaCommonAssets` 保留原 Git 子模块位置，避免改写已有 checkout 的子模块元数据。OCR 配置指向 `assets/MaaCommonAssets/OCR/ppocr_v6/small`，模型仍从子模块复制到 `resource/base/model/ocr`，不提交模型副本。`assets/config/maa_pi_config.json` 是旧的本机调试配置，不进入发布包。原 `deps` 下载目录退出版本管理，本机文件不删除。`MFAAvalonia` 测试环境未改动。

原 158 个资源／任务文件内容保持一致；另一个任务文件 `tasks/daily/clear_red_candy.json` 修复了“龙族”case 缺失的 `pipeline_override` 外层。没有增加或修改 Pipeline 节点。翻译键保留原样，翻译值中的 `Resource/` 改为实际目录 `resource/`，兼容区分大小写的平台。

Prettier 配置合并到 `package.json` 的 `prettier` 字段，不再另设 `.prettierrc.mjs`。重新生成模板时应保留此合并，避免新生成的配置覆盖项目规则。

开发辅助目录已统一收进 `tools/`，分类与根目录保留规则见 [工具目录说明](../README.md)。刷新 CMP 模板后，还应保留工作流对 `tools/ci/`、`tools/check_resource.py` 的引用。

## 版本与 Interface 所有权

- `maa-project.json` 使用 schemaVersion 2，项目 slug 为 `maa-dudul`，显示名称和发布启动文件保持 `MaaDuDuL`。
- Interface 设置 `project.interfaceUnmanaged: true`。控制器名、资源 ID、任务、分组、选项、MirrorChyan ID 和国际化标签由项目维护。
- 资源选择顺序仍为 cn → base、en → base + en、zh_hant → base + zh_hant。配置中的资源 slug `zh-hant` 与实际目录 `zh_hant` 有意不同。
- MaaFramework 与 Python binding 统一锁定 5.13.0，MFAAvalonia 保持原 CI 的 v2.16.2-beta.2。后续升级统一修改 manifest，再执行 `yarn versions:sync` 与 `yarn versions:check`，详见 [版本维护](version-management.md)。
- Python 支持 3.11–3.13，桌面模板打包 Python 3.13；Android 使用 MaaFwApp 与预编译 Python 内核。

## 开发命令

```sh
yarn install --frozen-lockfile
uv sync --frozen
git submodule update --init --recursive
uv run python tools/configure.py
yarn run check
```

开发命令 `yarn dev`、`yarn agent`、`yarn debug` 保留；Python 使用显式 `MDDL_PYTHON` 或项目 `.venv`，不再回退系统 Python。MFAA 操作拆分为 `yarn dev:prepare`、`yarn dev:start`、`yarn dev:status`，详见 [本地开发管理](local-development.md)。根 package 使用 ESM，`tools/dev/package.json` 将原开发脚本保留为 CommonJS。VS Code 的依赖安装任务需手动启动，不会打开目录即自动执行。

Yarn 1 的 `yarn check` 是其内置依赖检查，务必使用 `yarn run check` 执行项目静态检查。当前静态门禁检查迁移工具配置的格式和全部 Interface／Pipeline schema；`check:maa`、`check:py` 单独保留，旧 Custom 代码尚未建立全量 Ruff／Pyright 基线，不将其作为本次发布门禁。CI 另保留使用锁定 MaaFramework 的原生资源加载检查。

## 发布和维护

桌面 `desktop.yml` 使用六个平台的对应架构 runner、CMP runtime 同步和内置 Python，供手动构建及 `release.yml` 复用。依赖在构建时安装，Agent 首次启动不执行 pip。CMP 直接将 GUI 可执行文件命名为 `MaaDuDuL`，不再用 PyInstaller 构建额外启动器。发布包额外包含 locales、tools/ci/config 和图标，并保留项目更新日志和 MirrorChyan 上传。Android 使用 MaaFwApp 配方接入资源和 Python agent，依赖由 `tools/ci/requirements-android.txt` 声明。

```sh
yarn doctor
yarn cmp --update schema --report
yarn sync:runtime
yarn release:dry-run
```

后两条涉及运行库下载或打包检查，应由维护者需要时执行。CMP 的 `--update node-deps` 默认使用 pnpm；本项目使用 `yarn install`。项目版本和运行库版本通过 `yarn versions:sync` 同步派生配置、锁文件与导出，`yarn versions:check` 检查一致性。

CMP 管理文件升级会覆盖项目适配。再次运行 `--add github` 或刷新模板后，应审查并保留：Yarn 命令、发布检查范围、单对象 Agent 兼容、locales／tools/ci/config 收录、MaaDuDuL 启动文件名、项目更新日志、MirrorChyan hook、自定义 customs 导入检查。不要通过 `--add agent` 覆盖现有业务入口。Interface 为 unmanaged，版本更新也应核对根 Interface 的 `version`。

CLI 写操作提供 `.create-maa-project` 下的备份；本次旧文件和目录迁移可通过 Git diff 审查，未提交、未推送。维护前先检查工作区，避免恢复操作覆盖用户自己的改动。

## 本次验证边界

- 已通过：`yarn run check`，Python AST 语法检查，修改的 JS/MJS 语法检查，24 个任务、101 个选项的翻译／选项／入口引用检查，迁移前后 158 个资源文件内容比对。
- CMP doctor：配置、Interface、Python、编辑器、资源、OCR 和路径均通过；仅 `node-tooling`、`node-lockfile` 失败，因为 CMP 3.5.2 硬编码要求 `pnpm-workspace.yaml`、`pnpm-lock.yaml`。本项目有意使用 Yarn 和 `yarn.lock`，保留 doctor 原始失败，不伪造 pnpm 文件。
- 未执行：开发环境启动、原生资源加载、设备任务、完整打包、package smoke、发布运行库下载、全量 Python lint/typecheck。遵守项目“不自动构建测试”的要求，CI 与真实运行仍需后续验证。

模板依据：[CMP v3.5.2 集成 Skill](https://github.com/Windsland52/create-maa-project/blob/v3.5.2/skills/create-maa-project/SKILL.md)。协议依据为本地 `tools/docs/maafw-guide/3.3-ProjectInterfaceV2协议.md`；schema 来自 CMP 附带的官方快照，来源和哈希保存在 `tools/schema/schema-manifest.json`。
