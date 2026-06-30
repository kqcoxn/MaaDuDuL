"""速成班关卡选择模块

本模块实现速成班关卡的自动选择功能，根据当前游戏日期自动确定并点击对应关卡。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter, LocalStorage, get_game_weekday
from agent.customs.maahelper import ParamAnalyzer, Tasker, RecoHelper

# 当前副本编号，由 SelectCramLevel 写入，供 SelectCramBattleLevel 读取
_current_dungeon: int = 1


@AgentServer.custom_action("select_cram_level")
class SelectCramLevel(CustomAction):
    """速成班关卡选择自定义动作

    根据当前游戏日期自动选择速成班关卡：
        - 周一至周五：根据日期直接选择对应关卡（1-5）
        - 周六：根据参数选择，可选关卡 1/2/3
        - 周日：根据参数选择，可选关卡 4/5
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行关卡选择逻辑

        Args:
            context: MaaFramework 上下文对象
            argv: 自定义动作运行参数

        Returns:
            bool: 执行成功返回 True，失败返回 False

        Note:
            游戏日期计算逻辑：凌晨 3 点前视为前一天
        """
        try:
            # 解析自定义动作参数
            args = ParamAnalyzer(argv)

            # 获取游戏星期
            weekday = get_game_weekday()

            # 根据游戏日期选择关卡
            weekday_names = ["一", "二", "三", "四", "五", "六", "日"]
            level = 1
            if weekday < 5:
                # 周一至周五：关卡与星期对应（1-5）
                level = weekday + 1
                Prompter.log(f"游戏日期为周{weekday_names[weekday]}，选择关卡 {level}")
            elif weekday == 5:
                # 周六：从参数读取关卡（可选 1/2/3）
                level = args.get(["week_6", "w6"], 2)
                if level not in [1, 2, 3]:
                    Prompter.log(f"周六关卡 {level} 无效，使用默认关卡 2")
                    level = 2
                Prompter.log(f"游戏日期为周六，选择关卡 {level}")
            else:
                # 周日：从参数读取关卡（可选 4/5）
                level = args.get(["week_7", "w7"], 5)
                if level not in [4, 5]:
                    Prompter.log(f"周日关卡 {level} 无效，使用默认关卡 5")
                    level = 5
                Prompter.log(f"游戏日期为周日，选择关卡 {level}")

            # 执行点击操作
            Tasker(context).click(130 + (level - 1) * 256, 354)

            # 保存当前副本编号供后续速刷关卡选择使用
            global _current_dungeon
            _current_dungeon = level

            return True
        except Exception as e:
            return Prompter.error("选择速成班关卡", e)


@AgentServer.custom_action("select_cram_battle_level")
class SelectCramBattleLevel(CustomAction):
    """速刷关卡选择自定义动作

    进入当天副本后，根据 SelectCramLevel 保存的副本编号和配置选择具体速刷关卡。
    参数 1-5 分别对应5个副本的速刷关卡号。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行速刷关卡选择逻辑

        读取 SelectCramLevel 保存的副本编号，使用对应参数中的关卡号，
        调用"短期速成班_识别速战关卡"节点进行 OCR 识别并点击。

        Args:
            context: MaaFramework 上下文对象
            argv: 自定义动作运行参数

        Returns:
            bool: 执行成功返回 True，失败返回 False
        """
        try:
            # 解析自定义动作参数，获取各副本的关卡号
            args = ParamAnalyzer(argv)
            levels = {
                1: args.get("1", "25"),
                2: args.get("2", "25"),
                3: args.get("3", "25"),
                4: args.get("4", "25"),
                5: args.get("5", "25"),
            }

            # 读取 SelectCramLevel 保存的当前副本编号
            dungeon = _current_dungeon
            level = levels[dungeon]

            # 使用识别辅助器识别关卡并点击
            rh = RecoHelper(context).recognize(
                "短期速成班_识别速战关卡", {"expected": f"第{level}课"}
            )

            if rh.hit:
                rh.click()
                Prompter.log(f"选择副本{dungeon}的第{level}课")
                return True

            Prompter.log("未识别到速刷关卡")
            return False
        except Exception as e:
            return Prompter.error("选择速刷关卡", e)
