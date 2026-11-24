"""多语言资源适配的分发层。

MaaFramework 的 ProjectInterface 会把当前选择的资源信息注入 Agent 进程：

- `PI_RESOURCE`：JSON，含 `name`（如 `cn` / `en` / `zh_hant`）与 `path`（如 `["./resource/base", "./resource/zh_hant"]`）
- `PI_CLIENT_LANGUAGE`：界面语言（与游戏客户端语言无关，仅作兜底参考）

据此可以**直接得知**当前加载的是哪套资源，不需要靠探测节点是否存在来猜测——
后者在国服上会持续产生 `MaaResourceGetNodeData failed` 报错。

另外会在任务开始时用 adb 看一眼设备上装的是哪个客户端：如果与所选资源不一致，
**只提示并中止**（运行时不改 pipeline，避免热切换带来的不确定行为）。

新增语言只需：
1. 在 `LOCALE_HANDLERS` 里登记一个处理器（负责把 pipeline 覆盖里的 expected 扩展成该语言可接受的写法）；
2. 在 `interface.json` 的 `resource` 里加一份 `./resource/<locale>` 资源；
3. 让对应的生成器（如 `tools/gen_zh_hant.py --locale <locale>`）产出覆盖层。
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

from agent.customs.utils import Prompter

# 基础资源对应简中；其余名字按覆盖层目录名命名（与 interface.json 的 resource.name 一致）
BASE_LOCALE = "cn"
ENV_RESOURCE = "PI_RESOURCE"

# 语言标识的兜底探测：某些前端可能不注入 PI_RESOURCE，此时退回「覆盖层标识节点」判断
FALLBACK_MARKERS: dict[str, str] = {"zh_hant": "国际服繁中_资源标识"}
_MARKER_TTL = 30.0
_marker_cache: dict[str, tuple[float, bool]] = {}


class LocaleHandler(Protocol):
    """语言处理器接口：把 pipeline 覆盖里的 expected 扩展为该语言的写法。"""

    def expand_override(self, pipeline_override: dict[str, Any]) -> dict[str, Any]:
        """返回扩展后的 pipeline 覆盖字典。"""
        ...


LOCALE_HANDLERS: dict[str, LocaleHandler] = {}

# 语言标识 → 给用户看的文案
LOCALE_LABELS: dict[str, str] = {
    "cn": "国服 / 简中",
    "zh_hant": "国际服 / 繁中",
    "en": "国际服 / 英文",
}

# 客户端包名 → 语言（国际服还要再看设备语言）
PACKAGE_SERVERS: dict[str, str | None] = {
    "com.bilibili.trickcalcn": "cn",
    "com.bilibili.trickcal": None,
}
# 主界面语言探测节点（resource/base/pipeline/其他/本地化探测.json）
SCREEN_PROBE_NODE = "本地化_语言探测"
# 主界面关键词：简中 / 繁中各取一组，用于区分国际服的繁中与英文
TRAD_KEYWORDS = ("活動", "活動視窗", "活動弹窗", "使者", "編輯", "编制阵容", "教團", "劇場", "通行證", "陣容")
SIMP_KEYWORDS = ("使徒", "活动弹窗", "编辑卡组", "圣团", "剧院")
# 英文界面实测文本（国际服英文客户端主界面）：Apostles=使徒、Events=活动弹窗、Trickcal Pass=冒险通行证
EN_KEYWORDS = ("Apostles", "Events", "Friends", "Quests", "Adventure", "Line-up", "Theater", "Recruit", "Premium", "Store")

# 资源标识 → 该资源对应的客户端包名，用于和设备实际安装的客户端对比
LOCALE_PACKAGES: dict[str, str] = {
    "cn": "com.bilibili.trickcalcn",
    "zh_hant": "com.bilibili.trickcal",
    "en": "com.bilibili.trickcal",
}

_announced = False
_mismatch_logged = False
_ambiguous_noted = False


def register_handler(locale: str, handler: LocaleHandler) -> None:
    """登记某语言的处理器。"""
    LOCALE_HANDLERS[locale] = handler


def _from_resource_env() -> str:
    """从 PI_RESOURCE 解析当前资源对应的语言标识，解析不出来返回空串。"""
    raw = os.environ.get(ENV_RESOURCE, "").strip()
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except Exception:
        return ""
    paths = data.get("path") or []
    if isinstance(paths, str):
        paths = [paths]
    # 覆盖层目录名最可靠：./resource/base + ./resource/zh_hant → zh_hant
    for path in paths:
        name = os.path.basename(str(path).replace("\\", "/").rstrip("/"))
        if name and name != "base":
            return name
    name = str(data.get("name") or "").strip()
    return name or BASE_LOCALE


def _marker_present(context: Any, locale: str) -> bool:
    """兜底探测：该语言的覆盖层标识节点是否存在（带有效期缓存）。"""
    marker = FALLBACK_MARKERS.get(locale)
    if not marker or context is None:
        return False
    now = time.monotonic()
    cached = _marker_cache.get(locale)
    if cached and now - cached[0] <= _MARKER_TTL:
        return cached[1]
    try:
        present = context.tasker.resource.get_node_data(marker) is not None
    except Exception:
        present = False
    _marker_cache[locale] = (now, present)
    return present


def current_locale(context: Any = None) -> str:
    """返回当前**所选资源**对应的语言标识；无法判断时按基础资源（简中）处理。

    Args:
        context: MaaFramework 的 Context 对象，仅兜底探测时使用。

    Returns:
        str: 语言标识，如 `cn` / `zh_hant`。
    """
    locale = _from_resource_env()
    if not locale:
        for candidate in LOCALE_HANDLERS:
            if _marker_present(context, candidate):
                locale = candidate
                break
    locale = locale or BASE_LOCALE
    announce(locale)
    return locale


def announce(locale: str | None = None) -> str:
    """把当前区服输出成一条中文文案（每个进程只输出一次）。

    Args:
        locale: 语言标识；为空时按所选资源判定。

    Returns:
        str: 实际输出的文案（便于测试断言）。
    """
    global _announced
    locale = locale or _from_resource_env() or BASE_LOCALE
    label = LOCALE_LABELS.get(locale, f"未知资源（{locale}）")
    text = f"当前区服：{label}"
    if not _announced:
        _announced = True
        try:
            Prompter.log(text)
        except Exception:
            pass
    return text


# ====================  设备侧核对（只提示，不热切换）  ====================


def _mfaa_device() -> tuple[str, str] | None:
    """从 MFAAvalonia 的实例配置里取 (adb 路径, 设备序列号)。"""
    candidates = [
        Path.cwd() / "config" / "instances",
        Path.cwd().parent / "MFAAvalonia" / "config" / "instances",
    ]
    for directory in candidates:
        if not directory.is_dir():
            continue
        for file in sorted(directory.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            device = data.get("AdbDevice") or {}
            adb = str(device.get("AdbPath") or "").strip()
            serial = str(device.get("AdbSerial") or "").strip()
            if adb and serial:
                return adb, serial
    return None


def _adb_shell(adb: str, serial: str, command: str) -> str:
    """执行一次 adb shell，失败返回空串。"""
    try:
        done = subprocess.run(
            [adb, "-s", serial, "shell", command],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return (done.stdout or "").strip()
    except Exception:
        return ""


def _server_of_package(package: str) -> str:
    """把包名翻译成「区服」：国服返回 cn，国际服返回 intl（具体语言要看画面）。"""
    if package == "com.bilibili.trickcalcn":
        return "cn"
    return "intl"


def detect_from_device() -> str:
    """判断设备上实际的客户端区服；判不出来返回空串。

    同一台设备可能同时装了国服与国际服，所以：
    装了多个版本时看**当前前台/正在运行**的那个；看不出运行状态则放弃判断，交给资源。
    """
    device = _mfaa_device()
    if not device:
        return ""
    adb, serial = device
    listing = _adb_shell(adb, serial, "pm list packages")
    if not listing:
        return ""
    # pm list packages 每行形如 package:com.bilibili.trickcalcn，必须精确比较
    # （com.bilibili.trickcal 是 com.bilibili.trickcalcn 的前缀，用 in 会误判成两个版本都在）
    packages = {
        line.strip()[len("package:"):].strip()
        for line in listing.splitlines()
        if line.strip().startswith("package:")
    }
    installed = [name for name in PACKAGE_SERVERS if name in packages]
    if not installed:
        return ""
    if len(installed) > 1:
        focus = _adb_shell(adb, serial, "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
        running = [name for name in installed if f"{name}/" in focus]
        if len(running) != 1:
            global _ambiguous_noted
            if not _ambiguous_noted:
                _ambiguous_noted = True
                Prompter.log(
                    "设备上同时装了国服与国际服客户端，且当前没有可判定的运行中客户端，"
                    "已跳过区服核对，按所选资源继续"
                )
            return ""
        return _server_of_package(running[0])
    return _server_of_package(installed[0])


def detect_from_screen(context: Any) -> str:
    """用主界面 OCR 判断当前客户端是简中还是繁中；判断不出来返回空串。

    国际服只有一个包名（com.bilibili.trickcal），繁中/英文无法从系统层面区分，
    所以这里用主界面上的固定文案再确认一次。

    Args:
        context: MaaFramework 的 Context 对象。

    Returns:
        str: `cn` / `zh_hant` / 空串。
    """
    try:
        from .tasker import Tasker

        image = Tasker(context).screenshot()
        if image is None:
            return ""
        detail = context.run_recognition(SCREEN_PROBE_NODE, image)
    except Exception:
        return ""
    if detail is None:
        return ""
    texts: list[str] = []
    for result in getattr(detail, "all_results", None) or []:
        text = getattr(result, "text", "") or ""
        if text:
            texts.append(text)
    joined = " ".join(texts)
    if not joined:
        return ""
    traditional = sum(1 for keyword in TRAD_KEYWORDS if keyword in joined)
    simplified = sum(1 for keyword in SIMP_KEYWORDS if keyword in joined)
    english = sum(1 for keyword in EN_KEYWORDS if keyword in joined)
    best = max(traditional, simplified, english)
    if best == 0:
        return ""
    if english == best:
        return "en"
    if traditional == best:
        return "zh_hant"
    return "cn"


def verify(context: Any = None) -> bool:
    """任务开始时核对「所选资源」与「设备实际客户端」是否一致。

    不一致时提示并停止任务链（队列随之退出），不做任何运行时热切换。

    Args:
        context: MaaFramework 的 Context 对象，用于兜底探测当前资源。

    Returns:
        bool: 始终返回 True；不一致时内部已停止任务链。
    """
    global _mismatch_logged
    selected = current_locale(context)
    detected = detect_from_device()
    if not detected:
        return True
    if detected == "intl":
        # 国际服：包名只能确定“国际服”，具体语言再看主界面文案
        screen = detect_from_screen(context)
        if screen:
            detected = screen
        elif selected != "cn":
            # 画面暂时判不出来，但资源也不是国服，先放行
            return True
    if detected == selected:
        return True

    detected_label = LOCALE_LABELS.get(detected, "国际服 / 未能确定语言" if detected == "intl" else detected)
    selected_label = LOCALE_LABELS.get(selected, selected)
    if not _mismatch_logged:
        _mismatch_logged = True
        Prompter.log(
            f"设备上的客户端是「{detected_label}」，而当前资源是「{selected_label}」；"
            f"已停止任务队列，请在 MFAA 的「资源」里切换到「{detected_label}」后重新开始"
        )
    # 停止任务链：让 Maa 的任务进入「已放弃」状态，MFAA 才会中止后续任务（队列整体退出）。
    # 注意这里返回 True：若返回 False，MFAA 只会把本条任务记为「失败」并继续下一条。
    try:
        from .tasker import Tasker

        Tasker(context).stop(wait=False)
    except Exception as e:
        Prompter.error("停止任务队列", e)
    return True


def localize_override(context: Any, pipeline_override: dict[str, Any]) -> dict[str, Any]:
    """按当前资源对应的语言扩展 pipeline 覆盖里的识别文本。

    Args:
        context: MaaFramework 的 Context 对象。
        pipeline_override: 形如 {节点名: {字段: 值}} 的覆盖配置。

    Returns:
        dict: 扩展后的覆盖配置；简中或没有对应处理器时原样返回。
    """
    if not pipeline_override:
        return pipeline_override
    locale = current_locale(context)
    handler = LOCALE_HANDLERS.get(locale)
    if handler is None:
        return pipeline_override
    try:
        return handler.expand_override(pipeline_override)
    except Exception as e:
        Prompter.error(f"本地化覆盖（{locale}）", e)
        return pipeline_override


def describe() -> str:
    """返回一段可直接打日志的环境摘要，便于排查语言判定问题。"""
    return f"locale={current_locale()} env={os.environ.get(ENV_RESOURCE, '')[:120]}"


__all__ = [
    "BASE_LOCALE",
    "LOCALE_HANDLERS",
    "LOCALE_LABELS",
    "LOCALE_PACKAGES",
    "LocaleHandler",
    "announce",
    "current_locale",
    "describe",
    "detect_from_device",
    "detect_from_screen",
    "localize_override",
    "register_handler",
    "verify",
]
