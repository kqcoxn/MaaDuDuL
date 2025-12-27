from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("receive_task_reward")
class ReceiveTaskReward(CustomAction):
    """"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """"""
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            category = args.get(["category", "c"])

            Prompter.log(f"领取{category}任务奖励")
            if category == "日":
                category = "天"

            Tasker(context).run(
                "领取奖励_领取任务奖励开始",
                {
                    "领取奖励_进入具体任务面板": {"expected": f"{category}"},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("领取任务奖励", e)


@AgentServer.custom_action("receive_pass_reward")
class ReceivePassReward(CustomAction):
    """"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """"""
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            category = args.get(["category", "c"])

            Prompter.log(f"领取{category}通行证奖励")
            if category == "等级":
                category = "grade_pass"
            elif category == "便装":
                category = "clothes_path"
            elif category == "冒险":
                category = "adv_pass"

            Tasker(context).run(
                "领取奖励_领取通行证奖励开始",
                {
                    "领取奖励_进入通行证界面": {"template": f"main/{category}.png"},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("领取任务奖励", e)
