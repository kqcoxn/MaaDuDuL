"""巅峰对决特殊处理模块。

提供巅峰对决相关的自定义识别功能，包括战斗力解析和对手选择逻辑。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import RecoHelper, ParamAnalyzer, Tasker


# ====================  辅助函数  ====================


def parse_power(text: str) -> int:
    """解析战斗力文本。

    从识别结果中提取战斗力数值，支持全角/半角符号处理。
    OCR可能将千分位分隔符识别为逗号或小数点，均会被正确处理。

    参数：
        text：包含战斗力信息的文本，格式如 "战斗力：12,345" 或 "战斗力：140.489"

    返回：
        战斗力数值（整数）。如果解析失败则返回无穷大

    示例：
        >>> parse_power("战斗力：12,345")
        12345
        >>> parse_power("战斗力：140.489")
        140489
        >>> parse_power("战斗力:10000")
        10000
    """
    # 移除所有非数字字符（战斗力、冒号、逗号、小数点等）
    num_str = "".join(c for c in text if c.isdigit())

    # 尝试转换为整数
    try:
        return int(num_str)
    except ValueError:
        # 解析失败时返回无穷大，确保不会被选中
        return float("inf")


# ====================  自定义识别类  ====================


@AgentServer.custom_recognition("pick_opponent")
class PickOpponent(CustomRecognition):
    """选择对手识别器。

    在巅峰对决中选择战斗力最低的对手。
    通过识别所有对手的战斗力，自动选择数值最小的目标。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """执行对手选择分析。

        识别所有可见对手的战斗力，并返回战斗力最低的目标位置。

        参数：
            context：MaaFramework 上下文
            argv：自定义识别参数

        返回：
            战斗力最低对手的识别结果，包含位置信息
        """
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            strategy = args.get(["strategy", "s"], "min_power")  # min_power, max_rank

            if strategy == "min_power":
                # 最低战力
                # 识别所有对手的战斗力文本
                rh = RecoHelper(context, argv).recognize("巅峰对决_识别战斗力")
                if rh.hit:
                    results = rh.filtered_results
                    # 选择战斗力最低的对手
                    min_result = min(results, key=lambda res: parse_power(res.text))
                    return RecoHelper.rt(min_result)
            elif strategy == "max_rank":
                # 最高排名
                return RecoHelper.rt(box=(695, 234, 0, 0))

            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("选择对手", e, reco_detail=True)
