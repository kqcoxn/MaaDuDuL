from ast import arg
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

from agent.customs.utils import Prompter, CounterManager
from agent.customs.maahelper import RecoHelper, ParamAnalyzer


@AgentServer.custom_recognition("stable_reco")
class StableReco(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """多次连续识别"""
        try:
            # 解析参数
            params = ParamAnalyzer(argv)
            max_count = params.get(["max", "m"], 3)
            node_name = params.get(["node", "n"], None)
            if not node_name:
                return Prompter.error(
                    "多次连续识别", "未指定节点名称", reco_detail=True
                )

            # 获取计数器
            counter_key = "stable_reco_" + node_name
            counter = CounterManager.get(counter_key)

            # 识别
            rh = RecoHelper(context, argv).recognize(node_name)
            if rh.hit:
                if counter.count() <= max_count:
                    return RecoHelper.NoResult
                return rh.best_result
            counter.reset()
            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("多次连续识别", e, reco_detail=True)
