"""进程守卫模块。

提供任务生命周期监控和进程状态检测功能，包括任务启动监听和停止检测。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import RecoHelper


# ====================  任务启动监听  ====================


@AgentServer.custom_action("on_task_start")
class OnTaskStart(CustomAction):
    """任务启动监听器。

    在任务开始时触发，用于执行初始化操作或记录任务启动事件。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行任务启动时的监听逻辑。

        参数：
            context：MAA 上下文对象，包含任务运行环境信息
            argv：自定义动作运行参数

        返回：
            bool：操作成功返回 True，失败返回 False
        """
        try:
            # 任务启动时的处理逻辑（当前为空实现）
            return True
        except Exception as e:
            return Prompter.error("设置操作间隔", e)


# ====================  任务停止检测  ====================


@AgentServer.custom_recognition("check_stopping")
class CheckStopping(CustomRecognition):
    """任务停止状态检测器。

    实时检测任务是否处于即将停止的状态，用于流程控制和资源清理。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """分析任务停止状态。

        参数：
            context：MAA 上下文对象，包含任务执行器状态
            argv：自定义识别分析参数

        返回：
            CustomRecognition.AnalyzeResult：
                如果任务正在停止，返回识别成功结果；
                否则返回无结果状态
        """
        try:
            # 检查任务执行器的停止标志，返回对应的识别结果
            return RecoHelper.rt() if context.tasker.stopping else RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("检测任务停止", e, reco_detail=True)
