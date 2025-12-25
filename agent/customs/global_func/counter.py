"""计数器相关的自定义动作和识别类。

本模块提供了三个自定义功能：
1. InitCounter：初始化计数器
2. Count：执行计数操作
3. CheckCounter：检查计数器状态
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter, CounterManager
from agent.customs.maahelper import ParamAnalyzer, RecoHelper


# ====================  计数器初始化  ====================


@AgentServer.custom_action("init_counter")
class InitCounter(CustomAction):
    """初始化计数器的自定义动作。

    创建或重置指定的计数器，设置初始值和最大值。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行计数器初始化。

        参数：
            context：上下文对象
            argv：运行参数，支持以下字段：
                - key/k：计数器键名，默认为 "default"
                - initial_count/ic：初始计数值，默认为 1
                - max_count/mc：最大计数值，默认为 1

        返回：
            bool：初始化成功返回 True，失败返回 False
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"], "default")
            initial_count = args.get(["initial_count", "ic"], 1)
            max_count = args.get(["max_count", "mc", "m"], 1)
            CounterManager.get(key, initial_count, max_count).reset()
            return True
        except Exception as e:
            return Prompter.error("初始化计数器", e)


# ====================  计数操作  ====================


@AgentServer.custom_action("count")
class Count(CustomAction):
    """执行计数的自定义动作。

    对指定的计数器进行计数操作，每次调用计数值递增。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行计数操作。

        参数：
            context：上下文对象
            argv：运行参数，支持以下字段：
                - key/k：计数器键名，默认为 "default"

        返回：
            bool：计数成功返回 True，失败返回 False
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"], "default")
            CounterManager.get(key).count()
            return True
        except Exception as e:
            return Prompter.error("执行计数", e)


# ====================  计数器状态检查  ====================


@AgentServer.custom_recognition("check_counter")
class CheckCounter(CustomRecognition):
    """检查计数器状态的自定义识别。

    检查指定计数器的当前计数值，当计数值小于 0 时返回识别结果。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """分析并检查计数器状态。

        参数：
            context：上下文对象
            argv：分析参数，支持以下字段：
                - key/k：计数器键名，默认为 "default"

        返回：
            CustomRecognition.AnalyzeResult：
                - 当计数值 < 0 时，返回识别成功结果
                - 否则返回无结果
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"], "default")
            # 检查计数
            if CounterManager.get(key).is_max:
                return RecoHelper.rt()
            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("检查计数器", e, reco_detail=True)
