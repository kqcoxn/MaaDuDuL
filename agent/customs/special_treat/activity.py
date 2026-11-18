"""活动相关的自定义动作模块。

本模块提供活动界面导航、活动日活等活动相关的自定义动作实现。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import re
import time

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker, RecoHelper

# ====================  活动界面导航  ====================


@AgentServer.custom_action("enter_activity")
class EnterActivity(CustomAction):
    """进入指定活动界面的自定义动作。

    通过活动标题查找并进入对应的活动界面。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行进入活动界面的操作。

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，期望包含：
                - title/t：活动标题名称

        返回：
            bool：成功进入活动界面返回 True，否则返回 False
        """
        try:
            # 解析参数，获取活动标题
            args = ParamAnalyzer(argv)
            title = args.get(["title", "t"])

            # 运行进入活动界面的 Pipeline 任务
            task_detail = Tasker(context).run(
                "进入活动界面_开始",
                {
                    "进入活动界面_识别活动": {"expected": title},
                    "进入活动界面_未找到指定活动": {"focus": f"> 未找到活动:{title}"},
                },
            )

            # 检查最后执行的节点，判断是否成功进入活动
            if Tasker.get_last_node_name(task_detail) == "进入活动界面_识别活动":
                return True
            return False
        except Exception as e:
            return Prompter.error("进入指定活动", e)


# ====================  活动日活  ====================


@AgentServer.custom_action("check_activity_progress")
class CheckActivityProgress(CustomAction):
    """检查活动进度的自定义动作。

    识别每日活动作战的进度信息，计算剩余挑战次数并动态调整后续任务参数。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行检查活动进度的操作。

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数（本动作暂未使用参数）

        返回：
            bool：成功识别进度并计算剩余次数返回 True，识别失败或发生异常返回 False
        """
        try:
            rh = RecoHelper(context).recognize("每日活动作战_识别进度")
            if rh.hit:
                progress = (
                    rh.best_result.text.replace(" ", "")
                    .replace("/20", "")
                    .replace("120", "")
                    .replace("020", "")
                    .replace(":20", "")
                    .replace("：20", "")
                )

                progress = int(progress)
                if progress < 0:
                    progress = -progress
                left_times = 20 - int(progress)
                progress = min(progress, 20)

                if left_times <= 0:
                    Prompter.log(f"今日已完成活动作战")
                    return False
                Prompter.log(f"剩余次数：{left_times}")
                context.override_pipeline(
                    {
                        "每日活动作战_速战": {"custom_action_param": f"t={left_times}"},
                        "每日活动作战2_速战": {
                            "custom_action_param": f"t={left_times}"
                        },
                    },
                )
                return True
            context.override_pipeline(
                {
                    "每日活动作战_速战": {"custom_action_param": f"t=20"},
                    "每日活动作战2_速战": {"custom_action_param": f"t=20"},
                },
            )
            Prompter.log(f"未检测到活动进度！")
            return False
        except Exception as e:
            return Prompter.error("检查每日活动进度", e)


@AgentServer.custom_action("check_activity_achievement")
class CheckActivityAchievement(CustomAction):
    """检查活动任务「成就」页里各档「完成活动关卡」次数成就是否已全部完成。

    切到「成就」页，从顶端往下滑到底，收集各档次数成就（如 100 次、200 次）的进度，再切回
    「每日任务」页，后续的进度检查与领取都在「每日任务」页进行。目标最高的一档也已完成时返回
    False，交给 on_error 跳过作战；未完成、找不到该成就或出错时返回 True，照常作战。

    「每日任务」页也有同名的「完成活动关卡」（10/20 次），所以切页前后各读一次列表，
    内容没变就视为没切过去，照常作战。
    """

    TAB_ACHIEVEMENT = "每日活动作战_成就分页"
    TAB_DAILY = "每日活动作战_每日任务分页"
    LIST_NODE = "每日活动作战_识别成就"
    # 次数成就的标题，不含「微辣」「中辣」「地狱辣」等难度后缀
    TITLE = re.compile(r"完成活[动動][关關閣間]卡")
    PROGRESS = re.compile(r"(\d+)/(\d+)")
    # 进度条在标题下方，离标题超过这个距离就不认
    MAX_GAP = 120
    # 每日任务里同名任务的目标最多 20 次，次数成就的目标一定更多
    DAILY_TARGET = 20
    # 成就列表向下滑动（1280x720 基准），滑到列表内容不再变化为止
    SWIPE = (880, 560, 880, 230)
    SWIPE_MS = 500
    MAX_PAGES = 6

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行检查活动关卡次数成就的操作。

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数（本动作暂未使用参数）

        返回：
            bool：各档次数成就都已完成返回 False，其余情况返回 True
        """
        try:
            tiers = None
            rh = RecoHelper(context)
            before = self._list_texts(rh)
            if rh.recognize(self.TAB_ACHIEVEMENT).hit:
                rh.click()
                time.sleep(1)
                results = self._list_results(rh)
                if sorted(r.text for r in results) != before:
                    tiers = self._collect_tiers(context, rh, results)
                if rh.recognize(self.TAB_DAILY, refresh_image=True).hit:
                    rh.click()
                    time.sleep(1)

            if tiers is None:
                Prompter.log("未能切换到「成就」页，照常作战")
                return True
            if not tiers:
                Prompter.log("未找到「完成活动关卡」成就，照常作战")
                return True
            summary = "、".join(f"{total} 次 {done}/{total}" for total, done in sorted(tiers.items()))
            top = max(tiers)
            if tiers[top] >= top:
                Prompter.log(f"「完成活动关卡」成就已全部完成（{summary}），今日不再作战")
                return False
            Prompter.log(f"「完成活动关卡」成就尚未全部完成（{summary}），照常作战")
            return True
        except Exception as e:
            Prompter.error("检查活动关卡成就", e)
            return True

    def _collect_tiers(self, context: Context, rh: RecoHelper, results: list) -> dict[int, int]:
        """从成就列表当前位置往下滑到底，收集各档次数成就的 {目标次数: 已完成次数}。"""
        tasker = Tasker(context)
        tiers: dict[int, int] = {}
        seen = None
        for _ in range(self.MAX_PAGES):
            texts = sorted(r.text for r in results)
            if texts == seen:
                break
            seen = texts
            for total, done in self._tiers(results).items():
                tiers[total] = max(done, tiers.get(total, 0))
            tasker.swipe(*self.SWIPE, duration=self.SWIPE_MS)
            time.sleep(1)
            results = self._list_results(rh)
        return tiers

    def _list_results(self, rh: RecoHelper) -> list:
        """重新截图并读取任务列表区域的全部 OCR 结果。"""
        rh.recognize(self.LIST_NODE, refresh_image=True)
        return list(rh.reco_detail.all_results) if rh.reco_detail else []

    def _list_texts(self, rh: RecoHelper) -> list[str]:
        """读取任务列表区域的文字，用于比较切页前后是否有变化。"""
        return sorted(r.text for r in self._list_results(rh))

    def _tiers(self, results) -> dict[int, int]:
        """在一屏成就列表的 OCR 结果里，找出每个「完成活动关卡」标题下方最近的进度。

        返回 {目标次数: 已完成次数}；标题在屏幕底部、进度被截掉时这一屏不计，滑动后再读到。
        """
        texts = [(r.box, r.text.replace(" ", "")) for r in results]
        titles = [box for box, text in texts if self.TITLE.fullmatch(text)]
        bars = []
        for box, text in texts:
            matched = self.PROGRESS.fullmatch(text)
            if matched and int(matched.group(2)) > self.DAILY_TARGET:
                bars.append((box, int(matched.group(1)), int(matched.group(2))))
        tiers: dict[int, int] = {}
        for title in titles:
            below = [
                (box[1] - title[1], done, total)
                for box, done, total in bars
                if 0 < box[1] - title[1] <= self.MAX_GAP
            ]
            if below:
                _, done, total = min(below)
                tiers[total] = max(done, tiers.get(total, 0))
        return tiers
