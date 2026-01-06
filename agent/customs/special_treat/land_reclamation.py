"""开荒功能模块

提供开荒期间的特殊处理功能，包括新商品查看与领取等操作。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import time

from agent.customs.utils import Prompter, MatrixOperator
from agent.customs.maahelper import ParamAnalyzer, Tasker


# ====================  新商品查看与领取  ====================


@AgentServer.custom_action("new_goods")
class NewGoods(CustomAction):
    """新商品查看与领取自定义动作

    用于在开荒期间查看并领取不同商店类型的新商品奖励。
    支持三种商店类型：精品店、房间店和默认的ud类型。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行新商品查看与领取流程

        Args:
            context: MaaFramework上下文对象
            argv: 自定义动作运行参数，支持以下参数：
                - type/t: 商店类型，可选值：
                    - "boutique" 或 "b": 精品店
                    - "room" 或 "r": 房间店
                    - "ud": 默认类型（可省略）

        Returns:
            bool: 执行成功返回True，失败返回False

        Note:
            - 不同商店类型使用不同的计数器上限和流水线配置
            - 精品店使用左右滑动逻辑，房间店使用上下滑动逻辑
        """
        try:
            # 解析参数
            args = ParamAnalyzer(argv)
            store_type = args.get(["type", "t"], "ud")

            # 商店类型
            pipeline_override = {}
            if store_type == "boutique" or store_type == "b":
                pipeline_override = {
                    "新礼包查看_初始化计数器": {"custom_action_param": "k=store&m=15"},
                    "新礼包查看_领取查看奖励": {"roi": [856, 551, 99, 56]},
                    "新礼包查看_获取查看奖励": {"roi": [1163, 108, 0, 0]},
                    "新礼包查看_计数": {"next": "新礼包查看_左右滑动"},
                }
            elif store_type == "room" or store_type == "r":
                pipeline_override = {
                    "新礼包查看_初始化计数器": {"custom_action_param": "k=store&m=5"},
                    "新礼包查看_计数": {"next": "新礼包查看_上下半滑动"},
                }

            Tasker(context).run("新礼包查看_初始化计数器", pipeline_override)
            return True
        except Exception as e:
            # 捕获异常并记录错误日志
            return Prompter.error("领取新商品奖励", e)
