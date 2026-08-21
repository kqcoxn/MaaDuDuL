---
name: maa-pipeline-option
description: "Add runtime UI options (select/checkbox/switch/input) to MaaFramework option surfaces such as `assets/interface.json` or `assets/resource/tasks/**/*.json`. Use when adding a user-facing toggle, selector, checkbox, or input; wiring options to `pipeline_override`; aligning option paths with Python `context.get_node_data()` or CustomAction params; or reviewing option behavior across Pipeline JSON and Python."
---

# Pipeline Option 工作流

如果选项属于一个尚未定义起始状态、安全边界和验收条件的端到端自动化目标，先交给 `$maa-workflow-build` 建立任务契约；已有契约时，再用本 skill 完成选项接线与局部验证。

## 项目初始化接力

新增选项前先查目标项目根目录的 `basic_info.md`。存在且包含第 0 节时，读取“0. Maa Skills 接力协议”和第 1/2/3/6 节，先确认 interface、resource/task entry、目标节点与 Python 外部调用，再按本 skill 查实际 option surface 和读取路径。文档只是缓存：`pipeline_override`、`context.get_node_data()` 和 Custom 参数路径必须在当前文件中闭环核实。文件缺失或没有第 0 节时按本 skill 直接发现 option surface；不得自动调用 `$maa-project-init`，只有用户明确要求初始化或刷新时才调用。相关源码比文档新时视为缓存可能过期并以源码为准，不自动刷新或覆盖已有非空文档。

## TL;DR：先识别 option surface

新增一个 UI 选项需要先识别本项目使用的 option surface。MaaGumballs 主要是 `assets/interface.json`，M9A 同时使用 `assets/interface.json` 与 `assets/resource/tasks/**/*.json`。不要假设所有 Maa 项目只有一种入口。

常见联动点如下，按项目实际协议取用，缺关键点会导致 UI 看不到选项或运行时读不到值：

| # | 位置 | 内容 |
|---|------|------|
| 1 | option 定义处 | `assets/interface.json` 的 `option` 字典，或 `assets/resource/tasks/**/*.json` 里的 task option 定义 |
| 2 | task 注册处 | `interface.json` task 的 `option: []`，或 tasks JSON 的任务/预设引用 |
| 3 | `assets/resource/base/pipeline/*.json` | **预定义**目标节点（pipeline_override 不会创建节点） |
| 4 | Python 代码（仅 Python 需要读取或执行 Custom 时必需） | `context.get_node_data()`、`argv.custom_action_param`、`argv.custom_recognition_param` 与 option 路径保持一致 |

> ⚠️ **pipeline_override 只做属性合并，不会凭空创建节点。** 少了第 3 步，`context.get_node_data()` 会返回 `None`，运行时静默失败。

完整协议参考（嵌套 option、global_option、controller/resource 限制、占位符注入）：[references/protocol.md](references/protocol.md)

## 历史校正

- **不要把 pure override 当成唯一最佳解**：只改已有节点字段时 pure override 最小；但涉及运行时事件库、计数、动态目标、识别后处理、失败策略、跨节点状态时，CustomAction/CustomRecognition 更合适。
- **不要把 Flag 节点当成唯一配置入口**：M9A 的 v5 object-form 里，参数经常通过 `action.param.custom_action_param`、`custom_action_param_code`、`recognition.param.custom_recognition_param` 进入 Custom；这和 `context.get_node_data("Flag")` 是不同通道。
- **字段路径必须闭环**：UI 写哪条路径，Python 就读哪条路径；pure override 则 Python 不读，直接观察运行时行为。
- **`enabled`/`enable` 不是审美选择**：MaaFramework 原生启停用 `enabled`；历史项目若已有 `enable` helper，可沿用并兼容，否则优先 `enabled`。

---

## 4 种 type 速查

| type | 选择 | override 字段 | 节点预定义形态 |
|------|------|---------------|---------------|
| `select` | 单选互斥 | `expected` | `recognition: "OCR"` + `expected: [...]` |
| `switch` | 二元 Yes/No | `enabled`（或项目已有的 `enable`） | `{"enabled": bool}` / `{"enable": bool}` |
| `input` | 自由文本 | `{name}` 占位符可注入目标字段 | 按最终读取方预定义 `expected` 或 `action.param.custom_action_param` |
| `checkbox` | 多选 | `enabled` | `{"enabled": false}` |

## 选哪个模式？

| 你的需求 | 推荐模式 |
|---------|---------|
| 启用/禁用一个 Python 业务函数 | **A**（switch + Flag 节点 + Python 读 flag） |
| 从多个互斥选项里选一个值 | **B**（select + OCR 节点） |
| 同时启用多个独立的功能模块 | **C**（checkbox + 多个 Flag 节点） |
| 用户输入自定义文本 | **D**（input + 占位符注入） |
| 切换行为（点哪个按钮 / 走哪条 next 链）但不想改 Python | **E**（pure override 现有节点字段） |

> **经验法则**：行为只等于“覆盖已有节点字段”时优先 pure override；一旦需要运行时数据、计数、动态识别、失败策略或跨节点状态，改用 Flag + Python / CustomAction / CustomRecognition。目标是让改动面和逻辑复杂度匹配。

### 先确认代码读取路径

加选项前先 `rg "get_node_data|_node_enabled|Flag_" agent assets`，确认这次配置到底由谁读取。

常见对应关系:

