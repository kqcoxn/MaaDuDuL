"""生成国际服繁体中文（zh_hant）资源覆盖层。

扫描 resource/base/pipeline，把 OCR 节点的 expected 扩展为国际服可识别的写法
（转换规则见 agent/customs/maahelper/zh_hant.py），连同下方的节点级调整一起写入
resource/zh_hant/pipeline。该目录由本脚本整体生成，请勿手动修改；需要调整时改本脚本后重新生成：

    python tools/gen_zh_hant.py

国服 pipeline 更新后也需要重新生成。--rebuild-chars 会用 Windows 内置的简繁转换（LCMapStringEx）
重建简繁字表 agent/customs/maahelper/zh_hant_chars.json，仅可在 Windows 上执行。
"""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BASE_PIPELINE = ROOT / "resource" / "base" / "pipeline"
# 支持的语言覆盖层：locale → 生成到 resource/<locale>/pipeline，标识文件用 locale 命名
SUPPORTED_LOCALES = {"zh_hant": "国际服繁中"}
LOCALE = "zh_hant"


def out_pipeline(locale: str = LOCALE) -> Path:
    """返回某语言的覆盖层输出目录。"""
    return ROOT / "resource" / locale / "pipeline"


OUT_PIPELINE = out_pipeline()
ZH_HANT_MODULE = ROOT / "agent" / "customs" / "maahelper" / "zh_hant.py"
CHARS_FILE = ZH_HANT_MODULE.with_name("zh_hant_chars.json")

CN_PACKAGE = "com.bilibili.trickcalcn"
GLOBAL_PACKAGE = "com.bilibili.trickcal"

# 只加在特定节点上的额外识别文字（简体书写）
NODE_EXTRA: dict[str, list[str]] = {
    # 主界面的「使者」被角色遮挡，OCR 会拆成「使」「者」两段，改认同一区域的「編制陣容」
    "返回主界面_使徒": ["编制阵容"],
    "懒加载返回主界面_使徒": ["编制阵容"],
    "圣团巡礼_获取世界树": ["获得"],
    # 「冒險協會」被图标遮挡，OCR 只能识别到「險協」
    "圣团巡礼_进入冒险协会": ["险协"],
    # 教团外部顶端显示「Lv.4」，国服为「等级」
    "圣团巡礼_确保在外部": ["Lv\\.\\d"],
    # 冒险界面的入口直接写「PVP」，进入后是标题为「PVP」的大厅，「入場」按钮位置与国服相同
    "巅峰对决_进入巅峰对决": ["PVP"],
    "巅峰对决_确保进入巅峰对决": ["PVP"],
    # 扫荡结算的跳过按钮；不做成通用词，避免返回主界面时误点速成班的「SKIP」
    "速战_跳过动画": ["SKIP"],
    # 短期速成班次数用完时的提示「今天的課堂已全數完成」
    "速战_无法速战": ["课堂已全数完成"],
    # 国际服的跑腿结算是「先前跑腿結果」弹窗，原有点击位置 (646,620) 正好是「確認」按钮
    "农场视察_获取派遣奖励": ["先前跑腿结果"],
    # 装备材料「获取详情」关卡卡片上的按钮，国际服为「移動」
    "装备材料_识别前往": ["移动"],
    # 游戏改版后的资源下载弹窗，国际服标题为「檔案下載」（「開始下載」按钮在原有点击位置）
    "启动游戏_更新游戏": ["档案下载"],
    # 活动大厅的「像素异世界」开场提示，国际服字序相反：「異世界像素載入完成。」
    "每日活动作战_关闭梦境之地提示": ["异世界像素"],
    "每日活动作战2_关闭梦境之地提示": ["异世界像素"],
}

# 国际服的两字按钮字距较宽，OCR 会拆成单字（「購」「買」），限定了 roi 的节点改认第一个字
SPLIT_WORDS: dict[str, str] = {
    "购买": "购",
}

# 不追加繁体写法的节点：国际服画面上有同字但含义不同的文字，会误点
NODE_SKIP: set[str] = {
    # 国际服主界面「冒險」按钮上的气泡写着「立刻出發！」，会被当成更新完成按钮反复点进关卡列表
    "启动游戏_更新结束",
}

