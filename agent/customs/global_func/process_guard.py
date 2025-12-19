from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter


@AgentServer.custom_action("on_task_start")
class OnTaskStart(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """任务开始时监听"""
        try:
            return True
        except Exception as e:
            return Prompter.error("设置操作间隔", e)