| UI override 写什么 | Python 应该读什么 | 备注 |
|-------------------|-------------------|------|
| `{ "Flag_X": { "enabled": true } }` | `node.get("enabled")` | MaaFramework 标准启停字段 |
| `{ "Flag_X": { "enable": true } }` | `node.get("enable")` 或兼容 helper | 仅用于已有项目约定/历史字段 |
| `{ "SomeOCR": { "expected": ["A"] } }` | `node["recognition"]["param"]["expected"][0]` | 节点必须预定义为 OCR |
| `{ "SomeNode": { "next": ["A"] } }` | 不读，直接由 pipeline 行为生效 | pure override 模式 |

**不要字段错位**：例如 UI 写 `AutoSky_CloneConfig.enable`，Python 却调用读取 `expected` 的函数；或 UI 写 `expected`，Python 只看 `enabled`。这种错误不会报 JSON 语法错，但运行时会表现为"选项没生效"。

### 启停节点必须短路调用

如果同一个节点既保存 `enable`/`enabled` 开关，又是可执行的 Recognition/Action 节点，先读取开关，只有开启时才调用它。关闭节点后继续检查同级候选分支，不能调用已关闭节点，也不能因为开关值直接 `continue` 整个事件扫描。

```python
if _node_enabled(context, "OptionalNode"):
    result = context.run_recognition("OptionalNode", image)
    if result and result.hit:
        context.run_task("OptionalNode")
        continue

# OptionalNode 关闭或未命中，继续识别 CombatNode、ExploreNode 等同级分支。
```

---

## 完整模式示例

需要 switch、select、checkbox、input、pure override 或流程型选项的完整代码时，读取 [references/patterns.md](references/patterns.md)。

## 命名与默认值

### 命名约定

| 角色 | 风格 | 示例 |
|------|------|------|
| option 名（用户可见） | 中文动词起头 | `开启5月城堡相亲`、`选择刷取任务国家` |
| 节点名（pipeline） | 英文 | `Flag_EnableMarryTask`、`EnterCity`、`检测_科内塔之怒` |
| switch case 名 | **严格 `Yes` / `No`** | 不要用 `true/false` 或 `是/否`（Client 解析跨平台不一致） |

### 默认值策略

> **保持现有行为是底线。** 老用户不该因新选项而行为改变。

| 场景 | 推荐 default |
|------|-------------|
| 新开关让功能默认关闭 | `No`（明确告知用户"关了"） |
| 新开关让功能默认开启 | `Yes`（保留旧行为） |
| 旧代码无条件开启 | `Yes`（兼容） |
| 旧代码无条件关闭 | `No`（兼容） |

---

## 读取位置

| 决策类型 | 放哪读 | 理由 |
|---------|-------|------|
| 是否执行某段流程 | 业务函数入口 `handle_xxx` | 与现有同名函数风格一致，子函数自治 |
| 用哪个值做主逻辑 | 任务入口 `run` 或 `YearlyTaskProcessor` | 一次读取、多次复用 |

> **反例**：不要把"是否开启 X"的判断堆在通用 `dispatch` 函数（如 `handle_festival_by_month`）里。每加一个开关 dispatch 就多一个 `if-elif`，越来越臃肿。

---

## ✅ 推荐做法

1. **先复用现有模式**：参考同项目里现成的同类选项（开关 → `开启5月城堡相亲`；选择 → `选择刷取任务国家`）
2. **3 处同步改完再跑**：不要中途停下来"先编译试试"
3. **JSON 改完跑资源加载检查**：本仓库与 M9A 的真实路径是 `python tools/ci/check_resource.py assets/resource/base`；如果目标项目路径不同，先用 `Get-ChildItem tools -Recurse -Filter check_resource.py` 发现真实脚本。pipeline 加载错误（如重复 key）会立刻报
4. **默认值遵循现状**：选项是"开"还是"关"取决于旧代码行为，不是你的偏好
5. **在 task 的 `doc` 数组里加一行说明**：用户能看懂每个选项的作用
6. **让 option 通道匹配实际复杂度**：行为只动已有 pipeline 字段时用 pure override；Python 需要做真实判断、计数、动态识别或安全策略时，用 Flag + Python / CustomAction / CustomRecognition，不要为了少写 Python 把复杂逻辑硬塞进 JSON。

---

## 反模式

实现或审查 option 时读取 [references/anti-patterns.md](references/anti-patterns.md)，逐项排除常见的接线与状态机错误。

## 验证流程

改完一次完整流程，**按顺序**做这 4 步：

1. **JSON 语法检查**

   ```bash
   python -c "import json; json.load(open('assets/interface.json', encoding='utf-8'))"
   python -c "import json; json.load(open('assets/resource/base/pipeline/auto_task.json', encoding='utf-8'))"
   ```

2. **资源加载检查**

   ```bash
   python tools/ci/check_resource.py assets/resource/base
   ```

   期望输出 `All directories checked.`

3. **Pipeline 节点测试**（可选）

   ```python
   data = context.get_node_data("Flag_EnableSailingFestivalPurchase")
   assert data is not None, "节点未预定义"
   assert "enabled" in data
   ```

4. **端到端验证**：用 Pipeline Testing Skill 跑一次实际流程

---

## 完整协议

更多 type 字段、嵌套 option、global_option、controller/resource 限制、`{占位符}` 注入机制等高级特性见 [references/protocol.md](references/protocol.md)。
