# Maa Pipeline Option Anti-patterns

## Contents

1. 不要只通过 pipeline_override 定义节点
2. 不要忘记 task option 注册
3. 不要把判断塞进 dispatch
4. 不要混淆字段路径
5. switch case 使用 Yes/No
6. input 注入与读取路径必须一致
7. Pipeline 节点名使用 ASCII
8. 不要跨文件重复定义节点
9. 不要强行增加 Flag 节点
10. 不要用 Python orchestration 替代状态机
11. UI override 与 Python 读取必须一致

## ❌ 不要做

### 1. 不要只通过 pipeline_override 定义节点

```jsonc
// ❌ 错：节点没在 pipeline JSON 中预定义 → 不会被加载 → get_node_data() 返回 None

// ✅ 对：在 pipeline JSON 里预定义
"Flag_EnableSailingFestivalPurchase": { "enabled": true }
```

**验证方法**：加完后跑 `python tools/ci/check_resource.py assets/resource/base`（或目标项目真实资源检查命令），并在 Python 里加个 `None` 兜底日志。

### 2. 不要忘了注册到 task 的 option 数组

```jsonc
// ❌ 错：option 定义了但 task 不引用 → UI 上看不到
"option": []

// ✅ 对：同步注册
"option": ["开启3月启航节购买"]
```

### 3. 不要把判断塞到 dispatch 函数

```python
# ❌ 错：dispatch 越来越臃肿
def handle_festival_by_month(month):
    if month == 3 and not context.get_node_data("Flag_X").get("enabled"):
        return True
    if month == 3:
        return handle_sailing_festival(context)
    # ... 每加一个开关都得多一个 if

# ✅ 对：业务函数自治
def handle_sailing_festival(context):
    if not context.get_node_data("Flag_X").get("enabled"):
        return True
    # ... 正常逻辑
```

### 4. 不要混淆字段路径

| 用途 | 字段路径 | 备注 |
|------|---------|------|
| `select` | `data["recognition"]["param"]["expected"][0]` | 节点必须 `recognition: "OCR"` |
| `input` 注入 CustomAction | `data["action"]["param"]["custom_action_param"][key]` 或执行时的 `argv.custom_action_param` | 取决于参数消费位置 |
| `input` 注入普通节点字段 | 读取被占位符覆盖的真实路径，如 `recognition.param.expected` | input 不限定注入目标 |
| `switch` / `checkbox` | `data["enabled"]` | 最简单 |
| 历史 `enable` 开关 | `data.get("enable", data.get("enabled", default))` | 仅在项目已有该字段时使用 |
| 模式 E 不读 | （不读，直接看 override 后节点的运行时行为） | pure override 模式，Python 拿不到也不需要 flag |

### 5. 不要用非 `Yes`/`No` 的 switch case 名

```jsonc
// ❌ 错：Client 解析可能不一致
{ "name": "true" } / { "name": "是" } / { "name": "ON" }

// ✅ 对：跨 Client 一致
{ "name": "Yes" } / { "name": "No" }
```

### 6. 不要让 input 注入路径和读取路径错位

`input` 的 `{name}` 占位符既可以注入 OCR `expected`，也可以注入 `action.param.custom_action_param`。选择哪条路径取决于最终消费方：普通 OCR/配置读取用实际节点字段，CustomAction 执行参数用 `argv.custom_action_param`。不要写入一条路径却从另一条路径读取。

### 7. 不要用中文做 pipeline 节点名

```jsonc
// ❌ 错：中文节点名 + 英文字段访问
"开启5月": { "enabled": true }

// ✅ 对：英文 Flag_ 命名
"Flag_EnableMarryTask": { "enabled": true }
```

中文做 option 名（用户可见），英文做 pipeline 节点名（代码访问）。混了会让代码和配置都对不上。

### 8. 不要在多文件 pipeline 里重复定义同名节点

`parse_and_override_once` 合并所有 pipeline JSON 时**严格拒绝**重复顶层 key。检查方法：

```bash
grep -rn "^\s*\"YourNodeName\":" assets/resource/base/pipeline/
```

两个文件都定义同一个顶层节点会直接让整个 `check_resource.py` 失败，且 Python `json.load()` 检测不出来（Python 会静默覆盖），必须用 C++ 解析器或 C++ 模拟检测。

