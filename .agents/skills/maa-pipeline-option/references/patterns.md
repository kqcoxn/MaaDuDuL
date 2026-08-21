# Maa Pipeline Option Patterns

## Contents

- 模式 A：switch + Flag 节点
- 模式 B：select + OCR 节点
- 模式 C：checkbox + 多个 Flag 节点
- 模式 D：input + 占位符注入
- 模式 E：pure override
- 状态机与流程型选项

## 模式 A：开关（switch + Flag 节点）— 最常用

**适用**：开启/关闭某个功能。

### interface.json

```jsonc
"开启5月城堡相亲": {
    "type": "switch",
    "description": "是否开启5月自动相亲",
    "default_case": "Yes",
    "cases": [
        {
            "name": "Yes",
            "pipeline_override": { "Flag_EnableMarryTask": { "enabled": true } }
        },
        {
            "name": "No",
            "pipeline_override": { "Flag_EnableMarryTask": { "enabled": false } }
        }
    ]
}
```

### 配套 pipeline 节点（必须预定义！）

```jsonc
"Flag_EnableMarryTask": { "enabled": true }
```

> 若项目历史节点使用 `enable` 而非 `enabled`，必须同时保证 Python 侧有兼容读取，例如 `node.get("enable", node.get("enabled", True))`。否则优先使用协议字段 `enabled`。

### 注册到 task

```jsonc
"task": [{
    "name": "推年计划",
    "entry": "Auto_YearlyTask",
    "option": ["开启5月城堡相亲", /* 其他选项 */]
}]
```

### Python 读取（建议放在业务函数入口）

```python
def handle_marry_festival(context: Context) -> bool:
    """处理春林节相亲（5月）"""
    EnableMarryTask = context.get_node_data("Flag_EnableMarryTask").get("enabled")
    if not EnableMarryTask:
        logger.info("自动相亲已关闭，跳过")
        return True
    # ... 正常逻辑
```

---

## 模式 B：单选（select + OCR 节点）

**适用**：选择城市、关卡、模式等互斥选项。

### interface.json

```jsonc
"选择刷取任务国家": {
    "type": "select",
    "description": "选择要刷取任务的目标城市",
    "default_case": "雄月城",
    "cases": [
        { "name": "王座堡", "pipeline_override": { "EnterCity": { "expected": ["王座堡"] } } },
        { "name": "雄月城", "pipeline_override": { "EnterCity": { "expected": ["雄月城"] } } }
    ]
}
```

### 配套 OCR 节点

```jsonc
"EnterCity": {
    "recognition": "OCR",          // ⚠️ 必须是 OCR，否则 expected 不生效
    "expected": ["王座堡", "圣盾堡", "雄月城", "翠庭"],
    "roi": [58, 320, 600, 682],
    "action": "Click"
}
```

### Python 读取

```python
data = context.get_node_data("EnterCity")
city = data.get("recognition", {}).get("param", {}).get("expected", ["王座堡"])[0]
```

---

## 模式 C：多选（checkbox + 多个 Flag 节点）

**适用**：多条件检测（好苗子条件）、可叠加的功能模块。

### interface.json

```jsonc
"开启好娃提醒": {
    "type": "checkbox",
    "default_case": ["科内塔之怒"],
    "cases": [
        { "name": "科内塔之怒",   "pipeline_override": { "检测_科内塔之怒":     { "enabled": true } } },
        { "name": "太阳+科内塔之怒", "pipeline_override": { "检测_太阳+科内塔之怒": { "enabled": true } } }
    ]
}
```

### 配套节点（每个 case 一个，默认全 false）

```jsonc
"检测_科内塔之怒":      { "expected": ["koneita"],            "enabled": false },
"检测_太阳+科内塔之怒": { "expected": ["sun_and_koneita"],    "enabled": false }
```

### Python 读取（遍历收集）

```python
def _get_enabled_checks(context) -> list:
    enabled = []
    for key in ["检测_科内塔之怒", "检测_太阳+科内塔之怒"]:
        node = context.get_node_data(key)
        if node and node.get("enabled", False):
            expected = node.get("recognition", {}).get("param", {}).get("expected", [])
            if expected:
                enabled.append(expected[0])
    return enabled
```

---

## 模式 D：自由输入（input + 占位符注入）