# 仅在特定节点不追加繁体写法的原文：国际服画面上常驻同名按钮，会被误点
NODE_KEEP_ORIGINAL: dict[str, set[str]] = {
    # 国际服活动大厅底部常驻「夢境之地」按钮（未开放时提示「還尚未開放的難度」），提示用「輕觸畫面」关闭即可
    "每日活动作战_关闭梦境之地提示": {"梦境之地"},
    "每日活动作战2_关闭梦境之地提示": {"梦境之地"},
}

# 直接覆盖的节点字段
NODE_FIELDS: dict[str, dict[str, Any]] = {
    # 参观结束后连续两次返回只间隔约 1 秒，第二次会在画面切换中失效，停留在「教主的房間」
    "圣团巡礼_额外从房间返回": {"post_delay": 2500},
    # 冒险界面刚打开时点击「PVP」会被转场吞掉，任务卡在冒险界面；成功时点击都在打开约 2 秒后
    "巅峰对决_进入冒险": {"post_delay": 2000},
    # 原流程点「开始下载」后只等「立刻出发」（最长 15 分钟）；国际服下载完直接进开场动画和开始界面，
    # 主界面气泡「立刻出發！」又在 NODE_SKIP 里，所以点完下载就回到启动流程继续识别
    "启动游戏_更新游戏": {"next": []},
}

# 国际服独有的画面，新增节点处理（expected 用简体书写）
EXTRA_NODES: dict[str, dict[str, Any]] = {
    # 跑腿结算弹窗（「先前跑腿結果」或「跑腿結果」）后仍能识别到首页图标，返回主界面会反复点击首页而卡住；
    # 两种弹窗的「確認」位置不同，同时识别到标题和按钮时点击按钮
    "返回主界面_跑腿结果": {
        "recognition": {
            "type": "And",
            "param": {
                "all_of": [
                    {"recognition": {"type": "OCR", "param": {"roi": [400, 0, 480, 120], "expected": ["跑腿结果"]}}},
                    {"recognition": {"type": "OCR", "param": {"roi": [400, 560, 480, 120], "expected": ["^确认$"]}}},
                ],
                "box_index": 1,
            },
        },
        "action": {"type": "Click"},
        "post_delay": 2000,
    },
    # 启动时伺服器较慢会长时间停在「正在載入伺服器設定」，超过 60 秒就会判定启动失败、接着跑下一个任务；
    # 画面还在载入时持续等待（每次约 4~5 秒，总上限约 10 分钟，避免伺服器维护时无限等待）
    "启动游戏_等待载入": {
        "recognition": {"type": "OCR", "param": {"expected": ["正在载入"]}},
        "post_delay": 3000,
        "max_hit": 120,
    },
    # 有时载入是真的卡死，重开游戏就好：连续约 3 分钟都在载入时关闭游戏再重新启动，最多重开 2 次
    "启动游戏_载入过久重启": {
        "recognition": {
            "type": "Custom",
            "param": {"custom_recognition": "stable_reco", "custom_recognition_param": "m=36&n=启动游戏_等待载入"},
        },
        "action": {"type": "StopApp", "param": {"package": GLOBAL_PACKAGE}},
        "post_delay": 3000,
        "max_hit": 2,
        "focus": {"Node.Recognition.Succeeded": "> 载入太久，重启游戏"},
        "next": ["启动游戏_启动游戏"],
    },
    # MuMu 国际版启动后可能弹出全屏广告，并且盖在游戏画面上方；「领取礼物」会认到广告上的「領取你的」
    # 而点开广告。认到右上角的「移除廣告」时点它右边的 ×（不点「移除廣告」本身，那是模拟器的付费页面）
    # 默认关闭，在「启动游戏」任务的「关闭模拟器广告」选项开启
    "启动游戏_关闭模拟器广告": {
        "enabled": False,
        "max_hit": 5,
        "recognition": {"type": "OCR", "param": {"roi": [640, 0, 640, 360], "expected": ["移除广告"]}},
        "action": {"type": "Click", "param": {"target": True, "target_offset": [95, 6, -63, -11]}},
        "post_delay": 2000,
        "focus": {"Node.Recognition.Succeeded": "> 关闭模拟器广告"},
        "next": ["启动游戏_启动游戏"],
    },
    # 广告被点开后会进入 Google Play 的游戏页面，认到商店页面时重新启动游戏
    # （「愿」与「願」不在逐字对照表里，直接写字符类）
    "启动游戏_回到游戏": {
        "max_hit": 3,
        "recognition": {"type": "OCR", "param": {"expected": ["加入[愿願]望清[单單]", "超过\\d+万次"]}},
        "focus": {"Node.Recognition.Succeeded": "> 画面跳到了应用商店，重新回到游戏"},
        "next": ["启动游戏_启动游戏"],
    },
    # 游戏改版后的资源下载画面，底部显示「…(15.7%) 6.7MB/42.5MB 5.5MB/s」；下载量大时会超过 60 秒，持续等待
    "启动游戏_等待下载": {
        "recognition": {"type": "OCR", "param": {"roi": [200, 660, 880, 60], "expected": ["MB/s"]}},
        "post_delay": 3000,
        "max_hit": 200,
        "focus": {"Node.Recognition.Succeeded": "> 正在下载游戏资源"},
    },
    # 登录后的「艾利亞斯邊疆之界／新的事件座標出現了。」卡片动画会一直播放，要点一下才会关闭；
    # 点卡片下方的文字（实测点在画面其他位置也能关闭，不会触发底下的按钮）。
    # 卡片下方隐约可见主界面，排在「连续识别主界面」之前，避免卡片还在时就判定进入主界面
    "启动游戏_关闭事件座标": {
        "recognition": {"type": "OCR", "param": {"roi": [300, 560, 680, 80], "expected": ["新的事件座标出现"]}},
        "action": {"type": "Click"},
        "post_delay": 2000,
        "max_hit": 5,
        "focus": {"Node.Recognition.Succeeded": "> 关闭事件座标提示"},
    },
}

