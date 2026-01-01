"""商店相关自定义动作模块。

本模块提供商店购买和礼包领取功能的自定义动作实现。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker


@AgentServer.custom_action("gift")
class Gift(CustomAction):
    """礼包领取自定义动作类。

    处理商店中礼包的领取操作。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行礼包领取操作。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，支持以下参数名：
                - gift/g：礼包名称

        Returns:
            bool：领取操作是否成功
        """
        try:
            # 解析参数，获取礼包名称
            args = ParamAnalyzer(argv)
            gift = args.get(["gift", "g"])

            Prompter.log(f"领取{gift}")

            # 执行领取流程
            Tasker(context).run(
                "每日采购_购买礼包开始",
                {
                    "每日采购_选中礼包": {"expected": gift},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("领取指定礼包", e)


@AgentServer.custom_action("buy")
class Buy(CustomAction):
    """商品购买自定义动作类。

    处理商店中商品的购买操作，支持通过多种参数名称指定商品。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行商品购买操作。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，支持以下参数名：
                - goods/g：商品名称
                - commodity/c：商品名称（别名）

        Returns:
            bool：购买操作是否成功
        """
        try:
            # 解析参数，获取商品名称
            args = ParamAnalyzer(argv)
            goods = args.get(
                [
                    "goods",
                    "g",
                    "commodity",
                    "c",
                ]
            )

            Prompter.log(f"购买{goods}")

            # 执行购买流程
            Tasker(context).run(
                "每日采购_购买商品",
                {
                    "每日采购_查看商品详情": {"expected": goods},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("购买指定商品", e)