**适用**：用户输入自定义关卡号、自定义黑名单任务等。`input` 只是 UI surface；占位符可以注入 `expected` 或 `action.param.custom_action_param`，最终路径由消费方决定。

### interface.json

```jsonc
"自定义任务黑名单": {
    "type": "input",
    "inputs": [
        {
            "name": "任务名称",
            "pipeline_type": "string",
            "default": "",
            "verify": "^[^,，]*$",
            "pattern_msg": "不能包含逗号"
        }
    ],
    "pipeline_override": {
        "CustomTaskBlacklist": {
            "expected": ["{任务名称}"]   // {名称} 占位符被实际输入替换
        }
    }
}
```

### Python 读取

```python
data = context.get_node_data("CustomTaskBlacklist")
value = data.get("recognition", {}).get("param", {}).get("expected", [""])[0]
```

### ⚠️ 常见错误:混淆 `get_node_data()` 和 CustomAction 参数通道

`custom_action_param` 可以用，但要读对地方：

- 如果参数是给当前 CustomAction 执行时使用，写入 `action.param.custom_action_param`，在 Python 里读 `argv.custom_action_param`。
- 如果参数是给普通业务代码提前读取，写到一个预定义节点的 `recognition.param.expected`、`enabled`、`enable` 或其他明确字段，再用 `context.get_node_data("Node")` 读取对应路径。
- 不要把用户输入塞到 `pipeline_override.custom_action_param` 后，再用 `get_node_data("X").get("custom_action_param")` 读顶层字段；这两个不是同一条通道。

**错误信号**：UI 显示已选择，但 Python 读到默认值或 `None`。排查时打印完整 `context.get_node_data("X")`，确认字段实际落点。

---

## 模式 E：行为覆盖（pure override 现有节点字段）— 最简

**适用**：行为切换映射到现有 pipeline 节点的**单个字段**（`next` 数组 / `action` 类型 / `recognition` 算法 / 任何可覆盖字段），且**不需要 Python 判断**。

**核心思路**：用户切换 UI 选项 → 改变 pipeline 节点的字段值 → 框架自身根据新值执行。**Python 代码完全不动。**

### 典型场景：开关决定点哪个按钮

```jsonc
"开启自动接受佣兵": {
    "type": "switch",
    "default_case": "No",
    "cases": [
        {
            "name": "Yes",
            "description": "直接点确认",
            "pipeline_override": {
                "Event_MercenaryJoin": {
                    "next": ["Event_MercenaryJoinConfirm"]
                }
            }
        },
        {
            "name": "No",
            "description": "直接点取消",
            "pipeline_override": {
                "Event_MercenaryJoin": {
                    "next": ["Event_MercenaryJoinCancel"]
                }
            }
        }
    ]
}
```

`Event_MercenaryJoin` 节点本身在 [event_utils.json](../../assets/resource/base/pipeline/event_utils.json) 里有完整定义（`recognition` / `expected` / `roi` / `timeout` 都在），`pipeline_override` 只覆盖 `next` 字段，其他字段保持原值。

### `next` 数组的单元素 vs 多元素语义

| 写法 | 语义 | 何时用 |
|------|------|-------|
| `["A"]` | **强约束**：只走 A | 行为已确定，单路径足够（**模式 E 的典型形态**） |
| `["A", "B"]` | **回退链**：优先 A，A 失败走 B | 兜底机制（"优先点确认，找不到才点取消"） |
| `["A", "B", "[JumpBack]C"]` | 失败后跳回 C 节点重试 | 复杂回退 |

### 可被 override 的字段

| 字段 | override 效果 | 典型用途 |
|------|--------------|---------|
| `next` | 改变后续节点列表 | 切换行为路径（模式 E 主力） |
| `action` | 改变点击/滑动/输入动作 | 切换操作类型 |
| `recognition` | 改变识别算法 | 切换识别方式（OCR ↔ Template） |
| `expected` | 改变识别期望值 | 配合 select 选值 |
| `roi` | 改变识别区域 | 适配不同界面尺寸 |
| `timeout` | 改变超时时间 | 适配不同网络/性能 |

> **关键认识**：上面这些字段都是普通 JSON 值，pipeline_override 一视同仁做深合并。**模式 A 用的 `enabled` 字段只是最常见的入口，不是唯一可 override 的字段。**

### 模式 A vs 模式 E 对比

