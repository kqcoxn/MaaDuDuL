"""速成班关卡选择模块

本模块实现速成班关卡的自动选择功能，根据当前游戏日期自动确定并点击对应关卡。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from datetime import datetime, timedelta

from agent.customs.utils import Prompter, MatrixOperator, LocalStorage
from agent.customs.maahelper import ParamAnalyzer, Tasker, RecoHelper


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
            游戏日期计算逻辑：凌晨 4 点前视为前一天
        """
        try:
            # 解析自定义动作参数
            args = ParamAnalyzer(argv)

            # 计算游戏日期
            now = datetime.now()
            if now.hour < 4:
                game_date = now - timedelta(days=1)
            else:
                game_date = now
            weekday = game_date.weekday()

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

            return True
        except Exception as e:
            return Prompter.error("选择速成班关卡", e)
