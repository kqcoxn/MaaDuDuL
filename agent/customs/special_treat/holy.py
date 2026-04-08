"""圣团巡礼模块。

该模块实现了圣团巡礼活动中的自定义动作，包括：
- 宴席邀请：自动邀请指定角色参加宴席
- 冒险协会：管理冒险角色和物品优先级，自动决策日程安排
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import time

from agent.customs.maahelper.reco_helper import RecoHelper
from agent.customs.utils import Prompter
from agent.customs.maahelper import ParamAnalyzer, Tasker
from agent.customs.utils.matrix_operator import MatrixOperator


# ====================  宴席邀请  ====================


@AgentServer.custom_action("list_banquet")
class ListBanquet(CustomAction):
    """宴席邀请自定义动作。

    该动作负责执行圣团巡礼活动中的宴席邀请流程，
    根据传入的角色列表依次邀请对应角色。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行宴席邀请动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数，包含邀请角色列表。

        Returns:
            bool: 邀请成功返回 True，失败返回 False。
        """
        try:
            # 解析参数，获取邀请列表
            args = ParamAnalyzer(argv)
            invite_list = args.split_list(["invite_list", "list", "l"])

            Prompter.log(f"邀请名单：{invite_list}")

            # 依次邀请每个角色
            for character in invite_list:
                Prompter.log(f"正在邀请：{character}")
                Tasker(context).run(
                    "圣团巡礼_邀请客人开始",
                    {
                        "圣团巡礼_识别客人1": {"expected": character},
                        "圣团巡礼_识别客人2": {"expected": character},
                        "圣团巡礼_识别客人3": {"expected": character},
                    },
                )

            return True
        except Exception as e:
            return Prompter.error("宴席", e)


guest_matrix = MatrixOperator(370, 208, 184, 196)
cur_guest_index = (1, 1)


@AgentServer.custom_action("favorites_banquet")
class FavoritesBanquet(CustomAction):
    """收藏客人宴席邀请自定义动作。

    该动作负责按照矩阵布局依次邀请收藏的客人参加宴席，
    通过行列索引定位客人位置并执行邀请流程。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行收藏客人宴席邀请动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数，包含收藏客人数量。

        Returns:
            bool: 邀请成功返回 True，失败返回 False。
        """
        global cur_guest_index
        try:
            # 解析参数，获取收藏客人数量
            args = ParamAnalyzer(argv)
            count = args.get(["count", "c"])
            Prompter.log(f"收藏客人数量：{count}")
            if count > 12:
                Prompter.error("收藏客人数量不能超过 12")

            # 遍历收藏客人矩阵，按行列索引依次邀请
            for i in range(count):
                cur_guest_index = (i // 4 + 1, i % 4 + 1)
                Prompter.log(f"正在邀请：{cur_guest_index}")
                Tasker(context).run(
                    "圣团巡礼_邀请客人开始",
                    {"圣团巡礼_邀请客人开始": {"next": "圣团巡礼_邀请客人2"}},
                )
            Prompter.log(f"邀请结束")

            return True
        except Exception as e:
            return Prompter.error("宴席", e)


@AgentServer.custom_action("click_matrix_guest")
class ClickMatrixGuest(CustomAction):
    """点击矩阵客人位置自定义动作。

    该动作根据当前客人索引，在客人矩阵中定位并点击对应位置。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行点击矩阵客人位置动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数。

        Returns:
            bool: 点击成功返回 True，失败返回 False。
        """
        global cur_guest_index, guest_matrix
        try:
            # 根据当前客人索引获取矩阵坐标并点击
            Tasker(context).click(*guest_matrix.get_pos(*cur_guest_index))
            return True
        except Exception as e:
            return Prompter.error("选择收藏客人", e)


# ====================  冒险协会  ====================


# 全局变量：冒险角色列表
adventure_character_list = []

# 全局变量：物品优先级列表
adventure_item_list = []


@AgentServer.custom_action("set_adventure_character_list")
class SetAdventureList(CustomAction):
    """设置冒险角色列表自定义动作。

    用于配置冒险活动中需要查找的角色优先级列表。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行设置冒险角色列表动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数，包含角色列表。

        Returns:
            bool: 设置成功返回 True，失败返回 False。
        """
        global adventure_character_list
        try:
            # 解析参数，更新全局角色列表
            args = ParamAnalyzer(argv)
            adventure_character_list = args.split_list(["list", "l"])
            Prompter.log(f"冒险角色名单：{adventure_character_list}")
            return True
        except Exception as e:
            return Prompter.error("设置冒险角色名单", e)


@AgentServer.custom_action("set_adventure_item_list")
class SetAdventureItemList(CustomAction):
    """设置物品优先级列表自定义动作。

    用于配置冒险活动中物品的优先级顺序。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行设置物品优先级列表动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数，包含物品列表。

        Returns:
            bool: 设置成功返回 True，失败返回 False。
        """
        global adventure_item_list
        try:
            # 解析参数，更新全局物品列表
            args = ParamAnalyzer(argv)
            adventure_item_list = args.split_list(["list", "l"])
            Prompter.log(f"物品优先级列表：{adventure_item_list}")
            return True
        except Exception as e:
            return Prompter.error("设置物品优先级", e)


@AgentServer.custom_action("find_adventure_character")
class FindAdventureCharacter(CustomAction):
    """查找冒险角色自定义动作。

    从冒险角色列表中取出下一个角色并执行查找流程。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行查找冒险角色动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数。

        Returns:
            bool: 找到角色返回 True，列表为空或失败返回 False。
        """
        global adventure_character_list
        try:
            # 检查角色列表是否为空
            if not adventure_character_list:
                return False

            # 从列表中取出第一个角色
            character = adventure_character_list.pop(0)
            Prompter.log(f"查找角色：{character}")
            Tasker(context).run(
                "圣团巡礼_查找冒险角色开始",
                {
                    "圣团巡礼_识别冒险角色1": {"expected": character},
                    "圣团巡礼_识别冒险角色2": {"expected": character},
                    "圣团巡礼_识别冒险角色3": {"expected": character},
                },
            )
            return True
        except Exception as e:
            return Prompter.error("查找冒险角色", e)


@AgentServer.custom_action("decide_adventure")
class DecideAdventure(CustomAction):
    """冒险日程决策自定义动作。

    根据当前压力值和日程卡片类型（工作/休息），
    自动选择最优的日程安排策略。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行冒险日程决策动作。

        Args:
            context: MAA 上下文对象，提供任务执行环境。
            argv: 动作运行参数。

        Returns:
            bool: 决策成功返回 True，失败返回 False。
        """
        global adventure_item_list
        type_text = {
            "work": "工作",
            "rest": "休息",
            "special_rest": "特别休息",
        }
        try:
            work_indexes = []  # 工作类日程索引列表
            rest_indexes = []  # 休息类日程索引列表
            special_rest_indexes = []  # 特别休息类日程索引列表

            def collect_type_index(index: int):
                """收集指定索引的日程卡片类型。

                Args:
                    index: 日程卡片索引（1-6）。
                """
                card_type = self._get_card_type(context, index)
                type_name = type_text.get(card_type, card_type)
                Prompter.log(f"日程 {index} 类型：{type_name}")
                if card_type == "work":
                    work_indexes.append(index)
                elif card_type == "special_rest":
                    special_rest_indexes.append(index)
                else:
                    rest_indexes.append(index)

            # 识别左侧日程卡片（索引 1-3）
            for i in range(1, 4):
                collect_type_index(i)
            # 切换到右侧，识别右侧日程卡片（索引 4-6）
            self._switch(context, "right")
            for i in range(4, 7):
                collect_type_index(i)

            # 根据压力值进行 3 轮决策
            for i in range(3):
                self._get_pressure(context)
                Prompter.log(f"当前压力：{self._cur_pressure}%")
                if self._cur_pressure >= 35:
                    Prompter.log("压力较大，饮茶先")
                    if special_rest_indexes:
                        Prompter.log("带薪休假！")
                        self._select(context, special_rest_indexes.pop(0))
                    else:
                        self._select(context, rest_indexes.pop(0))
                elif (3 - i) <= len(special_rest_indexes):
                    Prompter.log("带薪休假！")
                    self._select(context, special_rest_indexes.pop(0))
                else:
                    Prompter.log("压力较小，work work！")
                    self._select(context, work_indexes.pop(0))

            return True
        except Exception as e:
            return Prompter.error("冒险", e)

    def _switch(self, context: Context, side: str = None):
        """切换日程卡片左右侧视图。

        Args:
            context: MAA 上下文对象。
            side: 指定切换到哪一侧，'left' 或 'right'。
                  如果为 None，则切换到另一侧。

        Returns:
            str: 当前所在侧，'left' 或 'right'。
        """
        if side == "left":
            Tasker(context).run("圣团巡礼_切换至日程左侧")
            self._cur_side = "left"
        elif side == "right":
            Tasker(context).run("圣团巡礼_切换至日程右侧")
            self._cur_side = "right"
        else:
            # 未指定侧，切换到另一侧
            if self._cur_side == "left":
                Tasker(context).run("圣团巡礼_切换至日程右侧")
                self._cur_side = "right"
            else:
                Tasker(context).run("圣团巡礼_切换至日程左侧")
                self._cur_side = "left"
        time.sleep(0.8)
        return self._cur_side

    def _get_pressure(self, context: Context):
        """识别当前压力指数。

        Args:
            context: MAA 上下文对象。

        Returns:
            int: 当前压力值（百分比）。
        """
        res = RecoHelper(context).recognize("圣团巡礼_识别压力指数").best_result
        text = res.text.replace("%", "")
        self._cur_pressure = int(text)
        return self._cur_pressure

    def _get_card_type(self, context: Context, index=1):
        """获取指定日程卡片的类型。

        Args:
            context: MAA 上下文对象。
            index: 日程卡片索引（1-6），默认为 1。

        Returns:
            str: 卡片类型，'work'（工作）或 'rest'（休息）。
        """
        rh = RecoHelper(context).recognize(
            f"圣团巡礼_识别日程卡片{index}", {"expected": "压力"}
        )
        if not rh.hit:
            return "work"
        rh = RecoHelper(context).recognize(
            f"圣团巡礼_识别日程卡片{index}", {"expected": "特别休息"}
        )
        return "special_rest" if rh.hit else "rest"

    def _select(self, context: Context, index=1):
        """选择指定索引的日程卡片。

        如果目标卡片不在当前视图，会自动切换到对应侧。

        Args:
            context: MAA 上下文对象。
            index: 日程卡片索引（1-6），默认为 1。
        """
        # 如果目标卡片不在当前视图，先切换
        if (index <= 3 and self._cur_side == "right") or (
            index >= 4 and self._cur_side == "left"
        ):
            self._switch(context)
        # 识别并点击目标卡片
        rh = RecoHelper(context).recognize(f"圣团巡礼_识别日程卡片{index}")
        rh.click()
        time.sleep(0.2)
