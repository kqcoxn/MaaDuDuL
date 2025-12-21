from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("enter_activity")
class EnterActivity(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            args = ParamAnalyzer(argv)
            title = args.get(["title", "t"])

            task_detail = context.run_task(
                "进入活动界面_开始",
                {
                    "进入活动界面_识别活动": {"expected": title},
                    "进入活动界面_未找到指定活动": {"focus": f"> 未找到活动:{title}"},
                },
            )

            if Tasker.get_last_node_name(task_detail) == "进入活动界面_识别活动":
                return True
            return False
        except Exception as e:
            return Prompter.error("进入指定活动", e)