### 9. 不要为了"配置统一"硬塞 Flag 节点

```jsonc
// ❌ 错：行为切换只动 pipeline 字段，但你硬加了 Flag 节点 + Python 分支
"Flag_AcceptMercenary": { "enabled": true },   // ← 不必要
def handle_mercenary_join(context):
    if not context.get_node_data("Flag_AcceptMercenary").get("enabled"):
        return True
    context.run_task("Event_MercenaryJoin")      # 实际行为由 Event_MercenaryJoin.next 决定

// ✅ 对：直接 override `next`，零 Python 改动
"开启自动接受佣兵": {
    "type": "switch",
    "pipeline_override": {
        "Event_MercenaryJoin": { "next": ["Event_MercenaryJoinConfirm"] }
    }
}
```

**判断口诀**：如果你的 Python 分支里**只做了一件事**（调用 `run_task` 让 pipeline 接手），那这个分支完全可以由 `pipeline_override` 替代。Flag 节点 + Python 分支只在你需要在 Python 侧做**真正的条件逻辑**（不只是转发）时才必要。

### 10. 不要用 Python orchestration 替代状态机

如果一个跨页面流程可以**列举**为有限个页面状态（A → B → C → D），优先用 MaaFramework 的 `next` + `[JumpBack]` 串起来。**不要**写 Python `for` 循环 + `context.run_task()` 调度。

```jsonc
// ✅ 对：纯 JSON 状态机（推荐）
"GrowthTrial_Start": {
    "next": [
        "GrowthTrial_TeamReady",                  // 已在队伍配置页
        "[JumpBack]GrowthTrial_Difficulty_Select", // 在难度选择页
        "[JumpBack]GrowthTrial_Enter"             // 在大地图
    ]
}

"GrowthTrial_Enter": {
    "next": [
        "GrowthTrial_Enter_Click",                  // 找到图标
        "[JumpBack]BigMap_Activity_Resident",       // 切"常驻"tab
        "[JumpBack]BigMap_Activity"                 // 打开活动页
    ]
}

"GrowthTrial_EnterBattle": {
    "action": "Click",
    "next": [
        "GrowthTrial_FightStart",                    // 战斗开始
        "[JumpBack]GrowthTrial_TravelSelect_Boat",   // 弹出旅行框
        "[JumpBack]GrowthTrial_TravelSelect_Walk"    // fallback
    ]
}
```

```python
# ❌ 错：自己重新发明状态机
def enter_growth_trial(context):
    found = False
    for attempt in range(5):
        if context.run_recognition("BigMap_GrowthTrial_OCR", ...).hit:
            found = True
            break
        context.run_task("Map_SwipeUp_OnBigMap")
    if not found:
        return False
    context.run_task("GrowthTrial_Enter")
    # ... 又是 for/if 链
    return True
```

**自检问题**：
- 我的 Python 代码里是否在**调 `run_task` 把控制权交给 pipeline**？是 → 考虑改用 `next` 链
- 我的"流程推进"是否依赖**显式的状态变量**（如 `found`）？是 → 改用 `[JumpBack]` 让框架自动回退
- 我的"流程"是否**可以画成状态机图**？是 → 用 JSON `next` 链

**注意**：MaaFramework 全局加载时跨文件节点引用会解析（`main_ui.json` 里的 `BigMap_Activity*` 能在 `growth_trial.json` 引用），但**`run_pipeline` 测试工具只加载单文件**——集成测试必须用 MaaFramework GUI/CLI 触发。

### 11. 不要让 UI override 字段和 Python 读取字段不一致

```jsonc
// ❌ 错：UI 写 enable
"开启克隆体": {
    "type": "switch",
    "cases": [
        { "name": "Yes", "pipeline_override": { "AutoSky_CloneConfig": { "enable": true } } }
    ]
}
```

```python
# ❌ 错：代码却读 expected，永远读不到用户开关
self._clone_enabled = _read_expected_value(context, "AutoSky_CloneConfig")
```

```python
# ✅ 对：读同一个字段，或提供 enable/enabled 兼容
self._clone_enabled = _node_enabled(context, "AutoSky_CloneConfig")
```

自检口诀：**UI 写哪条路径，Python 就读哪条路径；pure override 则 Python 不读。**

---

