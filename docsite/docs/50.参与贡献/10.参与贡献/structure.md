# 项目结构

## 项目目录

- `/agent`：Python Custom 与 Agent 服务入口。
- `/resource`：Pipeline、图片、OCR 与任务说明。
- `/tasks`、`/locales`：Interface 导入的任务选项与翻译。
- `/interface.json`：UI 入口；`maa-project.json`：CMP 项目和运行库配置。
- `/tools`：统一存放开发与维护工具，详见仓库 `tools/README.md`。
  - `dev/`：本地开发、Agent 与调试器启动脚本。
  - `ci/`：CI 辅助脚本、发布配置与 Android 依赖清单。
  - `launcher/`：保留的旧启动器源码，当前 CMP 桌面发布不使用。
  - `docs/`：开发参考与 `template-migration.md` 迁移说明。
  - `schema/`：CMP 管理的协议 schema。
- `/docsite`：文档站源码；`/public`：文档与 Android 使用的静态素材。
- `/assets`：保留的 MaaCommonAssets 子模块与旧本机配置。
- `/.github`：GitHub Actions 工作流；`/.vscode`：编辑器配置。
- `/MFAAvalonia`：本地测试环境。
- 根目录的 package、pyproject、锁文件及点配置：对应工具的项目入口与自动发现配置。

## Custom 调用

在需要使用 Custom 时，现有各文件总体功能如下：

- `/agent`
  - `main.py`、`dev_main.py`：agent 入口文件，一般不用修改
  - `setup.py`：本地环境更新器，在开发时无需关心
  - `report.py`：使用反馈
  - `/presets`：预设的固定数据
  - `/customs`
    - `Activities.py`：活动相关
    - `AgentTraining.py`：特工相关
    - `CityWalk.py`：城市探索相关
    - `Counter.py`：通用计数器
    - `Global.py`：全局配置
    - `GridScheduling.py`：通用矩阵排布解决方案
    - `Liaison.py`：联络相关
    - `PeriodicInspection.py`：通用周期检查器
    - `PipeLauncher.py`：需设置参数的 Pipeline 启动器
    - `Pipeliner.py`：通用 Pipeline 调度器
    - `Procurement.py`：采购相关
    - `Rememberer.py`：全局记忆器
    - `Strap.py`：卡带相关
    - `StrategicAction.py`：清体力相关
    - `Timer.py`：通用独立计时器
    - `__init__.py`：导出配置
    - `utils.py`：通用工具函数
