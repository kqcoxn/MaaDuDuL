"""识别辅助模块。

提供识别结果处理、点击操作等辅助功能的封装类。
"""

from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition, RecognitionResult, RectType
from maa.context import Context
from maa.controller import Controller

import time
import numpy as np

from .tasker import Tasker


class RecoHelper:
    """识别辅助类。

    封装识别结果的处理、点击操作、结果过滤等常用功能。

    Attributes:
        NoResult: 无识别结果时的默认返回值
        context: MAA 上下文对象
        tasker: 任务执行器
        argv: 识别参数
        screencap: 当前截图缓存
        reco_detail: 最新的识别结果详情
        target: 上次点击的目标坐标
        targets: 批量点击的目标坐标列表
        best_result: 最佳匹配的识别结果
    """

    NoResult = CustomRecognition.AnalyzeResult(box=None, detail={"hit": False})

    def __init__(self, context: Context, argv: CustomRecognition.AnalyzeArg = None):
        """初始化识别辅助器。

        Args:
            context: MAA 上下文对象
            argv: 自定义识别参数，默认为 None
        """
        self.init_tasker(context)
        self.argv = argv
        self.screencap: np.ndarray | None = None

    def init_tasker(self, context: Context):
        """初始化任务执行器。

        Args:
            context: MAA 上下文对象

        Returns:
            self: 返回自身以支持链式调用
        """
        self.context = context
        self.tasker = Tasker(self.context)
        return self

    # ====================  识别相关方法  ====================

    def recognize(
        self,
        node_name: str = "识别",
        override_key_value: dict = {},
        refresh_image=False,
    ):
        """执行识别操作。

        根据参数选择使用缓存截图或刷新截图，然后运行指定节点的识别任务。

        Args:
            node: 识别节点名称，默认为 "识别"
            override_key_value: 覆盖节点的参数字典，默认为空字典
            refresh_image: 是否刷新截图，默认为 False

        Returns:
            self: 返回自身以支持链式调用
        """
        if refresh_image:
            image = self.refresh_screencap().screencap
        elif self.screencap is not None:
            image = self.screencap
        elif self.argv:
            image = self.argv.image
        else:
            image = self.refresh_screencap().screencap
        self.reco_detail = self.context.run_recognition(
            node_name, image, {node_name: override_key_value}
        )
        if self.hit:
            self.filtered_results = self.reco_detail.filtered_results
            self.best_result = self.reco_detail.best_result
        return self

    @property
    def hit(self):
        """判断是否识别到结果。

        Returns:
            bool: 如果识别到结果返回 True，否则返回 False
        """
        return (
            True
            if self.reco_detail
            and self.reco_detail.hit
            and self.reco_detail.best_result
            else False
        )

    def refresh_screencap(self):
        """刷新截图缓存。

        Returns:
            self: 返回自身以支持链式调用
        """
        self.screencap = self.tasker.screenshot()
        return self

    # ====================  点击操作方法  ====================

    def click(self, offset: tuple[int, int] = (0, 0)):
        """点击识别结果的最佳匹配项。

        如果没有识别到结果，则不执行点击操作。

        Args:
            offset: 点击偏移量 (x, y)，默认为 (0, 0)

        Returns:
            self: 如果成功点击返回自身，否则返回 None
        """
        if not self.hit:
            return None
        res = self.reco_detail.best_result
        target = RecoHelper.get_res_center(res)
        self.target = (target[0] + offset[0], target[1] + offset[1])
        self.tasker.click(*self.target)
        return self

    def click_all(
        self,
        offset: tuple[int, int] = (0, 0),
        interval=0.2,
        max_num=99999,
    ) -> tuple[int, int] | None:
        """点击所有识别结果。

        按顺序点击所有过滤后的识别结果，支持设置点击间隔和最大点击数量。

        Args:
            offset: 点击偏移量 (x, y)，默认为 (0, 0)
            interval: 点击间隔时间（秒），默认为 0.2
            max_num: 最大点击数量，默认为 99999

        Returns:
            self: 如果成功点击返回自身，否则返回 None
        """
        if not self.hit:
            return None
        results = self.reco_detail.filtered_results
        self.targets = []
        for i, res in enumerate(results):
            if i + 1 > max_num:
                break
            if i > 0:
                time.sleep(interval)
            target = RecoHelper.get_res_center(res)
            target = (target[0] + offset[0], target[1] + offset[1])
            self.targets.append(target)
            self.tasker.click(*target)
        return self

    # ====================  结果处理方法  ====================

    def concat(self) -> str:
        """拼接所有识别结果的文本。

        将所有过滤后的识别结果的文本内容拼接成一个字符串。

        Returns:
            str: 拼接后的文本字符串，如果没有识别结果则返回 None
        """
        if not self.hit:
            return None
        results = self.reco_detail.filtered_results
        text = ""
        for res in results:
            text += res.text
        return text

    # ====================  静态工具方法  ====================

    @staticmethod
    def get_res_center(result: RecognitionResult) -> tuple[int, int]:
        """计算识别结果的中心坐标。

        Args:
            result: 识别结果对象

        Returns:
            tuple[int, int]: 中心坐标 (x, y)
        """
        box = result.box
        return (round(box[0] + box[2] / 2), round(box[1] + box[3] / 2))

    @staticmethod
    def filter_reco(results: list[RecognitionResult], threshold: float = 0.7):
        """根据可信度过滤识别结果。

        Args:
            results: 识别结果列表
            threshold: 可信度阈值，默认为 0.7

        Returns:
            list[RecognitionResult]: 过滤后的识别结果列表
        """
        return [r for r in results if r.score >= threshold]

    @staticmethod
    def sort_reco(results: list[RecognitionResult]):
        """按可信度对识别结果排序。

        Args:
            results: 识别结果列表

        Returns:
            list[RecognitionResult]: 按可信度降序排列的识别结果列表
        """
        return sorted(results, key=lambda r: r.score, reverse=True)

    @staticmethod
    def rt(
        result: RecognitionResult = None,
        box: RectType = (0, 0, 0, 0),
        text: str = "",
    ):
        """构造识别结果对象。

        支持两种构造方式：
        1. 通过已有的 RecognitionResult 对象创建（优先）
        2. 通过手动指定 box 和 text 参数创建

        Args:
            result: 已有的识别结果对象，如果提供则直接使用其 box 和 text 属性
            box: 识别区域矩形 (x, y, w, h)，默认为 (0, 0, 0, 0)，仅在 result 为 None 时使用
            text: 识别文本内容，默认为空字符串，仅在 result 为 None 时使用

        Returns:
            CustomRecognition.AnalyzeResult: 自定义识别结果对象
        """
        if result:
            box = result.box if hasattr(result, "box") else box
            text = result.text if hasattr(result, "text") else text
        return CustomRecognition.AnalyzeResult(box, {"text": text, "hit": True})
