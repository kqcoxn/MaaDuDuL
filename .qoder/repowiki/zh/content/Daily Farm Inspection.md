# 日常农场检查

<cite>
**本文档引用的文件**
- [README.md](file://README.md)
- [agent/main.py](file://agent/main.py)
- [launcher/MaaDuDuL.py](file://launcher/MaaDuDuL.py)
- [MFAAvalonia/config/config.json](file://MFAAvalonia/config/config.json)
- [MFAAvalonia/Resource/base/default_pipeline.json](file://MFAAvalonia/Resource/base/default_pipeline.json)
- [MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json](file://MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json)
- [agent/preprocess/setup.py](file://agent/preprocess/setup.py)
- [requirements.txt](file://requirements.txt)
- [assets/resource/descs/daily/farm.md](file://assets/resource/descs/daily/farm.md)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概览](#架构概览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介

"Daily Farm Inspection"（每日农场检查）是一个基于MaaFramework和MFAAvalonia框架开发的自动化农场管理助手。该项目专为《嘟嘟脸恶作剧》游戏设计，提供智能化的农场视察、萝卜收取和跑腿派遣功能。

该项目的核心目标是通过图像识别技术和模拟控制，自动完成游戏中的日常农场任务，包括：
- 自动收取农场萝卜
- 智能重新派遣跑腿任务
- 宠物萝卜收集
- 农场状态检查和记录

项目采用现代化的架构设计，结合了Python后端逻辑、Avalonia GUI界面和MaaFramework的图像识别能力。

## 项目结构

项目采用模块化组织结构，主要包含以下几个核心部分：

```mermaid
graph TB
subgraph "项目根目录"
A[README.md] --> B[agent/]
A --> C[MFAAvalonia/]
A --> D[assets/]
A --> E[launcher/]
A --> F[deps/]
end
subgraph "agent/ - 核心代理模块"
B1[main.py] --> B2[preprocess/]
B2 --> B3[setup.py]
B --> B4[customs/]
B4 --> B5[global_func/]
B4 --> B6[special_treat/]
B4 --> B7[utils/]
end
subgraph "MFAAvalonia/ - GUI界面"
C1[config/] --> C2[config.json]
C --> C3[Resource/]
C3 --> C4[pipeline/]
C3 --> C5[descs/]
C3 --> C6[base/]
end
subgraph "assets/ - 资源文件"
D1[resource/] --> D2[pipeline/]
D1 --> D3[descs/]
D1 --> D4[interface.json]
end
```

**图表来源**
- [agent/main.py](file://agent/main.py#L1-L78)
- [MFAAvalonia/config/config.json](file://MFAAvalonia/config/config.json#L1-L545)

**章节来源**
- [README.md](file://README.md#L1-L117)
- [agent/main.py](file://agent/main.py#L1-L78)

## 核心组件

### Agent服务器组件

Agent服务器是整个系统的核心控制单元，负责协调各个功能模块的工作。

```mermaid
classDiagram
class AgentServer {
+start_up(socket_id) void
+join() void
+shut_down() void
+init_option(path) void
}
class Toolkit {
+init_option(path) void
+create_controller() Controller
+create_resource() Resource
}
class TaskManager {
+execute_pipeline(pipeline) Result
+check_progress() Progress
+handle_error(error) void
}
class CustomFunctions {
+periodic_check(key) boolean
+record_period(key) void
+on_task_start(params) void
}
AgentServer --> Toolkit : "使用"
AgentServer --> TaskManager : "管理"
TaskManager --> CustomFunctions : "调用"
```

**图表来源**
- [agent/main.py](file://agent/main.py#L47-L77)

### GUI界面组件

MFAAvalonia提供了现代化的图形用户界面，支持任务配置和状态监控。

```mermaid
classDiagram
class MainWindow {
+load_tasks() void
+execute_task(task_name) void
+show_progress() void
+display_log(message) void
}
class TaskConfig {
+name : string
+label : string
+entry : string
+default_check : boolean
+description : string
+options : array
}
class TaskQueue {
+add_task(task) void
+remove_task(task) void
+execute_queue() void
+clear_completed() void
}
MainWindow --> TaskConfig : "显示"
MainWindow --> TaskQueue : "管理"
TaskQueue --> TaskConfig : "包含"
```

**图表来源**
- [MFAAvalonia/config/config.json](file://MFAAvalonia/config/config.json#L34-L458)

**章节来源**
- [MFAAvalonia/config/config.json](file://MFAAvalonia/config/config.json#L1-L545)

## 架构概览

系统采用分层架构设计，实现了清晰的职责分离：

```mermaid
graph TB
subgraph "用户界面层"
UI[GUI界面<br/>MFAAvalonia]
CLI[命令行界面<br/>Launcher]
end
subgraph "应用服务层"
AG[Agent服务器<br/>Python]
TM[任务管理器<br/>Pipeline执行]
end
subgraph "业务逻辑层"
CF[自定义函数<br/>周期检查/记录]
SF[特殊处理<br/>农场视察流程]
GF[全局功能<br/>计数器/守护进程]
end
subgraph "基础设施层"
FW[MaaFramework<br/>图像识别]
OS[操作系统<br/>ADB/模拟器]
ST[存储系统<br/>本地缓存]
end
UI --> AG
CLI --> AG
AG --> TM
TM --> CF
TM --> SF
TM --> GF
CF --> FW
SF --> FW
GF --> FW
FW --> OS
AG --> ST
```

**图表来源**
- [agent/main.py](file://agent/main.py#L47-L77)
- [MFAAvalonia/config/config.json](file://MFAAvalonia/config/config.json#L1-L545)

## 详细组件分析

### 农场视察任务流程

农场视察是系统中最复杂的任务之一，涉及多个子流程和状态检查。

```mermaid
sequenceDiagram
participant User as 用户
participant GUI as GUI界面
participant Agent as Agent服务器
participant Pipeline as 任务流水线
participant Game as 游戏界面
participant OCR as OCR识别
participant Template as 模板匹配
User->>GUI : 启动农场视察任务
GUI->>Agent : 发送执行请求
Agent->>Pipeline : 加载农场视察流水线
Pipeline->>Game : 进入农场界面
Game->>Template : 检查农场界面
Template-->>Pipeline : 界面识别结果
alt 周期检查通过
Pipeline->>Game : 执行萝卜收取
Game->>OCR : 识别萝卜图标
OCR-->>Pipeline : 萝卜位置
Pipeline->>Game : 点击萝卜收取
Game->>OCR : 确认收取完成
OCR-->>Pipeline : 收取确认
Pipeline->>Game : 检查跑腿状态
Game->>OCR : 识别跑腿奖励
OCR-->>Pipeline : 奖励状态
alt 有跑腿奖励
Pipeline->>Game : 领取跑腿奖励
Game->>OCR : 确认奖励领取
OCR-->>Pipeline : 领取确认
else 无跑腿奖励
Pipeline->>Game : 返回主界面
end
Pipeline->>Agent : 记录周期完成
Agent-->>GUI : 任务完成通知
else 周期检查失败
Pipeline->>GUI : 显示今日已完成
end
```

**图表来源**
- [MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json](file://MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json#L25-L447)

### 依赖管理系统

系统具备智能的依赖检测和安装功能，确保运行环境的完整性。

```mermaid
flowchart TD
Start([启动检查]) --> ReadVersion[读取interface.json版本]
ReadVersion --> CheckLast[检查上次安装版本]
CheckLast --> CompareVersion{版本是否变化?}
CompareVersion --> |是| CheckConfig[检查pip配置]
CompareVersion --> |否| End([跳过安装])
CheckConfig --> EnableInstall{允许自动安装?}
EnableInstall --> |否| End
EnableInstall --> |是| InstallDeps[安装依赖包]
InstallDeps --> InstallSuccess{安装成功?}
InstallSuccess --> |是| UpdateConfig[更新配置文件]
InstallSuccess --> |否| Error[安装失败]
UpdateConfig --> End
Error --> End
```

**图表来源**
- [agent/preprocess/setup.py](file://agent/preprocess/setup.py#L204-L230)

**章节来源**
- [MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json](file://MFAAvalonia/Resource/base/pipeline/日常任务/农场视察.json#L1-L449)
- [agent/preprocess/setup.py](file://agent/preprocess/setup.py#L1-L230)

### 启动流程分析

系统提供了多种启动方式，支持不同环境下的部署需求。

```mermaid
flowchart TD
Launch([程序启动]) --> CheckOS{检测操作系统}
CheckOS --> |Windows| WinPath[查找MFAAvalonia.exe]
CheckOS --> |macOS/Linux| UnixPath[查找MFAAvalonia]
CheckOS --> |其他| ErrorOS[不支持的操作系统]
WinPath --> VerifyWin{验证文件存在}
UnixPath --> VerifyUnix{验证文件存在}
VerifyWin --> |存在| RunWin[运行MFAAvalonia.exe]
VerifyWin --> |不存在| ErrorWin[找不到可执行文件]
VerifyUnix --> |存在| RunUnix[运行MFAAvalonia]
VerifyUnix --> |不存在| ErrorUnix[找不到可执行文件]
RunWin --> AgentInit[初始化Agent服务器]
RunUnix --> AgentInit
AgentInit --> ToolkitInit[初始化Toolkit]
ToolkitInit --> SocketStart[启动Socket服务]
SocketStart --> DevOps[执行devops任务]
DevOps --> WaitExit[等待服务结束]
ErrorOS --> End([启动失败])
ErrorWin --> End
ErrorUnix --> End
```

**图表来源**
- [launcher/MaaDuDuL.py](file://launcher/MaaDuDuL.py#L1-L22)
- [agent/main.py](file://agent/main.py#L47-L77)

**章节来源**
- [launcher/MaaDuDuL.py](file://launcher/MaaDuDuL.py#L1-L22)
- [agent/main.py](file://agent/main.py#L1-L78)

## 依赖关系分析

系统依赖关系复杂但层次清晰，主要依赖包括：

```mermaid
graph TB
subgraph "核心依赖"
MF[MaaFramework 5.7.1] --> Base[基础框架]
REQ[requests 2.32.5] --> HTTP[HTTP客户端]
end
subgraph "GUI依赖"
AV[MFAAvalonia] --> UI[用户界面]
PY[Python] --> Runtime[运行时环境]
end
subgraph "工具依赖"
JSON[JSON配置] --> Config[配置管理]
LOG[日志系统] --> Debug[调试支持]
PIPE[流水线引擎] --> Exec[任务执行]
end
subgraph "游戏交互"
ADB[ADB控制] --> Device[模拟器/设备]
OCR[OCR识别] --> Image[图像处理]
TM[模板匹配] --> Vision[计算机视觉]
end
Base --> MF
HTTP --> REQ
UI --> AV
Runtime --> PY
Config --> JSON
Debug --> LOG
Exec --> PIPE
Device --> ADB
Vision --> OCR
Vision --> TM
```

**图表来源**
- [requirements.txt](file://requirements.txt#L1-L3)

**章节来源**
- [requirements.txt](file://requirements.txt#L1-L3)

## 性能考虑

系统在设计时充分考虑了性能优化：

### 图像识别优化
- 使用模板匹配进行快速界面识别
- OCR识别采用ROI区域限定，提高准确率
- 自定义识别算法减少误判率

### 内存管理
- 采用流式处理避免大内存占用
- 及时释放图像资源和识别结果
- 缓存机制优化重复操作

### 网络通信
- HTTP请求超时控制
- 重试机制防止临时网络错误
- 连接池复用提升效率

## 故障排除指南

### 常见问题及解决方案

**Agent启动失败**
- 检查MaaFramework依赖是否正确安装
- 验证Python环境编码设置
- 查看调试日志获取详细错误信息

**图像识别失败**
- 确认游戏分辨率和缩放设置
- 检查图像资源文件完整性
- 调整OCR识别参数和阈值

**ADB连接问题**
- 验证模拟器/设备连接状态
- 检查ADB路径配置
- 重启ADB服务尝试重新连接

**任务执行异常**
- 查看任务流水线配置
- 检查自定义函数实现
- 验证权限和资源访问

**章节来源**
- [agent/main.py](file://agent/main.py#L69-L71)
- [agent/preprocess/setup.py](file://agent/preprocess/setup.py#L190-L196)

## 结论

Daily Farm Inspection项目展现了现代自动化工具开发的最佳实践。通过合理的架构设计、完善的组件分离和智能化的任务执行机制，成功实现了农场管理的自动化。

项目的主要优势包括：
- **模块化设计**：清晰的职责分离便于维护和扩展
- **智能识别**：结合OCR和模板匹配提高识别准确性
- **用户友好**：提供直观的GUI界面和详细的配置选项
- **稳定可靠**：完善的错误处理和恢复机制

未来可以考虑的功能增强：
- 更多游戏场景的支持
- 机器学习算法的应用
- 实时状态监控和通知
- 多账户并发管理