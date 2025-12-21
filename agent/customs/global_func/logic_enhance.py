"""逻辑增强模块。

提供用于增强 MAA Pipeline 识别逻辑的自定义识别器，
包括稳定识别等功能，用于提高识别准确性和可靠性。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

from agent.customs.utils import Prompter, CounterManager
from agent.customs.maahelper import RecoHelper, ParamAnalyzer


# ====================  自定义识别器  ====================


@AgentServer.custom_recognition("stable_reco")
class StableReco(CustomRecognition):
    """稳定识别器。

    通过多次连续识别同一目标，确保识别结果的稳定性。
    只有当连续识别次数达到阈值时，才返回识别结果，
    避免因偶然因素导致的误识别。

    参数：
        max/m: 最大连续识别次数，默认为 3
        node/n: 要识别的节点名称或节点名称列表（必需）
                当为列表时，必须每个节点都识别到才算成功
                支持的列表格式：
                - JSON: {"node": ["节点1", "节点2"]}
                - URL参数: node=节点1&node=节点2

    返回：
        识别成功且达到阈值时返回识别结果，否则返回 NoResult
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """执行稳定识别分析。

        参数：
            context: MAA 上下文对象
            argv: 自定义识别参数

        返回：
            识别结果，包含识别到的目标信息或空结果
        """
        try:
            # 解析参数
            params = ParamAnalyzer(argv)
            max_count = params.get(["max", "m"], 3)
            node_name = params.get(["node", "n"], None)
            if not node_name:
                return Prompter.error(
                    "多次连续识别", "未指定节点名称", reco_detail=True
                )

            # 判断 node_name 是单个节点还是列表
            is_list = isinstance(node_name, list)
            node_list = node_name if is_list else [node_name]

            # 使用所有节点名称生成计数器键
            counter_key = "stable_reco_" + (
                "_".join(node_list) if is_list else node_name
            )
            counter = CounterManager.get(counter_key)

            # 对列表中的每个节点进行识别
            all_recognized = True
            best_result = None
            for node in node_list:
                rh = RecoHelper(context, argv).recognize(node)
                if not rh.hit:
                    all_recognized = False
                    break
                # 保存第一个识别结果作为返回值
                if best_result is None:
                    best_result = rh.best_result

            if all_recognized:
                # 所有节点都识别成功，累加计数
                if counter.count() < max_count:
                    # 未达到阈值，继续等待
                    return RecoHelper.NoResult
                # 达到阈值，返回识别结果
                return best_result
            # 识别失败，重置计数器
            counter.reset()
            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("多次连续识别", e, reco_detail=True)
