from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("buy")
class Buy(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            args = ParamAnalyzer(argv)
            commodity = args.get(["commodity", "c", "goods", "g"])

            context.run_task(
                "每日采购_购买商品",
                {
                    "每日采购_购买商品": {"focus": f"> 购买{commodity}"},
                    "每日采购_查看商品详情": {"expected": commodity},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("进入指定活动", e)
