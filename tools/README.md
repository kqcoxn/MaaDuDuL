# 开发与维护工具

所有命令默认在仓库根目录执行。本地测试环境准备、启动和状态查看见 [本地开发管理](docs/local-development.md)。常用的 `yarn dev`、`yarn agent`、`yarn debug` 命令不变。

| 路径 | 用途 |
| --- | --- |
| `dev/` | 本地开发、Agent 和调试器启动脚本；独立 package.json 保留 CommonJS |
| `ci/` | MaaFwApp 打包配方与 APK 校验、发布默认 config、Android 依赖清单 |
| `launcher/` | 旧 PyInstaller 启动器源码；CMP 桌面发布已不使用 |
| `docs/` | 开发参考、协议文档与模板迁移说明 |
| `schema/` | CMP 管理的 schema 快照 |
| `build-release.mjs`、`sync-runtime.mjs` | CMP 桌面打包与运行库同步 |
| `validate-schema.mjs`、`check_resource.py` | 静态 schema 检查与 MaaFramework 原生资源加载检查 |
| `configure.py`、`package_android.py`、`requirements.txt` | OCR 配置、Android 资源打包与辅助脚本依赖 |

根目录保留 Interface、CMP 和 maa-tools 入口，以及 Yarn、uv 的依赖清单与锁文件。`.github`、`.vscode`、`.editorconfig`、Prettier 配置和语言版本文件也保留在工具默认查找的位置。图标统一复用 `public/`，Interface 与开发/Android 资源包使用 `public/logo.png`；桌面打包还将 `public/logo.ico` 复制为包根目录的 `logo.ico`。

CMP 的脚本与 schema 继续使用默认 `tools/` 路径。重新生成工作流时，应保留项目适配：`tools/ci/config` 打包到发布包的 `config/`，Android 使用 `tools/ci/requirements-android.txt` 和 `tools/ci/android/`，资源检查使用 `tools/check_resource.py`。

目录整理只修改文件位置和路径引用；未启动开发环境或执行构建、资源加载、设备测试。架构维护方式见 [模板迁移说明](docs/template-migration.md)。

## 根目录配置保留依据

- `package.json` 同时承载 Yarn 命令、依赖与 Prettier 配置，不再保留独立 `.prettierrc.mjs`。
- `.prettierignore` 按文件所在目录解释忽略规则，留在根目录以保持 CLI 和编辑器一致。
- `.editorconfig`、`.gitattributes` 分别供编辑器和 Git 使用，负责缩进、编码、换行及二进制文件属性。
- CMP 3.5.2 固定检查 `.node-version`、`.python-version`、`requirements.in`、`requirements.txt` 和 `uv.lock`；其 Python 依赖更新还会生成 requirements 文件，因此保留这些入口。
- `pyproject.toml` 是 Python 项目依赖声明，`uv.lock` 是锁文件，`requirements.txt` 供内置 Python 安装依赖；这些用途不同。
- 更新 CMP 模板后，应避免重新引入根目录图标副本和独立 Prettier 配置，并保留发布工作流的 `public/logo.ico` 引用。

版本统一维护入口与升级步骤见 [版本维护](docs/version-management.md)。
