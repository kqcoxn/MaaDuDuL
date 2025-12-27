"""清紫糖关卡选择模块

提供克隆工厂和到手蜡关卡选择的自定义动作。
根据关卡编号自动计算屏幕坐标位置并执行点击操作。

包含功能：
    - SelectCloneLevel：选择克隆工厂关卡（4 列布局）
    - SelectCrayonLevel：选择到手蜡关卡（5 列布局）
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import time

from agent.customs.utils import Prompter, MatrixOperator
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("select_clone_level")
class SelectCloneLevel(CustomAction):
    """选择克隆工厂关卡的自定义动作

    根据传入的关卡编号，自动计算屏幕坐标并点击对应的关卡。
    支持 1-20 关卡的选择，关卡大于 12 时需要先向上滑动界面。

    参数格式：
        - level 或 l：关卡编号（1-20）

    关卡布局：
        - 1-12 关：屏幕可见区域，起始坐标 (118, 238)，每行 4 个，共 3 行
        - 13-20 关：需要向上滑动后可见，起始坐标 (117, 343)，每行 4 个，共 2 行
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            # 解析参数获取关卡编号
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            tasker = Tasker(context)

            # 关卡 13-20：需要向上滑动界面
            if level > 12:
                tasker.swipe(360, 596, 360, 210).wait()
                mo = MatrixOperator(117, 343, 163, 178)
                level -= 8
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))
            # 关卡 1-12：直接点击可见区域
            else:
                mo = MatrixOperator(118, 238, 163, 178)
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))

            return True
        except Exception as e:
            return Prompter.error("选择克隆工厂关卡", e)


@AgentServer.custom_action("select_crayon_level")
class SelectCrayonLevel(CustomAction):
    """选择到手蜡关卡的自定义动作

    根据传入的关卡编号，自动计算屏幕坐标并点击对应的关卡。
    到手蜡关卡采用 5 列布局

    参数格式：
        - level 或 l：关卡编号（从 1 开始）

    关卡布局：
        - 起始坐标：(80, 264)
        - 间隔：横向 123px，纵向 276px
        - 每行 5 个关卡
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            tasker = Tasker(context)

            mo = MatrixOperator(80, 264, 123, 276)
            row = (level - 1) // 5 + 1
            col = (level - 1) % 5 + 1
            tasker.click(*mo.get_pos(row, col))

            return True
        except Exception as e:
            return Prompter.error("选择到手蜡关卡", e)


@AgentServer.custom_action("select_duplicate_level")
class SelectDuplicateLevel(CustomAction):
    """"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """"""
        try:
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            if type(level) is int and level < 10:
                level = f"0{level}"

            Tasker(context).run(
                "清紫糖_查找关卡开始", {"清紫糖_查找指定关卡": {"expected": f"{level}"}}
            )

            return True
        except Exception as e:
            return Prompter.error("选择副本关卡", e)
