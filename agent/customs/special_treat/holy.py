"""
圣团巡礼模块

该模块实现了圣团巡礼活动中的宴席邀请自定义动作，
用于自动邀请指定角色参加宴席。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from typing import List

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("banquet")
class Banquet(CustomAction):
    """
    宴席邀请自定义动作类

    该动作负责执行圣团巡礼活动中的宴席邀请流程，
    根据传入的角色列表依次邀请对应角色。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """
        执行宴席邀请动作

        参数:
            context: MAA 上下文对象，提供任务执行环境
            argv: 动作运行参数，包含邀请角色列表

        返回:
            bool: 邀请成功返回 True，失败返回 False
        """
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            invite_list: List[str] = args.get(["list", "l"])
            # 过滤空字符串
            invite_list = [item for item in invite_list if item and item.strip()]

            Prompter.log(f"邀请名单：{invite_list}")

            # 依次邀请每个角色
            for character in invite_list:
                Prompter.log(f"正在邀请：{character}")
                Tasker(context).run(
                    "圣团巡礼_邀请客人开始",
                    {"圣团巡礼_识别客人": {"expected": character}},
                )

            return True
        except Exception as e:
            return Prompter.error("宴席", e)
