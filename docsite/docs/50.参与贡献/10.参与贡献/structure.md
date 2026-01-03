# 项目结构

::: tip 注意
本小节编写时基于 MDDL `v3.0.4` 版本
:::

## 项目目录

- `/.github`：存放 GitHub 配置文件，一般不用管
- `/DocSite`：文档站源码
- `/MFAAvalonia`：MFAAvalonia 本地调试存储
- `/MFATools`：MFATools 本地使用存储
- **`/agent`：存放 Custom 代码**
- **`/assets`：存放 Pipeline、Interface 文件与静态资源，请配合 MPE 使用**
- `/ci`：存放自动化部署脚本，一般不用管
- `/deps`：存放 MaaFramework 依赖包
- `/dev`：存放开发相关脚本，可以在`开发相关.md`中查看调用方式
- `/docs`：存放不重要的文档，如更新记录等
- `/feedbacker`：自动打包小工具
- `/gc`：安全清理小工具
- `/launcher`：MDDL 启动器
- 其他文件：全局相关配置

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
