"""诡计骰子每日任务与免费循环对局调度。"""

import re
import time

import numpy as np
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

from agent.customs.maahelper import ParamAnalyzer, RecoHelper, Tasker
from agent.customs.utils import CounterManager, Prompter


def _recognize(context: Context, image: np.ndarray, node: str) -> RecoHelper:
    helper = RecoHelper(context)
    helper.screencap = image
    return helper.recognize(node)


def _run(tasker: Tasker, entry: str) -> bool:
    if tasker.stopping:
        return False
    detail = tasker.run(entry)
    return bool(detail and detail.status.succeeded and not tasker.stopping)


def _entries(context: Context, tasker: Tasker) -> int | None:
    # 切场时标题和按钮可能先于次数出现，单帧漏识别不能直接结束任务。
    deadline = time.monotonic() + 15
    while not tasker.stopping:
        image = tasker.screenshot()
        if _recognize(context, image, "诡计骰子_大厅标记").hit:
            result = _recognize(context, image, "诡计骰子_入场次数")
            if result.hit and result.best_result is not None:
                match = re.search(r"(?:次数)?\s*(\d+)\s*/\s*(\d+)", result.best_result.text)
                if match and 0 <= int(match[1]) <= int(match[2]) <= 80:
                    return int(match[1])
        if time.monotonic() >= deadline:
            break
        tasker.wait(0.3)
    return None


def _daily_progress(context: Context, tasker: Tasker) -> tuple[int, list[int]] | None:
    image = tasker.screenshot()
    if not _recognize(context, image, "诡计骰子_大厅标记").hit:
        return None
    progress, ready = 0, []
    for index in range(1, 4):
        if _recognize(context, image, f"诡计骰子_游玩奖励已领{index}").hit:
            progress = index
        elif _recognize(context, image, f"诡计骰子_游玩奖励可领{index}").hit:
            progress = index
            ready.append(index)
    return progress, ready


def _claim_play_rewards(context: Context, tasker: Tasker) -> int | None:
    status = _daily_progress(context, tasker)
    if status is None:
        return None
    progress, ready = status
    for index in ready:
        if not _run(tasker, f"诡计骰子_领取游玩奖励{index}"):
            return None
        image = tasker.screenshot()
        if not _recognize(context, image, f"诡计骰子_游玩奖励已领{index}").hit:
            Prompter.log(f"第{index}档奖励未确认，停止")
            return None
    if ready:
        Prompter.log("游玩奖励已领取")
    return progress


def _claim_daily_achievements(context: Context, tasker: Tasker) -> bool:
    if not _run(tasker, "诡计骰子_打开成就"):
        return False
    # 显式选择每日任务，避免沿用上次打开的常驻成就页签。
    if not _run(tasker, "诡计骰子_选择每日成就"):
        return False
    image = tasker.screenshot()
    if not _recognize(context, image, "诡计骰子_每日成就已选").hit:
        return False
    if not _recognize(context, image, "诡计骰子_每日成就状态").hit:
        return False
    if _recognize(context, image, "诡计骰子_每日成就可领").hit:
        if not _run(tasker, "诡计骰子_领取每日成就"):
            return False
        image = tasker.screenshot()
        if _recognize(context, image, "诡计骰子_每日成就可领").hit:
            Prompter.log("每日奖励未确认，停止")
            return False
    if not _recognize(context, image, "诡计骰子_每日成就已选").hit:
        return False
    return _run(tasker, "诡计骰子_关闭成就")


def _finish_daily(context: Context, tasker: Tasker, complete: bool) -> bool:
    if not _claim_daily_achievements(context, tasker):
        return False
    if not _run(tasker, "返回主界面"):
        return False
    if not complete:
        Prompter.log("每日游玩未完成")
    return complete


@AgentServer.custom_action("trick_dice_session")
class TrickDiceSession(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            params = ParamAnalyzer(argv)
            mode = params.get("mode", "daily")
            if mode not in ("daily", "loop"):
                Prompter.log("任务模式无效")
                return False
            tasker = Tasker(context)
            # 模式入口分别初始化公共计数器；周期检查和记录仅在每日Pipeline中执行。
            counter = CounterManager.get("诡计骰子每日" if mode == "daily" else "诡计骰子循环", strict=True)
            count = counter.max_count
            if type(count) is not int or count < 1:
                Prompter.log("执行次数无效，停止")
                return False
            if not _run(tasker, "诡计骰子_进入大厅"):
                return False
            # 只使用界面确认的免费次数；一次任务最多消耗初始可用次数。
            budget = _entries(context, tasker)
            if budget is None:
                Prompter.log("入场次数未确认，停止")
                return False
            while not tasker.stopping:
                if mode == "loop" and counter.is_max:
                    return True
                progress = _claim_play_rewards(context, tasker) if mode == "daily" else None
                if mode == "daily":
                    if progress is None:
                        return False
                    if progress == 3:
                        return _finish_daily(context, tasker, True)
                    if counter.is_max:
                        Prompter.log("每日进度未确认，停止")
                        return _finish_daily(context, tasker, False)
                before = _entries(context, tasker)
                if before is None:
                    return False
                if before == 0 or counter.cur_count >= budget:
                    if mode == "daily":
                        return _finish_daily(context, tasker, False)
                    Prompter.log("入场次数不足")
                    return True
                if not _run(tasker, "诡计骰子_单局"):
                    Prompter.log("对局异常，停止")
                    return False
                after = _entries(context, tasker)
                if after is None or after >= before:
                    Prompter.log("结算未确认，停止")
                    return False
                counter.count()
                Prompter.log(f"已完成{counter.cur_count}/{count}局")
            return False
        except Exception as error:
            Prompter.log(f"任务调度异常：{type(error).__name__}")
            return False
