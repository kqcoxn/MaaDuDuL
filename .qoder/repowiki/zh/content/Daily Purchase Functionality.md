# 日常采购功能文档

<cite>
**本文档引用的文件**
- [purchase.json](file://assets/resource/tasks/daily/purchase.json)
- [purchase.md](file://assets/resource/descs/daily/purchase.md)
- [store.py](file://agent/customs/special_treat/store.py)
- [clear_red_candy.json](file://assets/resource/tasks/daily/clear_red_candy.json)
- [clear_purple_candy.json](file://assets/resource/tasks/daily/clear_purple_candy.json)
- [clear_red_candy.md](file://assets/resource/descs/daily/clear_red_candy.md)
- [clear_purple_candy.md](file://assets/resource/descs/daily/clear_purple_candy.md)
- [default_pipeline.json](file://assets/resource/base/default_pipeline.json)
</cite>

## 更新摘要
**变更内容**
- 新增糖果采购功能模块，包括红糖和紫糖购买选项
- 添加周期检查机制，防止重复购买
- 更新商店采购系统以支持糖果购买
- 新增专门的糖果清理任务（清红糖、清紫糖）

## 目录
1. [简介](#简介)
2. [项目结构概览](#项目结构概览)
3. [核心组件分析](#核心组件分析)
4. [架构设计](#架构设计)
5. [详细功能分析](#详细功能分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [故障排除指南](#故障排除指南)
9. [结论](#结论)

## 简介

日常采购功能是MaaDuDuL自动化框架中的一个核心日常任务模块，专门负责处理游戏中的每日免费礼包领取和商店采购操作。该功能通过高度模块化的配置系统，实现了对各种商店类型的智能识别和自动化操作。

**更新** 新增了糖果采购功能，包括红糖和紫糖的购买选项，以及相应的周期检查机制。

该功能具有以下特点：
- 支持多种免费礼包类型（每日、每周、每月）
- 覆盖多个商店类型（日常商店、战斗宝石商店、尊享商店等）
- **新增** 支持糖果采购（红糖、紫糖）
- 提供灵活的采购模式（逐个购买、一键购买）
- 具备完善的错误处理和状态监控机制
- **新增** 周期检查机制，防止重复操作

## 项目结构概览

日常采购功能在项目中的组织结构如下：

```mermaid
graph TB
subgraph "日常任务模块"
DailyTask[日常任务配置]
Purchase[每日采购任务]
FreeGift[免费礼包系统]
Store[商店管理系统]
Candy[糖果采购系统]
end
subgraph "配置文件"
TaskConfig[每日采购.json]
DescConfig[purchase.md]
PipelineConfig[default_pipeline.json]
end
subgraph "自定义动作"
GiftAction[礼包领取动作]
BuyAction[商品购买动作]
CandyAction[糖果购买动作]
end
subgraph "糖果清理任务"
RedCandy[清红糖任务]
PurpleCandy[清紫糖任务]
end
DailyTask --> Purchase
Purchase --> FreeGift
Purchase --> Store
Purchase --> Candy
Purchase --> TaskConfig
TaskConfig --> DescConfig
TaskConfig --> PipelineConfig
Store --> GiftAction
Store --> BuyAction
Candy --> CandyAction
RedCandy --> RedCandy
PurpleCandy --> PurpleCandy
```

**图表来源**
- [purchase.json:1-584](file://assets/resource/tasks/daily/purchase.json#L1-L584)
- [store.py:138-186](file://agent/customs/special_treat/store.py#L138-L186)

**章节来源**
- [purchase.json:1-584](file://assets/resource/tasks/daily/purchase.json#L1-L584)
- [purchase.md:1-13](file://assets/resource/descs/daily/purchase.md#L1-L13)

## 核心组件分析

### 任务配置系统

日常采购功能采用JSON配置驱动的方式，通过复杂的嵌套结构实现精细化的功能控制：

```mermaid
classDiagram
class PurchaseTask {
+string name
+string label
+string entry
+boolean default_check
+string description
+array option
}
class OptionConfig {
+string type
+string label
+array cases
+object pipeline_override
+array option
}
class CaseConfig {
+string name
+string action
+string next
+object pipeline_override
}
class CandyConfig {
+string type
+string label
+string description
+array cases
+array option
}
PurchaseTask --> OptionConfig : contains
OptionConfig --> CaseConfig : has multiple
PurchaseTask --> CandyConfig : contains
```

**图表来源**
- [purchase.json:13-583](file://assets/resource/tasks/daily/purchase.json#L13-L583)

### 自定义动作模块

系统提供了三个核心的自定义动作类来处理具体的业务逻辑：

```mermaid
classDiagram
class Gift {
+run(context, argv) bool
-ParamAnalyzer args
-Tasker tasker
-Prompter logger
}
class Buy {
+run(context, argv) bool
-ParamAnalyzer args
-Tasker tasker
-Prompter logger
}
class BuyCandy {
+run(context, argv) bool
-ParamAnalyzer args
-Tasker tasker
-Prompter logger
}
class CustomAction {
<<interface>>
+run(context, argv) bool
}
class Tasker {
+run(pipeline_name, expected_map) bool
}
class ParamAnalyzer {
+get(valid_names) string
}
Gift --|> CustomAction
Buy --|> CustomAction
BuyCandy --|> CustomAction
Gift --> Tasker : uses
Buy --> Tasker : uses
BuyCandy --> Tasker : uses
Gift --> ParamAnalyzer : uses
Buy --> ParamAnalyzer : uses
BuyCandy --> ParamAnalyzer : uses
```

**图表来源**
- [store.py:16-98](file://agent/customs/special_treat/store.py#L16-L98)
- [store.py:138-186](file://agent/customs/special_treat/store.py#L138-L186)

**章节来源**
- [store.py:1-186](file://agent/customs/special_treat/store.py#L1-L186)

## 架构设计

### 整体架构图

```mermaid
graph TB
subgraph "用户界面层"
UI[用户配置界面]
Config[任务配置界面]
CandyUI[糖果采购界面]
end
subgraph "业务逻辑层"
PurchaseEngine[采购引擎]
GiftSystem[礼包系统]
StoreSystem[商店系统]
CandySystem[糖果系统]
end
subgraph "数据访问层"
TaskConfig[任务配置存储]
PipelineConfig[管道配置存储]
LogStorage[日志存储]
CandyLog[Candy状态存储]
end
subgraph "外部接口"
GameInterface[游戏界面]
OCRService[OCR识别服务]
ImageProcessor[图像处理服务]
end
UI --> Config
Config --> PurchaseEngine
CandyUI --> CandySystem
PurchaseEngine --> GiftSystem
PurchaseEngine --> StoreSystem
PurchaseEngine --> CandySystem
GiftSystem --> TaskConfig
StoreSystem --> TaskConfig
CandySystem --> TaskConfig
PurchaseEngine --> PipelineConfig
PurchaseEngine --> LogStorage
CandySystem --> CandyLog
StoreSystem --> GameInterface
GiftSystem --> GameInterface
CandySystem --> GameInterface
StoreSystem --> OCRService
StoreSystem --> ImageProcessor
```

**图表来源**
- [purchase.json:478-583](file://assets/resource/tasks/daily/purchase.json#L478-L583)
- [store.py:138-186](file://agent/customs/special_treat/store.py#L138-L186)

### 数据流架构

```mermaid
sequenceDiagram
participant User as 用户
participant Config as 配置系统
participant Engine as 采购引擎
participant Store as 商店系统
participant Candy as 糖果系统
participant Game as 游戏界面
User->>Config : 设置采购选项
Config->>Engine : 加载配置
Engine->>Store : 初始化商店连接
Engine->>Candy : 初始化糖果连接
Store->>Game : 检测商店界面
Candy->>Game : 检测糖果界面
Game-->>Store : 返回商店状态
Game-->>Candy : 返回糖果状态
Store->>Engine : 报告可用商品
Candy->>Engine : 报告可用糖果
Engine->>Store : 执行购买操作
Engine->>Candy : 执行糖果购买
Store->>Game : 完成购买流程
Candy->>Game : 完成糖果购买
Game-->>Store : 返回结果
Game-->>Candy : 返回结果
Store-->>Engine : 返回购买结果
Candy-->>Engine : 返回购买结果
Engine-->>User : 显示最终状态
```

**图表来源**
- [purchase.json:478-583](file://assets/resource/tasks/daily/purchase.json#L478-L583)
- [store.py:138-186](file://agent/customs/special_treat/store.py#L138-L186)

## 详细功能分析

### 免费礼包系统

系统支持三种不同周期的免费礼包：

| 礼包类型 | 周期频率 | 触发条件 | 特殊功能 |
|---------|---------|---------|----------|
| 每日免费礼包 | 每日 | 服务器时间变化 | 周期检查、重复领取保护 |
| 每周免费礼包 | 每周 | 星期一凌晨 | 周期检查、自动重置 |
| 每月免费礼包 | 每月 | 每月1日凌晨 | 周期检查、月份验证 |

### 商店采购系统

系统支持四种主要商店类型：

```mermaid
flowchart TD
Start([开始采购流程]) --> CheckStore{检查商店类型}
CheckStore --> |日常商店| DailyStore[日常商店]
CheckStore --> |战斗宝石商店| GemStore[战斗宝石商店]
CheckStore --> |尊享商店| PremiumStore[尊享商店]
CheckStore --> |每周免费礼包| WeeklyGift[每周免费礼包]
CheckStore --> |糖果商店| CandyStore[Candy商店]
DailyStore --> CheckMode{检查采购模式}
CheckMode --> |逐个购买| IndividualBuy[逐个购买模式]
CheckMode --> |一键购买| BulkBuy[一键购买模式]
IndividualBuy --> SelectItem[选择具体商品]
SelectItem --> ConfirmPurchase[确认购买]
GemStore --> BuyItems[直接购买物品]
PremiumStore --> CheckGift{检查是否有礼包}
CheckGift --> |有礼包| ClaimGift[领取礼包]
CheckGift --> |无礼包| SkipGift[跳过]
WeeklyGift --> ClaimWeekly[领取每周礼包]
BulkBuy --> AutoSelect[自动选择物品]
AutoSelect --> ConfirmPurchase
BuyItems --> ConfirmPurchase
ClaimGift --> ConfirmPurchase
SkipGift --> End([结束])
CandyStore --> CheckCandyType{检查糖果类型}
CheckCandyType --> |红糖| RedCandy[购买红糖]
CheckCandyType --> |紫糖| PurpleCandy[购买紫糖]
RedCandy --> InputCount[输入购买数量]
InputCount --> ConfirmCandy[确认购买]
PurpleCandy --> InputCount
ConfirmCandy --> End
End --> End([结束])
```

**图表来源**
- [purchase.json:186-202](file://assets/resource/tasks/daily/purchase.json#L186-L202)
- [purchase.json:478-583](file://assets/resource/tasks/daily/purchase.json#L478-L583)

### 糖果采购系统

**新增** 系统现在支持红糖和紫糖的购买：

#### 红糖购买
- **适用场景**：获取基础培养材料
- **购买位置**：糖果商店右侧区域
- **参数支持**：数量输入（默认3次）
- **周期检查**：每日仅检查一次

#### 紫糖购买  
- **适用场景**：获取高级培养材料
- **购买位置**：糖果商店左侧区域
- **参数支持**：数量输入（默认3次）
- **周期检查**：每日仅检查一次

#### 周期检查机制
- **每日检查**：防止重复购买同一天的糖果
- **状态记录**：本地存储购买状态
- **智能跳过**：已购买则自动跳过

### 商品采购模式

系统提供两种不同的采购模式：

#### 逐个购买模式
- **适用场景**：需要精确控制购买的商品
- **优势**：完全可控，可以针对特定商品进行优化
- **劣势**：操作步骤较多，耗时较长
- **典型商品**：朱珠糖、星星糖、锻造书、魔卡龙等

#### 一键购买模式
- **适用场景**：批量购买预设的商品组合
- **优势**：操作简便，效率高
- **劣势**：需要预先配置好购买清单
- **使用要求**：需要用户自行勾选要购买的物品

**章节来源**
- [purchase.json:478-583](file://assets/resource/tasks/daily/purchase.json#L478-L583)

## 依赖关系分析

### 组件依赖图

```mermaid
graph TB
subgraph "核心依赖"
MAAFramework[MAA Framework]
PythonRuntime[Python Runtime]
JSONParser[JSON解析器]
end
subgraph "内部模块"
TaskManager[任务管理器]
ConfigLoader[配置加载器]
ActionExecutor[动作执行器]
StateManager[状态管理器]
CandyStateManager[Candy状态管理器]
end
subgraph "工具模块"
Prompter[提示器]
ParamAnalyzer[参数分析器]
Tasker[任务调度器]
CandyChecker[Candy检查器]
end
subgraph "外部服务"
GameAPI[游戏API]
OCRService[OCR服务]
ImageRecognition[图像识别]
end
MAAFramework --> TaskManager
PythonRuntime --> ConfigLoader
JSONParser --> ConfigLoader
TaskManager --> ActionExecutor
TaskManager --> StateManager
ActionExecutor --> Prompter
ActionExecutor --> ParamAnalyzer
ActionExecutor --> Tasker
StateManager --> CandyStateManager
CandyStateManager --> CandyChecker
ActionExecutor --> GameAPI
ActionExecutor --> OCRService
ActionExecutor --> ImageRecognition
```

**图表来源**
- [store.py:6-13](file://agent/customs/special_treat/store.py#L6-L13)

### 配置依赖关系

```mermaid
erDiagram
DAILY_PURCHASE {
string task_name
string entry_point
boolean default_check
string description_ref
}
OPTION_CONFIG {
string option_name
string option_type
string label
array cases
object pipeline_override
}
CASE_CONFIG {
string case_name
string action
string next
object pipeline_override
}
CANDY_CONFIG {
string candy_type
string candy_label
string candy_description
array candy_cases
}
PIPELINE_CONFIG {
string pipeline_name
string action
string next
object expected_map
}
DAILY_PURCHASE ||--o{ OPTION_CONFIG : contains
OPTION_CONFIG ||--o{ CASE_CONFIG : has
CASE_CONFIG ||--o{ PIPELINE_CONFIG : creates
DAILY_PURCHASE ||--o{ CANDY_CONFIG : contains
```

**图表来源**
- [purchase.json:13-583](file://assets/resource/tasks/daily/purchase.json#L13-L583)

**章节来源**
- [default_pipeline.json:1-8](file://assets/resource/base/default_pipeline.json#L1-L8)

## 性能考虑

### 执行效率优化

日常采购功能在设计时充分考虑了执行效率：

1. **智能跳过机制**：通过周期检查避免重复操作
2. **批量处理**：一键购买模式减少交互次数
3. **缓存策略**：状态信息本地缓存减少重复查询
4. **并发控制**：合理的时间间隔设置避免过度频繁的操作
5. ****新增** 周期检查优化**：糖果采购的周期检查减少不必要的界面切换

### 资源管理

- **内存使用**：配置信息按需加载，避免内存占用过高
- **网络带宽**：OCR识别和图像处理采用本地化方案
- **CPU占用**：异步处理机制减少主线程阻塞
- ****新增** 状态存储优化**：糖果状态本地持久化减少重复查询

## 故障排除指南

### 常见问题及解决方案

| 问题类型 | 症状描述 | 可能原因 | 解决方案 |
|---------|---------|---------|---------|
| 配置加载失败 | 任务无法启动 | JSON格式错误或文件缺失 | 检查配置文件语法，确保文件存在 |
| 商店识别失败 | 无法进入商店界面 | OCR识别错误或界面变化 | 调整OCR参数，更新界面识别规则 |
| 购买操作超时 | 购买流程中断 | 网络延迟或游戏响应慢 | 增加超时等待时间，检查网络连接 |
| 礼包领取失败 | 礼包无法领取 | 礼包已过期或已被领取 | 检查礼包状态，重新触发领取流程 |
| **新增** 糖果购买失败 | 糖果无法购买 | 糖果界面未正确识别 | 检查周期检查状态，重新初始化界面 |
| **新增** 数量输入错误 | 购买数量不正确 | 输入格式错误或超出范围 | 验证输入格式，确保为正整数 |

### 错误处理机制

系统采用多层次的错误处理策略：

```mermaid
flowchart TD
Start([操作开始]) --> TryOperation{尝试执行操作}
TryOperation --> |成功| Success[操作成功]
TryOperation --> |失败| CheckError{检查错误类型}
CheckError --> |网络错误| RetryNetwork[重试网络操作]
CheckError --> |界面错误| RefreshUI[刷新界面状态]
CheckError --> |参数错误| ValidateParams[验证输入参数]
CheckError --> |周期检查错误| ResetCycle[重置周期状态]
CheckError --> |未知错误| LogError[记录错误日志]
RetryNetwork --> Reconnect[重新连接]
RefreshUI --> ResetState[重置状态]
ValidateParams --> FixParams[修正参数]
ResetCycle --> Recheck[重新检查]
LogError --> ReportError[报告错误]
Reconnect --> TryOperation
ResetState --> TryOperation
FixParams --> TryOperation
Recheck --> TryOperation
ReportError --> End([结束])
Success --> End
```

**图表来源**
- [store.py:48-52](file://agent/customs/special_treat/store.py#L48-L52)
- [store.py:184-186](file://agent/customs/special_treat/store.py#L184-L186)

**章节来源**
- [store.py:138-186](file://agent/customs/special_treat/store.py#L138-L186)

## 结论

日常采购功能作为MaaDuDuL自动化框架的重要组成部分，展现了现代自动化系统的几个关键特征：

1. **模块化设计**：通过清晰的组件分离实现了高度的可维护性和可扩展性
2. **配置驱动**：灵活的配置系统使得功能可以根据需求进行定制
3. **错误处理**：完善的异常处理机制确保了系统的稳定运行
4. **用户体验**：直观的界面设计和详细的帮助文档提升了用户的使用体验
5. ****新增** 周期管理**：智能的周期检查机制避免了重复操作，提高了效率

**更新** 最新的糖果采购功能为用户提供了更丰富的自动化选项，包括红糖和紫糖的购买能力，以及相应的周期检查机制。这不仅扩展了系统的功能范围，也体现了MaaDuDuL在游戏自动化领域的持续创新和发展。

该功能的成功实施为类似的游戏自动化任务提供了良好的参考模板，其设计理念和实现方法值得在其他自动化项目中借鉴和应用。