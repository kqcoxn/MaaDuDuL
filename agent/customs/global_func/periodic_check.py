"""周期性任务检查模块。

本模块提供了周期性任务检查的功能，支持按天或按周判断任务是否已完成。
主要功能包括：
    - 任务完成状态的记录和检查
    - 基于刷新时间的日期调整（凌晨4点前算作前一天）
    - 同日/同周判断

典型用法：
    在 Pipeline 中使用 periodic_check 识别器判断任务是否需要执行，
    使用 record_period 动作记录任务完成时间。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context

from typing import Optional
from datetime import datetime, date, timedelta

from agent.customs.utils import Prompter, LocalStorage
from agent.customs.maahelper import ParamAnalyzer


# ====================  日期检查器  ====================


class Inspector:
    """周期性任务检查器。

    提供任务记录和周期判断的核心功能，所有方法均为静态方法。
    支持按天和按周两种周期模式。
    """

    @staticmethod
    def _adjust_datetime() -> datetime:
        """根据游戏刷新时间调整日期。

        考虑到游戏凌晨4点刷新的特性，如果当前时间在凌晨4点之前，
        则认为仍处于前一天。这样可以确保周期判断符合游戏逻辑。

        Returns:
            datetime: 调整后的日期时间对象。

        Example:
            凌晨3点调用时，返回的日期是前一天。
            早上5点调用时，返回的日期是当天。
        """
        current_datetime = datetime.now()
        if current_datetime.hour < 4:
            return current_datetime - timedelta(days=1)
        return current_datetime

    @staticmethod
    def _get_storage_key(key: str) -> str:
        """生成本地存储的键名。

        Args:
            key: 任务标识符。

        Returns:
            str: 格式化后的存储键名，格式为 'last_{key}_date'。
        """
        return f"last_{key}_date"

    @staticmethod
    def record(key: str) -> None:
        """记录任务的最后完成日期。

        将当前日期（经过刷新时间调整）存储到本地，用于后续的周期判断。

        Args:
            key: 任务标识符，用于区分不同的周期性任务。

        Note:
            日期会根据 _adjust_datetime 方法进行调整。
        """
        current_datetime = Inspector._adjust_datetime()
        storage_key = Inspector._get_storage_key(key)
        LocalStorage.set(storage_key, str(current_datetime.date()))

    @staticmethod
    def same_week(key: str) -> bool:
        """判断任务是否在同一周内已完成。

        比较当前日期和上次记录日期的年份和ISO周数。

        Args:
            key: 任务标识符。

        Returns:
            bool: 如果在同一周内已完成返回 True，否则返回 False。
                  如果没有记录或记录格式错误，返回 False。

        Note:
            使用 ISO 8601 标准的周数计算方法。
        """
        current_datetime = Inspector._adjust_datetime()
        storage_key = Inspector._get_storage_key(key)
        last_date_str: Optional[str] = LocalStorage.get(storage_key)

        if not last_date_str:
            return False

        try:
            last_date = date.fromisoformat(last_date_str)
        except Exception as e:
            return False

        return (
            current_datetime.isocalendar()[1] == last_date.isocalendar()[1]
            and current_datetime.year == last_date.year
        )

    @staticmethod
    def same_day(task: str) -> bool:
        """判断任务是否在同一天内已完成。

        比较当前日期和上次记录日期是否为同一天。

        Args:
            task: 任务标识符。

        Returns:
            bool: 如果在同一天内已完成返回 True，否则返回 False。
                  如果没有记录或记录格式错误，返回 False。

        Note:
            日期判断基于调整后的日期（考虑刷新时间）。
        """
        current_datetime = Inspector._adjust_datetime()
        storage_key = Inspector._get_storage_key(task)
        last_date_str: Optional[str] = LocalStorage.get(storage_key)

        if not last_date_str:
            return False

        try:
            last_date = date.fromisoformat(last_date_str)
        except (ValueError, TypeError):
            return False

        return current_datetime.date() == last_date


# ====================  custom  ====================


@AgentServer.custom_recognition("periodic_check")
class PeriodicCheck(CustomRecognition):
    """周期性任务检查识别器。

    用于 Pipeline 中判断周期性任务是否需要执行。
    支持按天（day/d）和按周（week/w）两种周期模式。

    参数说明（通过 argv.custom_param 传入）：
        key/k: (必需) 任务标识符
        periodic/p: (可选) 周期类型，'day'/'d' 或 'week'/'w'，默认 'day'
        record/r: (可选) 是否立即记录，默认 True

    返回：
        bool: True 表示需要执行（未完成），False 表示不需要执行（已完成）

    Example:
        custom_param: "k=daily_task;p=day;r=true"
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """分析周期性任务状态。

        Args:
            context: MAA 上下文对象。
            argv: 识别参数，包含自定义参数。

        Returns:
            CustomRecognition.AnalyzeResult:
                True 表示任务未完成需要执行，
                False 表示任务已完成无需执行。
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"])
            periodic = args.get(["periodic", "p"], "day")
            record_immediately = args.get(["record", "r"], True)

            # 处理布尔参数
            if record_immediately == "false":
                record_immediately = False
            else:
                record_immediately = True

            # 如果需要立即记录，则记录当前时间
            if record_immediately:
                Inspector.record(key)

            # 根据周期类型判断是否已完成
            is_done = False
            if periodic == "week" or periodic == "w":
                is_done = Inspector.same_week(key)
            elif periodic == "day" or periodic == "d":
                is_done = Inspector.same_day(key)

            # 返回是否需要执行
            return not is_done
        except Exception as e:
            return Prompter.error("检查周期任务", e, reco_detail=True)


@AgentServer.custom_action("record_period")
class SetLastPeriodicCheck(CustomAction):
    """记录周期性任务完成时间的动作。

    用于在 Pipeline 中显式记录任务的完成时间。
    通常在任务成功完成后调用。

    参数说明（通过 argv.custom_param 传入）：
        key/k: (必需) 任务标识符

    Example:
        custom_param: "k=daily_task"
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行记录动作。

        Args:
            context: MAA 上下文对象。
            argv: 动作参数，包含自定义参数。

        Returns:
            bool: 成功返回 True，失败返回 False。
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"])
            Inspector.record(key)
            return True
        except Exception as e:
            return Prompter.error("记录检查时间", e)
