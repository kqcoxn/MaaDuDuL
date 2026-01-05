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


@AgentServer.custom_action("quick_fight")
class QuickFight(CustomAction):
    """快速战斗的自定义动作

    直接启动速战流程，支持指定作战次数。
    当指定次数时，会覆盖速战流程中的相关配置。

    参数格式：
        - times 或 t：作战次数（可选，默认为 -1 表示不限次数）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行快速战斗操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含作战次数

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            # 解析参数获取关卡编号
            args = ParamAnalyzer(argv)
            times: int = args.get(["times", "t"], -1)

            pipeline_override = {}
            if times > 0:
                Prompter.log(f"指定作战次数：{times} 次")
                pipeline_override = {
                    "速战_确保可战斗": {"next": "速战_指定作战次数"},
                    "速战_输入作战次数": {"input_text": str(times)},
                }

            Tasker(context).run("速战_开始", pipeline_override)

            return True
        except Exception as e:
            return Prompter.error("速战", e)


@AgentServer.custom_action("select_clone_level")
class SelectCloneLevel(CustomAction):
    """选择克隆工厂关卡的自定义动作

    根据传入的关卡编号，自动计算屏幕坐标并点击对应的关卡。

    参数格式：
        - level 或 l：关卡编号（1-15）

    关卡布局：
        - 1-8 关：屏幕可见区域，起始坐标 (118, 238)，每行 4 个，共 2 行
        - 9-15 关：需要向上滑动后可见，起始坐标 (117, 343)，每行 4 个，共 2 行
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

            # 关卡 1-8
            if level < 8:
                tasker.swipe(360, 210, 360, 596).wait()
                mo = MatrixOperator(118, 238, 163, 178)
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))

            # 关卡 9-15
            else:
                tasker.swipe(360, 596, 360, 210).wait()
                mo = MatrixOperator(117, 343, 163, 178)
                level -= 8
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
    """选择副本关卡的自定义动作

    根据传入的关卡编号，通过 Pipeline 查找并选择对应的副本关卡。
    自动将小于 10 的关卡编号格式化为两位数字（如 1 转换为 "01"）。

    参数格式：
        - level 或 l：关卡编号（整数型）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行副本关卡选择操作

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
            if type(level) is int and level < 10:
                level = f"0{level}"

            Tasker(context).run(
                "清紫糖_查找关卡开始", {"清紫糖_查找指定关卡": {"expected": f"{level}"}}
            )

            return True
        except Exception as e:
            return Prompter.error("选择副本关卡", e)