# 把新增节点插入已有节点的 next：{节点: [(插在哪一项之后（None 为最前面）, 新增的 next 项)]}
NEXT_INSERT: dict[str, list[tuple[str | None, str]]] = {
    "返回主界面_开始": [("返回主界面_检测主界面", "[JumpBack]返回主界面_跑腿结果")],
    # 广告和商店页面要排在「领取礼物」之前，同一张截图会先认到它们
    "启动游戏_启动游戏": [
        (None, "[JumpBack]启动游戏_关闭事件座标"),
        ("启动游戏_连续识别开始界面", "启动游戏_载入过久重启"),
        ("启动游戏_载入过久重启", "[JumpBack]启动游戏_等待载入"),
        ("[JumpBack]启动游戏_等待载入", "[JumpBack]启动游戏_等待下载"),
        ("[JumpBack]启动游戏_等待下载", "启动游戏_回到游戏"),
        ("启动游戏_回到游戏", "启动游戏_关闭模拟器广告"),
    ],
    "启动游戏_捏脸启动": [
        (None, "[JumpBack]启动游戏_关闭事件座标"),
        ("启动游戏_连续识别主界面", "启动游戏_载入过久重启"),
        ("启动游戏_载入过久重启", "[JumpBack]启动游戏_等待载入"),
        ("[JumpBack]启动游戏_等待载入", "启动游戏_回到游戏"),
        ("启动游戏_回到游戏", "启动游戏_关闭模拟器广告"),
    ],
}

# Windows 内置的简繁转换只做逐字转换，一对多的字会原样保留，重建字表时补上其他写法
AMBIGUOUS: dict[str, str] = {
    "面": "麵", "后": "後", "余": "餘", "游": "遊", "喂": "餵",
    "干": "乾幹", "里": "裡裏", "制": "製", "台": "臺", "只": "隻",
    "发": "發髮", "复": "復複", "系": "係", "历": "歷曆", "准": "準",
    "钟": "鐘鍾", "冲": "衝沖", "卷": "捲", "签": "簽籤", "表": "錶",
    "征": "徵", "松": "鬆", "范": "範", "并": "並併", "汇": "匯彙", "仆": "僕",
    "尽": "盡儘", "蜡": "蠟", "占": "佔", "托": "託", "布": "佈",
    "周": "週", "斗": "鬥", "秘": "祕", "御": "禦",
}  # fmt: skip


