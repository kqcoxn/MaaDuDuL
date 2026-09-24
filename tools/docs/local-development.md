# 本地开发与 MFAA 管理

源码是唯一维护入口。`MFAAvalonia/` 中的 resource、tasks、locales、agent 和 Interface 是生成的测试副本，不在其中开发。GUI 程序和运行配置沿用现有安装。

## 环境与命令

首次或依赖变更后手动执行 `uv sync --frozen`。开发脚本使用项目 `.venv`；可通过 `MDDL_PYTHON` 指定 Python 可执行文件路径，不支持附带命令参数，也不会静默回退系统 Python。启动前检查 Python 3.11–3.13 和 manifest 声明的 MaaFramework binding 版本。prepare/start/status 还会在独立进程中调用测试目录原生库的 `MaaVersion()`，要求实际版本与 `maafw.version` 一致；不以 GUI 版本或安装记录代替运行库检查。

| 命令 | 行为 |
| --- | --- |
| `yarn dev:install` | 下载并安装 manifest 锁定版本的 MFAA 和 MaaFramework；保留数据、备份旧安装，不启动 GUI |
| `yarn dev:install --framework-only` | 只对齐已有 MFAA 安装中的 MaaFramework，不重复下载 GUI；同样备份旧安装 |
| `yarn dev:status` | 显示测试目录、Python、实际 MaaFramework 版本、准备时间、源码/副本是否匹配及管理锁；不修改测试目录，未准备、版本不匹配或已过期返回非零 |
| `yarn dev:prepare` | 同步测试副本、生成 Interface，记录摘要；不启动 GUI |
| `yarn dev:start` | 仅启动已准备且与源码和 Python 匹配的副本；前台等待 GUI 退出 |
| `yarn dev` | 依次 prepare、start，保留原快捷入口 |
| `yarn agent` | 独立启动源码 Agent，支持 socket 参数 |
| `yarn agent:check` | 使用源码 Interface 相同的 uv/Python 入口检查环境；不启动 Agent、不连接设备 |
| `yarn mpe` | 启动 MPE LocalBridge，以仓库为文件根目录，显式读取源码 `interface.json`；要求支持 `--interface` 的 MPE 2.0 |

默认测试目录为仓库 `MFAAvalonia/`。可通过 `MDDL_MFAA_ROOT` 或 `--workspace` 指向仓库外已有 MFAA 安装，例如 `yarn dev:status --workspace D:/MaaTest`。只有显式执行 `yarn dev:install` 才下载或更新 GUI，prepare/start 不会触发安装。

准备前先关闭 MFAA 及其 Agent。脚本检查 GUI 进程，管理命令之间使用工作区锁互斥；命令启动的 GUI 退出后才释放锁。若终端被强制终止，确认 GUI 和 Agent 均已退出后，手动删除测试目录内 `.mddl-dev.lock`。不要一边 prepare 一边从外部手动启动 GUI。

## 同步和数据保留

- 同步 resource、tasks、locales、agent、interface.json 和 public/logo.png；移除这些受管理范围内已不存在于源码的文件，避免旧任务残留。
- 不清理工作区根目录的 config、logs、debug；跳过 Agent 中的 config、logs、debug 和 Python 缓存。开发模式下 Agent 不再自动清理错误截图。
- 文件以临时文件替换；同步期间清除就绪记录，失败后 start 会拒绝启动，重新 prepare 即可恢复。不是整个目录的事务回滚。
- `.mddl-dev.json` 记录源码目录、解释器、准备时间和源码/测试副本摘要。start 会检查源代码变更、测试副本手工修改及解释器切换；存在变化时要求重新 prepare。
- 不支持测试工作区及受管理路径中的软链接/junction，避免误写源码或其他目录。旧 `tools/dev/build_mfaa.py` 仅作为 prepare 兼容入口，不再启动 GUI。

## Python 与 Interface

- 源码 Interface：`uv run --frozen --no-sync python -u agent/local_main.py`。本地入口先检查当前 Python 和 maafw 版本，再调用正式 Agent；依赖须先安装，不在 GUI 启动期间自动同步。
- MFAA 测试 Interface：写入选定 Python 的绝对路径，运行测试副本的 `agent/main.py`。保留虚拟环境入口路径，不把 Unix venv 的符号链接解析成系统 Python。
- 桌面发布：打包器生成包内 Python 相对路径和正式入口参数，不依赖用户的 uv 或开发环境。
- Android：打包器同时重写 child_exec 和 child_args，不继承源码的 uv 参数。
- VS Code 调试使用 `.venv` 的平台对应解释器和 `agent/local_main.py`，与源码 Interface 共用环境检查。已有编辑器解释器选择如覆盖了默认设置，应手动切换到项目环境。

`agent/dev_environment.py` 是源码入口、VS Code 和 yarn 开发命令的共享检查实现，只读取 manifest 和当前解释器的包信息，不安装依赖、不导入 MaaFramework 或注册 Custom。失败时在标准错误中给出实际 Python 路径、版本问题和修复命令；由于此时 maafw 可能缺失，不依赖会导入 maa 的 `Prompter`。正式入口 `agent/main.py` 不执行开发环境检查，发布包也不需要源码 manifest。

默认开发环境为仓库 `.venv`。`MDDL_PYTHON` 仅影响经 `tools/dev/run_python.js` 启动的 yarn 命令；源码 Interface、`yarn agent:check` 和 MPE 默认仍由 uv 选择项目环境，不读取这个覆盖变量。使用自定义解释器时，应在 MPE 的本地 Agent 覆盖中选择该解释器并保留 `-u agent/local_main.py` 参数；覆盖只影响 MPE，不修改源码 Interface。

## MPE 2.0 直接读取源码 Interface