| 场景 | 模式 A（Flag + Python） | 模式 E（pure override） |
|------|------------------------|----------------------|
| 行为由 Python `if` 控制 | ✅ 必须 | ❌ 绕远路 |
| 行为由 pipeline 字段决定 | ❌ 多此一举 | ✅ 最简 |
| 需要运行时根据 flag 走不同代码分支 | ✅ 唯一选择 | ❌ 不行 |
| 改动 Python 代码 | ✅ 需要 | ❌ 不需要 |
| 需要新加 Flag 节点 | ✅ 需要 | ❌ 不需要 |

### 实战决策流程

```
要加新选项
│
├─ 行为切换对应到一个 pipeline 节点的某个字段？
│   └─ ✅ 用模式 E（pure override）
│       示例：佣兵加入时点"确认"还是"取消"
│
└─ ❌ 行为在 Python 业务逻辑里
    └─ 用模式 A（Flag 节点 + Python 读 flag）
        示例：跳过整个 handle_sailing_festival 函数
```

---

## 补充：能用状态机就别写 Python orchestration

**MaaFramework 的 `next` + `[JumpBack]` 是为跨页面状态推进设计的原语**。如果一个流程的步骤可以**列举**为有限个页面状态（入口 → A → B → C → 战斗），优先用 JSON 状态机；不要写 Python 把 `context.run_task` 串起来。

详见 [maa-pipeline-guide](../../maa-pipeline-guide/SKILL.md) 的「跨页面状态机」典型模式。

### 状态机 vs Python orchestration 对比

| 场景 | 状态机（推荐） | Python orchestration（次选） |
|------|--------------|--------------------------|
| 有限页面状态推进（如活动流程） | ✅ 链 `next` + `[JumpBack]` | ❌ 自己写 `for/while` 调度 |
| 按 flag 跳过整段函数 | ❌ 不适合 | ✅ 读 flag + 早返回 |
| 复杂的运行时分支逻辑 | ❌ 难表达 | ✅ Python 灵活 |

### 跨文件节点引用的测试陷阱

MaaFramework 全局加载时，所有 `assets/resource/base/pipeline/*.json` 会合并到同一命名空间，所以 `[JumpBack]OtherFileNode` 能解析。但 `run_pipeline` 测试工具**只加载单文件**，跨文件引用会报"加载 Pipeline 失败"。

**应对**：
- 集成测试必须用 MaaFramework GUI / CLI 触发，不能依赖 `run_pipeline`
- 单元测试每个节点用 `run_pipeline` 是 OK 的（无跨文件依赖）
- 若某个流程有跨文件引用，本地调试时考虑用 `MaaCli` 跑全 bundle

---

## 补充：状态机驱动的「流程型选项」

如果一个 UI 选项代表的是**进入某个跨页面流程**（如"开启成长试炼"→ 大地图 → 难度选择 → 队伍 → 战斗），把选项的 `pipeline_override` 用于：
1. 切换"是否启用流程"的 Flag 节点
2. 注入该流程入口节点所需参数（如难度 `expected`）

而**不要**用 Python orchestration 串联流程中的每个节点。完整流程示例：

```jsonc
// 选项定义
"开启3月成长试炼": {
    "type": "switch",
    "default_case": "No",
    "cases": [
        {
            "name": "Yes",
            "pipeline_override": {
                "Flag_GrowthTrialMode": { "enabled": true },
                "GrowthTrial_Difficulty_Select": { "expected": ["噩梦"] }
            }
        },
        {
            "name": "No",
            "pipeline_override": {
                "Flag_GrowthTrialMode": { "enabled": false }
            }
        }
    ]
}
```

```jsonc
// 入口节点（路由）
"GrowthTrial_Start": {
    "next": [
        "GrowthTrial_TeamReady",                  // 已在队伍配置页
        "[JumpBack]GrowthTrial_Difficulty_Select", // 在难度选择页
        "[JumpBack]GrowthTrial_Enter"             // 在大地图
    ]
}
```

战斗入口自动接力：

```jsonc
"GrowthTrial_EnterBattle": {
    "action": "Click",
    "next": [
        "GrowthTrial_FightStart",                   // 战斗开始
        "[JumpBack]GrowthTrial_TravelSelect_Boat",  // 弹出旅行框
        "[JumpBack]GrowthTrial_TravelSelect_Walk"   // fallback
    ]
}
```

---
