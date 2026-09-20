# 坐标卫生（点击目标怎么来）

点击位置应当**由识别结果推导**，不是写死的常数。硬编码坐标在作者的模拟器上能跑，换一台设备就会因为分辨率、缩放、DPI、状态栏高度、安全区裁剪或 UI 版本变化而偏移到别的控件上，而且失败时不会报错——它只是点错地方。

MaaFramework 的默认行为已经做对了：`target` 默认是 `true`，即**点击本节点识别框的中心**。写死 `target` 通常是在覆盖一个本来正确的默认值。

## `target` 的取值语义

| 取值 | 含义 | 建议 |
|---|---|---|
| `true`（默认） | 点击本节点识别结果的框中心 | ✅ 首选 |
| `"NodeName"` | 点击另一个节点识别结果的框中心 | ✅ 目标本身不可识别时用它锚定 |
| `[x, y, w, h]` | 点击写死的区域中心 | ⚠️ 仅限例外，且必须写明理由 |
| `[x, y]` | 点击写死的点 | ⚠️ 同上 |

`target_offset` 是在 `target` 解析出来的框上再做偏移，本身不违规；违规的是**用它把点击从识别到的元素挪到一个从未被识别过的元素上**。

## 坏味 A：DirectHit + 硬编码 target

```jsonc
// ❌ 完全跳过识别：没有 OCR，没有 TemplateMatch，只有一对坐标
"Event_PirateRaid_ClickBanner": {
    "recognition": "DirectHit",
    "action": "Click",
    "target": [360, 900, 200, 80]
}
```

问题不只是坐标会偏。`DirectHit` 永远命中，所以这个节点**在任何画面上都会点下去**：横幅还没出现、还在加载、已经弹了别的窗口，它照点不误，`next` 拿到的状态也就无从判断。这类节点等于把「识别 → 操作 → 识别」循环中的识别环节整个删掉。

## 坏味 B：识别命中了，却把点击偏到别处

```jsonc
// ❌ OCR 找到了难度文字，然后用写死的偏移点右边的"确定"
"Activity_SelectDifficulty": {
    "recognition": "OCR",
    "expected": ["困难"],
    "action": "Click",
    "target_offset": [270, 0, 0, 0]
}
```

`270` 是在某一台设备的某一版 UI 上量出来的。按钮换位置、文案变长、分辨率变化，点击就落空，而识别仍然报成功——排查时最难查的一类问题。

## 推荐 1：OCR-based click（文字元素）

```jsonc
// ✅ 不写 target，MaaFramework 直接点识别到的文字中心
"Activity_EnterBattle": {
    "recognition": "OCR",
    "expected": ["进入战斗"],
    "roi": [0, 900, 720, 380],
    "action": "Click",
    "next": ["Activity_BattleStarted"]
}
```

- `expected` 写目标资源上实际显示的完整文案。
- `roi` 用来把识别范围限定到该文字所在区域，排除同名文字；它是**识别范围**，不是点击坐标。
- 同屏出现多个同名按钮时，用互不重叠的窄 ROI 区分，而不是用偏移去够。

## 推荐 2：TemplateMatch-based click（非文字元素）

按钮、图标、没有文字的横幅用模板匹配：

```jsonc
// ✅ 截图裁剪存入资源 image 目录，用模板定位后点击命中框中心
"Event_PirateRaid_ClickBanner": {
    "recognition": {
        "type": "TemplateMatch",
        "param": {
            "template": "Event/PirateRaid/banner.png",
            "roi": [0, 700, 720, 400],
            "threshold": 0.7
        }
    },
    "action": {"type": "Click"},
    "next": ["Event_PirateRaid_PreparePage"]
}
```

- 用 `screencap` 取无损原图，裁剪出稳定的图标区域，缩放到 720×1280 基准后存入该资源根声明的 image 目录。
- 只裁**不会变的部分**：避开数字、倒计时、进度条、红点；必要时用 `green_mask` 遮蔽。
- 阈值先用默认 `0.7`，命中不稳时看截图再调，不要直接退回硬编码坐标。

## 例外：确实需要相对偏移时

目标控件本身既没有稳定文字也没有稳定图案（例如一行里第 N 个空白槽位），此时允许锚定偏移，但必须同时满足：

1. 锚点是**识别结果**——`target: true` 或 `target: "已识别的节点名"`，不是全屏绝对坐标；
2. 偏移量从实测截图量出来，并在提交说明或测试记录里写明来源；
3. 点击后有下一屏识别验证，不假设点中了；
4. 一旦该控件可以用 OCR 或 TemplateMatch 直接识别，就换掉偏移写法。

## 决策顺序

```
要点击一个元素
│
├─ 有稳定可见文字？        → OCR + expected，不写 target
├─ 有稳定图案/图标？       → TemplateMatch + template，不写 target
├─ 有稳定颜色状态？        → ColorMatch，必要时配合 And 组合
├─ 只有相对位置关系？      → 识别锚点元素，再 target/target_offset 偏移，并记录理由
└─ 以上都没有？            → 先回去探明 UI，不要用 DirectHit + 坐标凑
```

## 自查清单

- [ ] 节点有真实识别算法，`DirectHit` 只用于无需识别的纯动作或流程节点
- [ ] 没有为了「点某个东西」而写死 `target` 的坐标数组
- [ ] `target_offset` 锚定在识别结果上，且偏移量有实测来源
- [ ] `roi` 只用于限定识别范围，没有被当作点击坐标使用
- [ ] 模板图来自无损原图裁剪并缩放到 720×1280
- [ ] 点击后有下一屏识别验证
