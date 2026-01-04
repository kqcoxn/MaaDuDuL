# API与接口参考

<cite>
**Referenced Files in This Document**   
- [interface.json](file://assets/interface.json)
- [main.py](file://agent/main.py)
- [MaaDuDuL.py](file://launcher/MaaDuDuL.py)
- [maafw-guide/3.3-ProjectInterfaceV2协议.md](file://instructions/maafw-guide/3.3-ProjectInterfaceV2协议.md)
- [maafw-guide/2.2-集成接口一览.md](file://instructions/maafw-guide/2.2-集成接口一览.md)
- [maafw-guide/2.3-回调协议.md](file://instructions/maafw-guide/2.3-回调协议.md)
- [maafw-guide/3.1-任务流水线协议.md](file://instructions/maafw-guide/3.1-任务流水线协议.md)
- [run_agent.py](file://dev/run_agent.py)
- [maa_pi_config.json](file://assets/config/maa_pi_config.json)
</cite>

## 目录
1. [简介](#简介)
2. [ProjectInterfaceV2协议](#projectinterfacev2协议)
3. [集成接口](#集成接口)
4. [回调协议](#回调协议)
5. [接口配置](#接口配置)
6. [客户端集成最佳实践](#客户端集成最佳实践)
7. [生产环境注意事项](#生产环境注意事项)

## 简介

MaaDuDuL 是基于 MaaFramework 构建的自动化助手，通过 ProjectInterfaceV2 协议对外暴露所有接口与协议。本文档详细描述了集成接口的调用方式、参数定义与返回值格式，包括同步/异步调用模式。文档还解析了回调协议的消息结构、事件类型与处理机制，说明如何监听任务状态变更。结合 interface.json 中的实际配置，说明接口配置项的含义与使用场景。

**Section sources**
- [README.md](file://README.md#L1-L118)

## ProjectInterfaceV2协议

ProjectInterfaceV2 协议是 MaaFramework 的标准化项目结构声明，通过 interface.json 文件定义项目的基本信息、控制器配置、资源加载、任务配置和选项定义。

### 基本信息

interface.json 文件包含项目的基本信息，如项目名称、版本号、描述等。

```json
{
    "interface_version": 2,
    "name": "MaaDuDuL",
    "title": "MDDL 嘟嘟脸小助手(kqcoxn/MaaDuDuL) v0.1.2 - MFAA | 游戏版本：黄油大崩溃",
    "icon": "logo.png",
    "description": "嘟嘟脸小助手",
    "version": "v0.1.2",
    "welcome": "欢迎使用 MDDL!",
    "contact": "QQ群: 926874985",
    "license": "LICENSE",
    "github": "https://github.com/kqcoxn/MaaDuDuL",
    "mirrorchyan_rid": "MaaDuDuL",
    "mirrorchyan_multiplatform": true
}
```

**Diagram sources**
- [interface.json](file://assets/interface.json#L1-L14)

### 控制器配置

控制器配置定义了预设的控制器信息，包括模拟器和 PlayCover。

```json
"controller": [
    {
        "name": "模拟器",
        "type": "Adb",
        "display_short_side": 720
    },
    {
        "name": "PlayCover",
        "type": "PlayCover",
        "display_short_side": 720,
        "playcover": {
            "uuid": "com.bilibili.trickcalcn"
        }
    }
]
```

**Diagram sources**
- [interface.json](file://assets/interface.json#L14-L27)

### 资源配置

资源配置定义了资源加载的信息，包括资源路径和控制器支持。

```json
"resource": [
    {
        "name": "B服",
        "path": ["./resource/base"]
    }
]
```

**Diagram sources**
- [interface.json](file://assets/interface.json#L29-L33)

### 任务配置

任务配置定义了可执行任务的信息，包括任务入口、默认选中状态和描述。

```json
"task": [
    {
        "name": "启动游戏",
        "label": "启动游戏",
        "entry": "启动游戏_开始",
        "default_check": true,
        "description": "Resource/descs/daily/start_game.md"
    },
    {
        "name": "领取邮件",
        "label": "领取邮件",
        "entry": "领取邮件_开始",
        "default_check": true,
        "description": "Resource/descs/daily/claim_mail.md",
        "option": ["领取邮件-周期检查"]
    }
]
```

**Diagram sources**
- [interface.json](file://assets/interface.json#L39-L71)

### 选项配置

选项配置定义了配置项的信息，包括类型、标签和描述。

```json
"option": {
    "领取邮件-周期检查": {
        "type": "switch",
        "label": "每日仅检查一次邮箱",
        "cases": [
            {
                "name": "No",
                "pipeline_override": {
                    "领取邮件_周期检查": {
                        "action": "DoNothing"
                    }
                }
            },
            {
                "name": "Yes"
            }
        ]
    }
}
```

**Diagram sources**
- [interface.json](file://assets/interface.json#L164-L181)

## 集成接口

MaaFramework 提供了多种集成接口，用于创建和管理资源、控制器、任务等。

### 资源管理

#### MaaResourceCreate

创建资源。

**参数**:
- 无

**返回值**:
- `MaaResourceHandle`: 资源句柄

#### MaaResourceDestroy

销毁资源。

**参数**:
- `res`: 资源句柄

#### MaaResourceAddSink

添加资源事件监听器。

**参数**:
- `res`: 资源句柄
- `sink`: 事件回调函数
- `trans_arg`: 传递给回调的参数

**返回值**:
- `MaaResourceId`: 监听器 ID

#### MaaResourceRemoveSink

移除资源事件监听器。

**参数**:
- `res`: 资源句柄
- `sink_id`: 监听器 ID

#### MaaResourceClearSinks

清除所有资源事件监听器。

**参数**:
- `res`: 资源句柄

#### MaaResourcePostBundle

异步加载资源路径下的资源。

**参数**:
- `path`: 资源路径

**返回值**:
- `MaaTaskId`: 操作 ID

#### MaaResourceStatus

查询操作状态。

**参数**:
- `id`: 操作 ID

**返回值**:
- `MaaStatus`: 操作状态

#### MaaResourceWait

等待操作完成。

**参数**:
- `id`: 操作 ID

### 控制器管理

#### MaaAdbControllerCreate

创建 Adb 控制器。

**参数**:
- `adb_path`: adb 路径
- `address`: 连接地址
- `screencap_methods`: 截图方式
- `input_methods`: 输入方式
- `config`: 额外配置
- `agent_path`: MaaAgentBinary 路径

**返回值**:
- `MaaControllerHandle`: 控制器句柄

#### MaaWin32ControllerCreate

创建 Win32 控制器。

**参数**:
- `hWnd`: 窗口句柄
- `screencap_method`: 截图方式
- `mouse_method`: 鼠标输入方式
- `keyboard_method`: 键盘输入方式

**返回值**:
- `MaaControllerHandle`: 控制器句柄

#### MaaControllerAddSink

添加控制器事件监听器。

**参数**:
- `ctrl`: 控制器句柄
- `sink`: 事件回调函数
- `trans_arg`: 传递给回调的参数

**返回值**:
- `MaaResourceId`: 监听器 ID

#### MaaControllerRemoveSink

移除控制器事件监听器。

**参数**:
- `ctrl`: 控制器句柄
- `sink_id`: 监听器 ID

#### MaaControllerClearSinks

清除所有控制器事件监听器。

**参数**:
- `ctrl`: 控制器句柄

#### MaaControllerPostConnection

异步连接设备。

**参数**:
- 无

**返回值**:
- `MaaTaskId`: 操作 ID

#### MaaControllerPostClick

异步点击。

**参数**:
- `x`, `y`: 点击坐标

**返回值**:
- `MaaTaskId`: 操作 ID

#### MaaControllerPostSwipe

异步滑动。

**参数**:
- `x1`, `y1`: 起点坐标
- `x2`, `y2`: 终点坐标
- `duration`: 滑动时长 ms

**返回值**:
- `MaaTaskId`: 操作 ID

#### MaaControllerPostStartApp

异步启动应用。

**参数**:
- `intent`: 目标应用

**返回值**:
- `MaaTaskId`: 操作 ID

#### MaaControllerPostStopApp

异步关闭应用。

**参数**:
- `intent`: 目标应用

**返回值**:
- `MaaTaskId`: 操作 ID

### 任务管理

#### MaaTaskerCreate

创建实例。

**参数**:
- 无

**返回值**:
- `MaaTaskerHandle`: 实例句柄

#### MaaTaskerDestroy

销毁实例。

**参数**:
- `tasker`: 实例句柄

#### MaaTaskerAddSink

添加实例事件监听器。

**参数**:
- `tasker`: 实例句柄
- `sink`: 事件回调函数
- `trans_arg`: 传递给回调的参数

**返回值**:
- `MaaResourceId`: 监听器 ID

#### MaaTaskerRemoveSink

移除实例事件监听器。

**参数**:
- `tasker`: 实例句柄
- `sink_id`: 监听器 ID

#### MaaTaskerClearSinks

清除所有实例事件监听器。

**参数**:
- `tasker`: 实例句柄

#### MaaTaskerBindResource

关联资源。

**参数**:
- `res`: 资源句柄

#### MaaTaskerBindController

关联控制器。

**参数**:
- `ctrl`: 控制器句柄

#### MaaTaskerInited

判断是否正确初始化。

**参数**:
- 无

**返回值**:
- `bool`: 是否初始化成功

#### MaaTaskerPostTask

异步执行任务。

**参数**:
- `entry`: 任务入口
- `pipeline_override`: 用于覆盖的 json

**返回值**:
- `MaaTaskId`: 任务 ID

#### MaaTaskerStatus

查询操作状态。

**参数**:
- `id`: 操作 ID

**返回值**:
- `MaaStatus`: 操作状态

#### MaaTaskerWait

等待操作完成。

**参数**:
- `id`: 操作 ID

### 上下文管理

#### MaaContextRunTask

同步执行任务。

**参数**:
- `entry`: 任务入口
- `pipeline_override`: 用于覆盖的 json

**返回值**:
- `MaaTaskId`: 任务 ID

#### MaaContextRunRecognition

同步执行识别。

**参数**:
- `entry`: 任务名
- `pipeline_override`: 用于覆盖的 json
- `image`: 前序截图

**返回值**:
- `MaaRecoId`: 识别 ID

#### MaaContextRunAction

同步执行操作。

**参数**:
- `entry`: 任务名
- `pipeline_override`: 用于覆盖的 json
- `box`: 前序识别位置
- `reco_detail`: 前序识别详情

**返回值**:
- `MaaActionId`: 操作 ID

**Section sources**
- [maafw-guide/2.2-集成接口一览.md](file://instructions/maafw-guide/2.2-集成接口一览.md#L1-L1015)

## 回调协议

MaaFramework 通过回调函数向上层应用发送各种状态通知和事件消息。所有回调消息都采用统一的格式：消息类型（message）+ 详细数据（details）。

### 消息格式

```cpp
typedef void(MAA_CALL* MaaEventCallback)(void* handle, const char* message, const char* details_json, void* trans_arg);
```

- **handle**: 相关对象的句柄
- **message**: 消息类型字符串，标识事件类型
- **details_json**: JSON 格式的详细数据，包含具体的事件信息
- **callback_arg**: 用户自定义的回调参数

### 消息类型

#### 资源加载消息

用于通知资源加载的状态变化。

- `Resource.Loading.Starting`: 资源开始加载时发送。
- `Resource.Loading.Succeeded`: 资源加载成功时发送。
- `Resource.Loading.Failed`: 资源加载失败时发送。

#### 控制器动作消息

用于通知控制器执行动作的状态。

- `Controller.Action.Starting`: 控制器开始执行动作时发送。
- `Controller.Action.Succeeded`: 控制器动作执行成功时发送。
- `Controller.Action.Failed`: 控制器动作执行失败时发送。

#### 任务消息

用于通知任务执行的状态。

- `Tasker.Task.Starting`: 任务开始执行时发送。
- `Tasker.Task.Succeeded`: 任务执行成功时发送。
- `Tasker.Task.Failed`: 任务执行失败时发送。

#### 节点下一步列表消息

用于通知节点识别下一步节点列表。

- `Node.NextList.Starting`: 节点开始识别下一步节点列表时发送。
- `Node.NextList.Succeeded`: 节点成功识别下一步节点列表时发送。
- `Node.NextList.Failed`: 节点识别下一步节点列表失败时发送。

#### 节点识别消息

用于通知节点识别过程的状态。

- `Node.Recognition.Starting`: 节点开始识别时发送。
- `Node.Recognition.Succeeded`: 节点识别成功时发送。
- `Node.Recognition.Failed`: 节点识别失败时发送。

#### 节点动作消息

用于通知节点执行动作的状态。

- `Node.Action.Starting`: 节点开始执行动作时发送。
- `Node.Action.Succeeded`: 节点动作执行成功时发送。
- `Node.Action.Failed`: 节点动作执行失败时发送。

#### 流水线节点消息

用于通知流水线节点执行的状态。

- `Node.PipelineNode.Starting`: 流水线节点开始执行时发送。
- `Node.PipelineNode.Succeeded`: 流水线节点执行成功时发送。
- `Node.PipelineNode.Failed`: 流水线节点执行失败时发送。

#### 识别节点消息

用于通知识别节点执行的状态。

- `Node.RecognitionNode.Starting`: 识别节点开始执行时发送。
- `Node.RecognitionNode.Succeeded`: 识别节点执行成功时发送。
- `Node.RecognitionNode.Failed`: 识别节点执行失败时发送。

#### 动作节点消息

用于通知动作节点执行的状态。

- `Node.ActionNode.Starting`: 动作节点开始执行时发送。
- `Node.ActionNode.Succeeded`: 动作节点执行成功时发送。
- `Node.ActionNode.Failed`: 动作节点执行失败时发送。

**Section sources**
- [maafw-guide/2.3-回调协议.md](file://instructions/maafw-guide/2.3-回调协议.md#L1-L365)

## 接口配置

### interface.json 配置

interface.json 文件是 ProjectInterfaceV2 协议的核心，定义了项目的各种配置。

#### 基本信息

- `interface_version`: 接口版本号，当前为 2。
- `name`: 项目唯一标识符。
- `title`: 窗口标题。
- `icon`: 应用图标文件路径。
- `description`: 项目描述信息。
- `version`: 项目版本号。
- `contact`: 联系方式信息。
- `license`: 项目许可证信息。
- `welcome`: 欢迎消息。
- `github`: 项目 GitHub 仓库地址。

#### 控制器配置

- `name`: 控制器唯一名称标识符。
- `type`: 控制器类型，取值为 `Adb`、`Win32` 和 `PlayCover`。
- `display_short_side`: 默认缩放分辨率的短边长度。
- `playcover.uuid`: 目标应用的 Bundle Identifier。

#### 资源配置

- `name`: 资源包唯一名称标识符。
- `path`: 加载的路径数组。
- `controller`: 指定该资源包支持的控制器类型列表。

#### 任务配置

- `name`: 任务唯一标识符。
- `label`: 任务显示名称。
- `entry`: 任务入口，为 `pipeline` 中 `Task` 的名称。
- `default_check`: 是否默认选中该任务。
- `description`: 任务详细描述信息。
- `option`: 任务配置项，为一个数组，含有若干后续 `option` 对象中的键的值。

#### 选项配置

- `type`: 配置项类型，可选值为 `"select"`、`"input"` 和 `"switch"`。
- `label`: 配置项显示标签。
- `description`: 配置项详细描述信息。
- `cases`: 仅在 `type` 为 `"select"`/`"switch"` 时使用，可选项，为一个对象数组，含有各个可选项的信息。
- `inputs`: 仅在 `type` 为 `"input"` 时使用，输入配置，为一个对象数组，定义用户可输入的字段。
- `pipeline_override`: 当配置项为 `"input"` 类型时使用，作为用户输入内容的替换模板。

**Section sources**
- [maafw-guide/3.3-ProjectInterfaceV2协议.md](file://instructions/maafw-guide/3.3-ProjectInterfaceV2协议.md#L1-L637)

## 客户端集成最佳实践

### 初始化

1. **创建资源**:
   ```python
   res = MaaResourceCreate()
   ```

2. **创建控制器**:
   ```python
   ctrl = MaaAdbControllerCreate(adb_path, address, screencap_methods, input_methods, config, agent_path)
   ```

3. **创建实例**:
   ```python
   tasker = MaaTaskerCreate()
   ```

4. **关联资源和控制器**:
   ```python
   MaaTaskerBindResource(tasker, res)
   MaaTaskerBindController(tasker, ctrl)
   ```

5. **注册事件监听器**:
   ```python
   MaaTaskerAddSink(tasker, callback, None)
   MaaTaskerAddNodeSink(tasker, callback, None)
   ```

6. **连接设备**:
   ```python
   MaaControllerPostConnection(ctrl)
   ```

### 执行任务

1. **异步执行任务**:
   ```python
   task_id = MaaTaskerPostTask(tasker, entry, pipeline_override)
   ```

2. **同步执行任务**:
   ```python
   task_id = MaaContextRunTask(context, entry, pipeline_override)
   ```

3. **等待任务完成**:
   ```python
   MaaTaskerWait(tasker, task_id)
   ```

4. **获取任务详情**:
   ```python
   detail = MaaTaskerGetTaskDetail(tasker, task_id)
   ```

### 处理回调

1. **注册回调函数**:
   ```python
   def callback(handle, message, details_json, trans_arg):
       # 解析消息类型
       if message == "Tasker.Task.Starting":
           # 处理任务开始事件
           pass
       elif message == "Node.Recognition.Succeeded":
           # 处理识别成功事件
           pass
       # ... 处理其他消息类型
   ```

2. **解析 JSON 数据**:
   ```python
   import json
   details = json.loads(details_json)
   ```

3. **更新 UI**:
   - 根据消息类型更新 UI 显示任务状态。
   - 使用 `details` 中的数据更新识别结果显示。

**Section sources**
- [maafw-guide/3.3-ProjectInterfaceV2协议.md](file://instructions/maafw-guide/3.3-ProjectInterfaceV2协议.md#L570-L633)

## 生产环境注意事项

### 安全考虑

1. **权限管理**:
   - 确保应用程序有足够的权限访问设备和文件系统。
   - 避免在生产环境中使用管理员权限运行应用程序。

2. **数据保护**:
   - 保护用户的敏感数据，如账号密码、设备信息等。
   - 使用加密存储敏感数据。

3. **防篡改**:
   - 验证应用程序的完整性，防止被篡改。
   - 使用数字签名验证应用程序的来源。

### 速率限制

1. **API 调用频率**:
   - 避免频繁调用 API，以免触发速率限制。
   - 使用缓存机制减少不必要的 API 调用。

2. **任务执行频率**:
   - 合理安排任务执行频率，避免对设备造成过大负担。
   - 使用定时任务调度器管理任务执行时间。

### 版本兼容性

1. **向前兼容**:
   - 确保新版本的应用程序能够兼容旧版本的配置文件。
   - 提供版本迁移工具，帮助用户平滑升级。

2. **向后兼容**:
   - 确保旧版本的应用程序能够正常运行新版本的配置文件。
   - 提供详细的版本更新日志，说明变更内容。

3. **测试**:
   - 在发布新版本前进行全面的测试，确保功能正常。
   - 使用自动化测试工具提高测试效率。

**Section sources**
- [README.md](file://README.md#L89-L93)
- [maafw-guide/3.3-ProjectInterfaceV2协议.md](file://instructions/maafw-guide/3.3-ProjectInterfaceV2协议.md#L75-L77)