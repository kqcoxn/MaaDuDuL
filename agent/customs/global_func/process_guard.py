"""进程守卫模块。

提供任务生命周期监控和进程状态检测功能，包括任务启动监听和停止检测。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import RecoHelper, ParamAnalyzer, Tasker


# ====================  hooks  ====================


def home_start(context: Context):
    """执行返回主界面的启动钩子。

    参数：
        context：MAA 上下文对象，用于执行任务流程
    """
    Tasker(context).run("懒加载返回主界面_开始")


hook_handler = {"hs": home_start}


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
        global hook_handler
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            task_hooks = args.get(["hook", "h", "type", "t", "class", "cls", "c"], [])
            if not isinstance(task_hooks, list):
                task_hooks = [task_hooks] if task_hooks else []

            # 执行相关逻辑
            for h in task_hooks:
                handler = hook_handler.get(h)
                if handler:
                    handler(context)

            return True
        except Exception as e:
            return Prompter.error("任务启动监听", e)


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
            return RecoHelper.rt() if context.tasker.stopping else RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("检测任务停止", e, reco_detail=True)
