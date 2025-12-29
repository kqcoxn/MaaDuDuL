"""任务执行器辅助模块。

本模块提供了 Tasker 类，用于封装 MaaFramework 的任务执行相关操作，
包括节点运行、截图、点击等常用功能。
"""

from maa.context import Context
from maa.define import TaskDetail
from maa.tasker import Controller

from typing import Dict
import numpy as np
import time


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

    @property
    def ctl(self) -> Controller:
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

    def run(self, entry: str, pipeline_override: Dict = {}):
        """运行指定的任务节点。

        执行 MaaFramework 任务，会自动为所有节点注入运行监测器，
        确保任务执行过程可被监控。

        Args:
            entry: 任务入口节点名称，即任务流程的起始节点。
            pipeline_override: 任务管道覆盖配置，用于动态修改节点行为，默认为空字典。

        Returns:
            任务执行结果对象。
        """
        # 构造默认 next_override
        node_list = self.context.tasker.resource.node_list
        for node_name in node_list:
            # 跳过监测器节点本身
            if node_name == "_run_task_monitor_inject":
                continue

            # 初始化 next
            node_data = self.context.tasker.resource.get_node_data(node_name)
            current_next = []
            exist_node_override = node_name in pipeline_override
            if exist_node_override:
                if "next" in pipeline_override[node_name]:
                    current_next = pipeline_override[node_name]["next"]
            elif node_data and "next" in node_data:
                current_next = node_data["next"]

            # 注入监测器
            if isinstance(current_next, str):
                current_next = [current_next] if current_next else []
            elif not isinstance(current_next, list):
                current_next = []

            # 检查是否已经注入过监测器，避免嵌套调用时重复注入
            if current_next and current_next[0] == "_run_task_monitor_inject":
                continue

            new_next = ["_run_task_monitor_inject"] + current_next

            # 合成 override
            if exist_node_override:
                pipeline_override[node_name]["next"] = new_next
            else:
                pipeline_override[node_name] = {"next": new_next}

        return self.context.run_task(entry, pipeline_override)

    def screenshot(self) -> np.ndarray:
        """执行截图操作。

        调用控制器进行截图，等待截图完成并获取结果。

        Returns:
            np.ndarray: 截图结果，为 NumPy 数组。
        """
        return self.ctl.post_screencap().wait().get()

    def click(self, x: int, y: int):
        """执行点击操作。

        在指定坐标位置执行点击操作。

        Args:
            x: 点击位置的 X 坐标（像素）。
            y: 点击位置的 Y 坐标（像素）。

        Returns:
            Tasker: 返回自身，支持链式调用。
        """
        self.ctl.post_click(x, y).wait()
        return self

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration=200):
        """执行滑动操作。

        在屏幕上从起始坐标滑动到目标坐标。

        Args:
            x1: 起始位置的 X 坐标（像素）。
            y1: 起始位置的 Y 坐标（像素）。
            x2: 目标位置的 X 坐标（像素）。
            y2: 目标位置的 Y 坐标（像素）。
            duration: 滑动持续时间（毫秒），默认为 200。

        Returns:
            Tasker: 返回自身，支持链式调用。
        """
        self.ctl.post_swipe(x1, y1, x2, y2, duration).wait()
        return self

    def wait(self, minutes: float = 0.5):
        """执行等待操作。

        暂停当前任务执行指定的时间，用于在任务流程中插入延迟。

        Args:
            minutes: 等待时长（分钟），默认为 0.5 分钟。

        Returns:
            Tasker: 返回自身，支持链式调用。
        """
        time.sleep(minutes * 60)
        return self

    @staticmethod
    def get_last_node_name(task_detail: TaskDetail) -> str:
        if task_detail and task_detail.nodes and len(task_detail.nodes) > 0:
            return task_detail.nodes[-1].name
        return ""