def load_zh_hant() -> Any:
    """直接按文件加载转换模块，避免导入 agent.customs 时注册全部 custom。"""
    spec = importlib.util.spec_from_file_location("zh_hant", ZH_HANT_MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rebuild_chars() -> None:
    """用 Windows 的 LCMapStringEx 为 GB2312 全部汉字生成简繁字表。"""
    import ctypes
    from ctypes import wintypes

    lcmap = ctypes.windll.kernel32.LCMapStringEx
    lcmap.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPCWSTR, ctypes.c_int,
        wintypes.LPWSTR, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, wintypes.LPARAM,
    ]  # fmt: skip
    lcmap.restype = ctypes.c_int
    traditional_flag = 0x04000000

    def to_traditional(ch: str) -> str:
        buf = ctypes.create_unicode_buffer(4)
        size = lcmap("zh-CN", traditional_flag, ch, 1, buf, 4, None, None, 0)
        return buf[:size]

    chars: dict[str, str] = {}
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                ch = bytes([hi, lo]).decode("gb2312")
            except UnicodeDecodeError:
                continue
            alts = "".join(dict.fromkeys(c for c in to_traditional(ch) + AMBIGUOUS.get(ch, "") if c != ch))
            if alts:
                chars[ch] = alts
    CHARS_FILE.write_text(json.dumps(chars, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
    print(f"已生成 {len(chars)} 个字到 {CHARS_FILE.relative_to(ROOT)}")


def ocr_override(zh_hant: Any, name: str, node: dict[str, Any]) -> dict[str, Any] | None:
    rec = node.get("recognition")
    if name in NODE_SKIP or not isinstance(rec, dict) or rec.get("type") != "OCR":
        return None
    param: dict[str, Any] = rec.get("param", {})
    expected = param.get("expected")
    if expected is None:
        return None
    items = expected if isinstance(expected, list) else [expected]
    extra = list(NODE_EXTRA.get(name, []))
    if param.get("roi"):
        extra += [SPLIT_WORDS[e] for e in items if e in SPLIT_WORDS]
    merged = zh_hant.expand_expected(expected, extra, NODE_KEEP_ORIGINAL.get(name, ()))
    if merged is expected:
        return None
    return {"recognition": {"param": {"expected": merged}}}


def package_override(node: dict[str, Any]) -> dict[str, Any] | None:
    action = node.get("action")
    if not isinstance(action, dict) or action.get("param", {}).get("package") != CN_PACKAGE:
        return None
    return {"action": {"param": {"package": GLOBAL_PACKAGE}}}


def localize_patterns(zh_hant: Any, value: Any) -> Any:
    """把新增节点中所有 expected 转换为简繁皆可的写法。"""
    if isinstance(value, dict):
        return {
            k: [zh_hant.mixed_pattern(e) for e in v] if k == "expected" else localize_patterns(zh_hant, v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [localize_patterns(zh_hant, v) for v in value]
    return value


def build_overrides(zh_hant: Any, data: dict[str, Any]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for name, node in data.items():
        if not isinstance(node, dict):
            continue
        override: dict[str, Any] = {}
        for part in (ocr_override(zh_hant, name, node), package_override(node), NODE_FIELDS.get(name)):
            if part:
                override.update(part)
        if name in NEXT_INSERT:
            next_list = list(node.get("next", []))
            for after, item in NEXT_INSERT[name]:
                next_list.insert(0 if after is None else next_list.index(after) + 1, item)
                extra_name = item.removeprefix("[JumpBack]")
                overrides[extra_name] = localize_patterns(zh_hant, EXTRA_NODES[extra_name])
            override["next"] = next_list
        if override:
            overrides[name] = override
    return overrides


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    global LOCALE, OUT_PIPELINE

    if "--locale" in sys.argv:
        LOCALE = sys.argv[sys.argv.index("--locale") + 1]
        if LOCALE not in SUPPORTED_LOCALES:
            print(f"暂不支持的语言：{LOCALE}（可用：{', '.join(SUPPORTED_LOCALES)}）")
            return 1
        OUT_PIPELINE = out_pipeline(LOCALE)

    if "--rebuild-chars" in sys.argv:
        rebuild_chars()

    zh_hant = load_zh_hant()
    if OUT_PIPELINE.exists():
        shutil.rmtree(OUT_PIPELINE)

    node_count = 0
    for src in sorted(BASE_PIPELINE.rglob("*.json")):
        overrides = build_overrides(zh_hant, json.loads(src.read_text(encoding="utf-8")))
        if overrides:
            write_json(OUT_PIPELINE / src.relative_to(BASE_PIPELINE), overrides)
            node_count += len(overrides)

    marker = {zh_hant.MARKER_NODE: {"recognition": {"type": "DirectHit"}, "action": {"type": "DoNothing"}}}
    write_json(OUT_PIPELINE / f"{SUPPORTED_LOCALES[LOCALE]}.json", marker)
    print(f"已生成 {node_count} 个节点覆盖到 {OUT_PIPELINE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
