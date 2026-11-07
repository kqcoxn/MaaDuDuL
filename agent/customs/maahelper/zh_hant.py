"""国际服繁体中文（zh_hant）资源的识别文本适配。

国际服繁中客户端的界面文字与国服相比，除了简繁差异，还有不少用词不同（如「速战」→「扫荡」），
OCR 也常把繁体字识别成简体（如「活動视窗」）。本模块把国服的 expected 扩展为
「每个字简繁皆可 + 国际服用词」的正则，并保留原文，供两处使用：

- tools/gen_zh_hant.py：生成 resource/zh_hant/pipeline 覆盖层
- Tasker.run / RecoHelper.recognize：运行时覆盖的 expected（礼包名、商品名、角色名、「第N课」等）

只有加载了 zh_hant 覆盖层（存在 MARKER_NODE 节点）时才会转换，国服资源不受影响。
"""

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# 仅存在于 zh_hant 覆盖层的节点，用于判断当前是否加载了国际服繁中资源
MARKER_NODE = "国际服繁中_资源标识"

# 简体字 → 可接受的繁体写法，由 tools/gen_zh_hant.py --rebuild-chars 生成
CHARS: dict[str, str] = json.loads(Path(__file__).with_name("zh_hant_chars.json").read_text(encoding="utf-8"))

# 国服用词 → 国际服用词，均用简体书写，生成正则时再转为简繁皆可。
# 只收录在国际服画面上确认过的词；替换一次完成，替换后的文字不会再被其他词替换。
TERMS: dict[str, str] = {
    "活动弹窗": "活动视窗",
    "使徒": "使者",
    "冒险通行证": "等级通行证",
    "圣团": "教团",
    "点击屏幕继续": "轻触画面",
    "键领取": "全部领取",
    "键发送": "全部发送",
    "邮箱": "信箱",
    "日常商店": "每日商店",
    "确定": "确认",
    "屏幕": "萤幕",
    "设置": "设定",
    "速战": "扫荡",
    "最大": "MAX",
    # 国际服原文「確定要購買…嗎？」「去獲得勝利吧」比国服长，会被原有 roi 截断首尾
    "是否购买": "要购买",
    "获取途径": "获取方式",
    "获取详情": "获取资讯",
    "所持数量": "持有量",
    "巅峰对决": "胜者的暴打场",
    "请选择对手": "请选择对战对象",
    "去获胜": "获得胜利",
    "编辑卡组": "编制阵容",
    "卡组": "阵容",
    "入场": "进场",
    "克隆工厂": "复制人工厂",
    "神秘面包房": "秘密的面包店",
    # 副本标题「拿起你的蠟筆」在原有 roi 内只能识别到「拿起你的」
    "到手蜡": "拿起你的",
    "糖果自由": "棉花糖自由",
    "波次": "W[Aa][Vv][Ee]",
    "娃娃怪破坏者": "娃娃怪战队",
    # 冒险界面的主线入口
    "振兴之路": "进攻",
    "微微辣": "微辣",
    "课": "堂",
    "客人列表": "客人名单",
    "消化药": "消化剂",
    "派遣跑腿": "送去跑腿",
    # 跑腿结算弹窗右侧按钮「再送去一次」
    "重新派": "再送去",
    "布朗谢": "布兰切",
    "斯诺基": "斯诺奇",
    "没有可领取的邮件": "没有收到的信件",
    "圣团长的房间": "教主的房间",
    "初级棉花糖自选宝箱": "下等棉花糖选择箱",
    "中级棉花糖自选宝箱": "中等棉花糖选择箱",
    "圣团证书": "教团证明书",
    "锻造书": "装备晶石",
    # 红糖在国际服只叫「糖果」，限定整个名称，避免匹配到「龍族糖果」等商品
    "朱珠糖": "^糖果$",
    # 宴会选菜面板右下角的按钮
    "招待": "上菜",
    "篡夺与越轨之间": "篡夺与脱序之间",
}

_TERMS_RE = re.compile("|".join(sorted(map(re.escape, TERMS), key=len, reverse=True)))


def mixed_pattern(text: str) -> str:
    """把有繁体写法的字替换为 [简繁] 字符类，例如 活动视窗 → 活[动動][视視]窗。

    已含字符类的正则原样返回，避免破坏原有语法。
    """
    if "[" in text:
        return text
    return "".join(f"[{ch}{CHARS[ch]}]" if ch in CHARS else ch for ch in text)


def variants(text: str) -> list[str]:
    """返回 text 的简繁皆可写法，以及套用国际服用词后的写法（若有不同）。"""
    result = [mixed_pattern(text)]
    global_text = _TERMS_RE.sub(lambda m: TERMS[m.group(0)], text)
    if global_text != text:
        result.append(mixed_pattern(global_text))
    return result


def expand_expected(expected: Any, extra: Iterable[str] = (), keep: Iterable[str] = ()) -> Any:
    """在保留原文的前提下，为 expected 追加国际服可识别的写法。

    Args:
        expected: 原 expected，字符串或字符串列表。
        extra: 额外追加的文字（简体书写），同样会转换为简繁皆可。
        keep: 不追加繁体写法的原文。

    Returns:
        追加后的列表；没有可追加的写法时原样返回。
    """
    items: list[Any] = expected if isinstance(expected, list) else [expected]
    merged = list(items)
    keep = set(keep)
    for item in [*items, *extra]:
        if not isinstance(item, str) or item in keep:
            continue
        for v in variants(item):
            if v not in merged:
                merged.append(v)
    return merged if len(merged) > len(items) else expected


def localize_override(context: Any, pipeline_override: dict[str, Any]) -> dict[str, Any]:
    """加载了国际服繁中资源时，转换 pipeline_override 中所有 expected；否则原样返回。

    Args:
        context: MaaFramework 的 Context 对象。
        pipeline_override: 形如 {节点名: {字段: 值}} 的覆盖配置。

    Returns:
        转换后的新字典，或原字典。
    """
    if not pipeline_override or not _zh_hant_loaded(context):
        return pipeline_override
    return {name: _convert(node) for name, node in pipeline_override.items()}


def _convert(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: expand_expected(v) if k == "expected" else _convert(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert(v) for v in value]
    return value


def _zh_hant_loaded(context: Any) -> bool:
    try:
        return bool(context.tasker.resource.get_node_data(MARKER_NODE))
    except Exception:
        return False
