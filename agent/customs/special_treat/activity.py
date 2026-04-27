"""活动相关的自定义动作模块。

本模块提供活动界面导航、活动日活等活动相关的自定义动作实现。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

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
                    {"每日活动作战_速战": {"custom_action_param": f"t={left_times}"}}
                )
                return True
            Prompter.log(f"未检测到活动进度！")
            return False
        except Exception as e:
            return Prompter.error("检查每日活动进度", e)