已静态核对本地 MaaPipelineEditor 的 `dev/2.0.0` 分支（`60d16436`）：LocalBridge 以主 Interface 所在目录启动 Agent，通过进程 PATH 查找 `uv`，并在参数末尾追加 socket ID；支持本地 Agent 启动覆盖。此结论针对该分支源码，不代表已安装的旧版 `mpelb` 已具备这些功能。

1. 首次准备或依赖变化后，在仓库根目录手动执行 `uv sync --frozen`。
2. 执行 `yarn agent:check`，确认源码入口实际选择的解释器及 maafw 版本。这个命令只检查环境，不启动 AgentServer。
3. 使用支持 `--interface` 的 MPE 2.0 LocalBridge 执行 `yarn mpe`。命令等价于 `mpelb --root . --interface ./interface.json`；文件扫描范围由原来的 `resource/` 扩大到仓库，显式入口避免与 `MFAAvalonia/` 等目录中的测试 Interface 混淆。
4. 在 MPE 中按需测试 Agent 连接或调试。单纯读取 Interface 不会启动 Agent。若此前配置过启动覆盖，应先检查覆盖是否仍然适用。

MPE 运行仓库中的 Agent，修改 Python 后重启 Agent 即可生效，无需 `dev:prepare`；没有热更新。`yarn dev` 继续运行 MFAA 测试副本，修改后仍需关闭 GUI/Agent 并重新 prepare。两种模式的 Custom 本地数据分别位于 `.local/agent/config/mddl/` 和测试目录的 `config/mddl/`（显式设置 `MDDL_STATE_ROOT` 时除外）。

如果 MPE 报找不到 `uv`，错误发生在 Python 入口执行之前，共享检查无法拦截。应让启动 LocalBridge 的进程 PATH 包含 uv 所在目录，安装 uv 后重启旧的终端/LocalBridge；也可以在 MPE 本地覆盖中将 `child_exec` 指向项目 Python 的绝对路径，`child_args` 设置为 `["-u", "agent/local_main.py"]`。不要手工追加 socket ID，LocalBridge 会自动传入。若提示 `--interface` 未知，需更新到支持该参数的 LocalBridge。

`MDDL_STATE_ROOT` 控制 Custom LocalStorage 的运行数据根目录：独立 Agent/VS Code 使用 `.local/agent`，受管理 MFAA 使用其测试目录，所以保留现有 `config/mddl`。未设置时维持发布环境的原路径。该变量不是 MFAA 自身的配置项；GUI 的日志与配置仍位于测试安装目录。不自动迁移或删除已有本地数据。

这次改动仅做静态检查，未执行 prepare/start、运行 Agent、构建发布包或修改现有测试安装。真实 GUI 与跨平台启动需要维护者手动验收。

## 安装 MFAA

手动执行 `yarn dev:install`。读取 `maa-project.json` 的 `runtime.mfa.version` 和 `maafw.version`，按当前 Windows/Linux/macOS 与 x64/arm64 分别选择 MaaXYZ/MFAAvalonia 和 MaaXYZ/MaaFramework GitHub Release 的精确版本资产，不追踪 latest。两份下载都强制验证 GitHub 的 SHA-256；API 或下载响应提供精确文件大小时也会核对。安装器在临时副本中先放置 GUI，再以项目指定的 MaaFramework 替换其原生库、平台插件和 MaaAgentBinary，与桌面打包的目录映射一致；调用 `MaaVersion()` 确认版本正确后才替换现有安装。

MFAA 的版本号与内置 MaaFramework 版本独立，更新 GUI 不代表协议已经与 Python Agent 对齐。若 GUI 已安装，只需要修复运行库，可执行 `yarn dev:install --framework-only`，随后执行 `yarn dev:prepare`。例如 Python Agent 5.13.0 与 GUI 内置 5.12.3 会因 Agent 协议不同而握手失败。

安装器支持 `GH_TOKEN`（优先）或 `GITHUB_TOKEN` 环境变量，仅向 GitHub API 发送凭据，不传给下载地址或重定向目标。API 返回限流错误时，会从同一版本的 GitHub 官方 Release 资产页面读取下载链接和 SHA-256，无需配置 token。页面缺少唯一且有效的 SHA-256 时仍会中止，不跳过校验。`yarn dev:prepare` 仅同步源码和资源，不会调用安装器或访问 GitHub。

安装和其他管理命令共用工作区锁，需要先关闭 GUI。资源、任务、Agent、Interface、public、config、logs、debug 保留；`runtimes/<平台>/native`、`plugins/<平台>` 和 `libs/MaaAgentBinary` 的文件作为整套 MaaFramework 替换，避免新旧库混用。其他文件按安装清单维护，首次接管不会删除这些范围之外的未知文件。旧安装备份在 `.local/mfaa-backups/`；仓库外目标备份在其父目录 `.mddl-mfaa-backups/`。备份不会自动删除。需要额外空间保存临时副本和旧安装。

安装后记录 `.mddl-runtime.json` 并使原 prepare 记录失效；继续执行 `yarn dev:prepare`，再 `yarn dev:start`。下载、校验或准备失败不会替换旧安装；最终替换失败会尝试恢复原目录。不支持含软链接或 junction 的安装目录/安装包，会明确拒绝而非跟随链接。GitHub 网络访问失败或限流后的 Release 页面回退失败会直接报告。

支持 `yarn dev:install --workspace D:/MaaTest`，也支持 `MDDL_MFAA_ROOT`。该命令使用与其他开发命令相同的 Python 环境，首次使用前先 `uv sync --frozen`。

版本升级请修改 `maa-project.json` 后执行 `yarn versions:sync`；完整说明见 [版本维护](version-management.md)。
