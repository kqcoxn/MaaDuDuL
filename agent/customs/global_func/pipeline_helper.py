from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("run")
class Run(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            args = ParamAnalyzer(argv)
            task = args.get(["task", "t"])
            expected_end = args.get(["expected_end", "ee", "e"], "")

            task_detail = context.run_task(task)

            if expected_end:
                if Tasker.get_last_node_name(task_detail) != expected_end:
                    return False
            return True
        except Exception as e:
            return Prompter.error("运行任务", e)
