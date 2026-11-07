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
OUT_PIPELINE = ROOT / "resource" / "zh_hant" / "pipeline"
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
}

# 把新增节点插入已有节点的 next：{节点: [(插在哪一项之后, 新增的 next 项)]}
NEXT_INSERT: dict[str, list[tuple[str, str]]] = {
    "返回主界面_开始": [("返回主界面_检测主界面", "[JumpBack]返回主界面_跑腿结果")],
}

# Windows 内置的简繁转换只做逐字转换，一对多的字会原样保留，重建字表时补上其他写法
AMBIGUOUS: dict[str, str] = {
    "面": "麵", "后": "後", "余": "餘", "游": "遊", "喂": "餵",
    "干": "乾幹", "里": "裡裏", "制": "製", "台": "臺", "只": "隻",
    "发": "發髮", "复": "復複", "系": "係", "历": "歷曆", "准": "準",
    "钟": "鐘鍾", "冲": "衝沖", "卷": "捲", "签": "簽籤", "表": "錶",
    "征": "徵", "松": "鬆", "范": "範", "并": "並併", "汇": "匯彙",
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
                next_list.insert(next_list.index(after) + 1, item)
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
    write_json(OUT_PIPELINE / "国际服繁中.json", marker)
    print(f"已生成 {node_count} 个节点覆盖到 {OUT_PIPELINE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
