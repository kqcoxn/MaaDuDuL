"""任务执行器辅助模块。

本模块提供了 Tasker 类，用于封装 MaaFramework 的任务执行相关操作，
包括节点运行、截图、点击等常用功能。
"""

from maa.context import Context
from maa.define import TaskDetail

import numpy as np


class Tasker:
    """任务执行器类。

    封装了 MaaFramework 的 Context 对象，提供便捷的任务执行接口。

    Attributes:
        context: MaaFramework 的上下文对象，包含任务执行器和控制器。
    """

    def __init__(self, context: Context):
        """初始化任务执行器。

        Args:
            context: MaaFramework 的 Context 对象。
        """
        self.context = context

    def _ctrler(self):
        """获取控制器实例。

        Returns:
            Controller: 当前任务执行器关联的控制器对象。
        """
        return self.context.tasker.controller

    @property
    def stopping(self):
        """检查任务是否正在停止。

        Returns:
            bool: 如果任务正在停止返回 True，否则返回 False。
        """
        return self.context.tasker.stopping

    def run_node(self, node: str):
        """运行单个任务节点。

        执行指定的任务节点，不设置后续节点、中断节点或错误处理节点。

        Args:
            node: 要执行的任务节点名称。

        Returns:
            Tasker: 返回自身，支持链式调用。
        """
        self.context.run_task(
            node, {node: {"next": [], "interrupt": [], "on_error": []}}
        )
        return self

    def screenshot(self) -> np.ndarray:
        """执行截图操作。

        调用控制器进行截图，等待截图完成并获取结果。

        Returns:
            np.ndarray: 截图结果，为 NumPy 数组。
        """
        return self._ctrler().post_screencap().wait().get()

    def click(self, x: int, y: int):
        """执行点击操作。

        在指定坐标位置执行点击操作。

        Args:
            x: 点击位置的 X 坐标（像素）。
            y: 点击位置的 Y 坐标（像素）。

        Returns:
            Tasker: 返回自身，支持链式调用。
        """
        self._ctrler().post_click(x, y).wait()
        return self

    @staticmethod
    def get_last_node_name(task_detail: TaskDetail) -> str:
        if task_detail and task_detail.nodes and len(task_detail.nodes) > 0:
            return task_detail.nodes[-1].name
        return ""
