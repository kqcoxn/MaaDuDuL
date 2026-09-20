# 本地开发与 MFAA 管理

源码是唯一维护入口。`MFAAvalonia/` 中的 resource、tasks、locales、agent 和 Interface 是生成的测试副本，不在其中开发。GUI 程序和运行配置沿用现有安装。

## 环境与命令

首次或依赖变更后手动执行 `uv sync --frozen`。开发脚本使用项目 `.venv`；可通过 `MDDL_PYTHON` 指定 Python 可执行文件路径，不支持附带命令参数，也不会静默回退系统 Python。启动前检查 Python 3.11–3.13 和 manifest 声明的 MaaFramework binding 版本。

| 命令 | 行为 |
| --- | --- |
| `yarn dev:install` | 下载并安装 manifest 锁定版本的 MFAA；保留数据、备份旧安装，不启动 GUI |
| `yarn dev:status` | 只读显示测试目录、Python、准备时间、源码/副本是否匹配及管理锁；未准备或已过期返回非零 |
| `yarn dev:prepare` | 同步测试副本、生成 Interface，记录摘要；不启动 GUI |
| `yarn dev:start` | 仅启动已准备且与源码和 Python 匹配的副本；前台等待 GUI 退出 |
| `yarn dev` | 依次 prepare、start，保留原快捷入口 |
| `yarn agent` | 独立启动源码 Agent，支持 socket 参数 |

默认测试目录为仓库 `MFAAvalonia/`。可通过 `MDDL_MFAA_ROOT` 或 `--workspace` 指向仓库外已有 MFAA 安装，例如 `yarn dev:status --workspace D:/MaaTest`。只有显式执行 `yarn dev:install` 才下载或更新 GUI，prepare/start 不会触发安装。

准备前先关闭 MFAA 及其 Agent。脚本检查 GUI 进程，管理命令之间使用工作区锁互斥；命令启动的 GUI 退出后才释放锁。若终端被强制终止，确认 GUI 和 Agent 均已退出后，手动删除测试目录内 `.mddl-dev.lock`。不要一边 prepare 一边从外部手动启动 GUI。

## 同步和数据保留

- 同步 resource、tasks、locales、agent、interface.json 和 public/logo.png；移除这些受管理范围内已不存在于源码的文件，避免旧任务残留。
- 不清理工作区根目录的 config、logs、debug；跳过 Agent 中的 config、logs、debug 和 Python 缓存。开发模式下 Agent 不再自动清理错误截图。
- 文件以临时文件替换；同步期间清除就绪记录，失败后 start 会拒绝启动，重新 prepare 即可恢复。不是整个目录的事务回滚。
- `.mddl-dev.json` 记录源码目录、解释器、准备时间和源码/测试副本摘要。start 会检查源代码变更、测试副本手工修改及解释器切换；存在变化时要求重新 prepare。
- 不支持测试工作区及受管理路径中的软链接/junction，避免误写源码或其他目录。旧 `tools/dev/build_mfaa.py` 仅作为 prepare 兼容入口，不再启动 GUI。

## Python 与 Interface

- 源码 Interface：`uv run --frozen --no-sync python -u agent/local_main.py`。本地入口设置开发环境后调用正式 Agent；依赖须先安装，不在 GUI 启动期间自动同步。
- MFAA 测试 Interface：写入选定 Python 的绝对路径，运行测试副本的 `agent/main.py`。保留虚拟环境入口路径，不把 Unix venv 的符号链接解析成系统 Python。
- 桌面发布：打包器生成包内 Python 相对路径和正式入口参数，不依赖用户的 uv 或开发环境。
- Android：打包器同时重写 child_exec 和 child_args，不继承源码的 uv 参数。
- VS Code 调试使用 `.venv` 的平台对应解释器。已有编辑器解释器选择如覆盖了默认设置，应手动切换到项目环境。

`MDDL_STATE_ROOT` 控制 Custom LocalStorage 的运行数据根目录：独立 Agent/VS Code 使用 `.local/agent`，受管理 MFAA 使用其测试目录，所以保留现有 `config/mddl`。未设置时维持发布环境的原路径。该变量不是 MFAA 自身的配置项；GUI 的日志与配置仍位于测试安装目录。不自动迁移或删除已有本地数据。

这次改动仅做静态检查，未执行 prepare/start、运行 Agent、构建发布包或修改现有测试安装。真实 GUI 与跨平台启动需要维护者手动验收。

## 安装 MFAA

手动执行 `yarn dev:install`。读取 `maa-project.json` 的 `runtime.mfa.version`，按当前 Windows/Linux/macOS 与 x64/arm64 选择 MaaXYZ/MFAAvalonia GitHub Release 的精确版本资产，不追踪 latest。先下载到临时目录，验证 GitHub 的 SHA-256 和文件大小，再准备安装。

安装和其他管理命令共用工作区锁，需要先关闭 GUI。资源、任务、Agent、Interface、public、config、logs、debug 保留；受安装清单管理的旧运行库文件会被替换。首次接管旧安装时不会猜测并删除未知文件。旧安装备份在 `.local/mfaa-backups/`；仓库外目标备份在其父目录 `.mddl-mfaa-backups/`。备份不会自动删除。需要额外空间保存临时副本和旧安装。

安装后记录 `.mddl-runtime.json` 并使原 prepare 记录失效；继续执行 `yarn dev:prepare`，再 `yarn dev:start`。下载、校验或准备失败不会替换旧安装；最终替换失败会尝试恢复原目录。不支持含软链接或 junction 的安装目录/安装包，会明确拒绝而非跟随链接。GitHub 网络访问或 API 限额导致的失败会直接报告。

支持 `yarn dev:install --workspace D:/MaaTest`，也支持 `MDDL_MFAA_ROOT`。该命令使用与其他开发命令相同的 Python 环境，首次使用前先 `uv sync --frozen`。

版本升级请修改 `maa-project.json` 后执行 `yarn versions:sync`；完整说明见 [版本维护](version-management.md)。
