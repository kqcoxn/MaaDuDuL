"""捏脸功能模块

提供游戏内捏脸功能的自动化识别与操作支持。
通过面部特征识别，自动执行左右捏脸动作。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import random

from agent.customs.utils import Prompter, CounterManager
from agent.customs.maahelper import RecoHelper, ParamAnalyzer, Tasker


@AgentServer.custom_recognition("pface")
class PinchFace(CustomRecognition):
    """捏脸自定义识别类

    用于识别游戏内的捏脸界面，并根据识别结果执行相应的捏脸操作。
    支持左侧和右侧面部特征的识别与调整。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """分析并执行捏脸操作

        通过识别捏脸界面的面部特征，判断需要调整的位置（左侧或右侧），
        并执行相应的捏脸动作。

        参数:
            context: MAA 上下文对象，提供运行时环境
            argv: 自定义识别参数，包含识别配置信息

        返回:
            CustomRecognition.AnalyzeResult: 识别结果，包含识别到的目标信息

        异常:
            捕获所有异常并通过 Prompter.error 返回错误信息
        """
        try:
            args = ParamAnalyzer(argv)
            check_once = (
                True if args.get(["check_once", "co", "o"], "t") == "t" else False
            )
            rh = RecoHelper(context, argv).recognize("捏脸_面部识别")
            if rh.hit:
                res = random.choice(rh.filtered_results)
                context.run_action(
                    "捏脸_左捏" if res.label == "lf" else "捏脸_右捏", res.box
                )
                return rh.rt(res)
            if check_once:
                return rh.rt()
            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("捏脸", e, reco_detail=True)
