"""游戏时间工具模块。

提供游戏日期计算功能，处理凌晨3点跨日逻辑。
"""

from datetime import datetime, timedelta


DAILY_REFRESH_HOUR = 3


def get_game_date() -> datetime:
    """获取当前游戏日期。

    游戏日期以凌晨3点为分界线，3点前视为前一天。

    Returns:
        datetime: 当前游戏日期
    """
    now = datetime.now()
    if now.hour < DAILY_REFRESH_HOUR:
        return now - timedelta(days=1)
    return now


def get_game_weekday() -> int:
    """获取当前游戏星期。

    游戏日期以凌晨3点为分界线，3点前视为前一天。

    Returns:
        int: 当前游戏星期（0=周一，1=周二，...，6=周日）
    """
    return get_game_date().weekday()
