"""好友换新相关的自定义识别。"""

import re
import unicodedata

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition

from agent.customs.maahelper import ParamAnalyzer, RecoHelper
from agent.customs.utils import Prompter


def parse_elapsed_minutes(text: str) -> int | None:
    """从“x分钟前 / x小时前 / x天前”文本中解析经过的分钟数。"""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"\s+", "", normalized)
    match = re.fullmatch(r"(\d+)(分钟|小时|天)前", normalized)
    if not match:
        return 0 if normalized == "刚刚" else None

    value = int(match.group(1))
    unit_minutes = {"分钟": 1, "小时": 60, "天": 24 * 60}
    return value * unit_minutes[match.group(2)]


@AgentServer.custom_recognition("find_inactive_friend")
class FindInactiveFriend(CustomRecognition):
    """返回最后登录时间达到阈值的最上方好友。

    custom_recognition_param 支持 JSON 或查询字符串格式：
    ``{"threshold": 7}`` / ``threshold=7``。阈值单位为天，默认为 7。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        try:
            threshold = ParamAnalyzer(argv).get(["threshold", "days", "d"], 7)
            if isinstance(threshold, bool) or not isinstance(threshold, int):
                raise ValueError("threshold 必须是整数")
            if threshold < 0:
                raise ValueError("threshold 不能小于 0")

            rh = RecoHelper(context, argv).recognize(
                "识别",
                {
                    "recognition": "OCR",
                    "roi": list(argv.roi),
                },
            )
            if not rh.hit:
                return RecoHelper.NoResult

            results = RecoHelper.merge_nearby(rh.filtered_results, radius=20)
            threshold_minutes = threshold * 24 * 60
            candidates = []
            for result in results:
                elapsed_minutes = parse_elapsed_minutes(result.text)
                if elapsed_minutes is not None and elapsed_minutes >= threshold_minutes:
                    candidates.append(result)

            if not candidates:
                return RecoHelper.NoResult

            target = min(
                candidates,
                key=lambda item: (item.box[1], item.box[0]),
            )
            Prompter.log(f"找到最后登录时间为“{target.text}”的好友")
            x, y, width, height = target.box
            center_box = (x + width // 2, y + height // 2, 1, 1)
            return RecoHelper.rt(box=center_box, text=target.text)
        except Exception as e:
            return Prompter.error("识别好友最后登录时间", e, reco_detail=True)
