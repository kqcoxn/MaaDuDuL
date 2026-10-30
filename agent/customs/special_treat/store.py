"""商店相关自定义动作模块。

本模块提供商店购买和礼包领取功能的自定义动作实现。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import re
import time

from agent.customs.utils import CounterManager, LocalStorage, Prompter, get_game_date
from agent.customs.maahelper import ParamAnalyzer, RecoHelper, Tasker


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
                - type/t：free 表示领取，其他值表示购买，仅影响日志
                - index/i：同名礼包从左到右的序号，从 0 开始，默认 0

        Returns:
            bool：领取操作是否成功
        """
        try:
            # 解析参数，获取礼包名称
            args = ParamAnalyzer(argv)
            gift = args.get(["gift", "g"])
            gift_type = args.get(["type", "t"], "free")
            gift_index = args.get(["index", "i"], 0)
            if type(gift_index) is not int or gift_index < 0:
                raise ValueError("index/i 必须是从 0 开始的整数")

            if gift_type == "free":
                Prompter.log(f"领取{gift}")
            else:
                Prompter.log(f"购买{gift}")

            # 执行领取流程
            Tasker(context).run(
                "每日采购_购买礼包开始",
                {
                    # 每次重设序号，避免后续礼包沿用上一次的覆盖值。
                    "每日采购_选中礼包": {
                        "recognition": {
                            "type": "OCR",
                            "param": {
                                "expected": gift,
                                "order_by": "Horizontal",
                                "index": gift_index,
                            },
                        },
                    },
                },
            )

            return True
        except Exception as e:
            return Prompter.error("领取/购买指定礼包", e)


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


@AgentServer.custom_action("special_buy")
class SpecialBuy(CustomAction):
    """特殊商品购买自定义动作类。

    处理商店中特殊商品的批量购买操作，按固定网格位置依次购买。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行特殊商品批量购买操作。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需额外参数）

        Returns:
            bool：购买操作是否成功
        """
        try:
            # 按 2行3列 网格遍历购买商品
            for i in range(2):  # 行
                for j in range(3):  # 列
                    Prompter.log(f"购买第 {i+1} 行 {j+1} 列商品")
                    Tasker(context).run(
                        "每日采购_购买商品",
                        {
                            "每日采购_查看商品详情": {
                                "recognition": "DirectHit",
                                "target": [660 + j * 224, 174 + i * 220, 1, 1],
                            },
                        },
                    )
                    time.sleep(0.4)

            return True
        except Exception as e:
            return Prompter.error("购买特殊商品", e)


@AgentServer.custom_action("buy_stamina")
class BuyStamina(CustomAction):
    """体力/糖果购买自定义动作类。

    先按水晶叶余额、今日剩余次数与持有上限算出可买次数，再进入购买界面购买。

    Note:
        - 红糖（朱珠糖）为体力，紫糖（星星糖）为模式副本入场资源，日志统一以「单次获得数量」表述；
        - 红糖「+」在主界面，紫糖「+」在冒险页，点「+」前先导航到对应页面；
        - 两种糖果弹窗布局不同，各用一套实测节点，红糖沿用原有节点，紫糖用紫糖专用节点；
        - 价格是递增累计计价，数量输入后必须按整行总价复核，够钱才点购买；
        - 红糖购买每轮只允许一次，用于防止「两遍装备」链路自激。
    """

    # 各糖果的日志用名称、弹窗入口节点与单次获得数量兜底值（0 表示未知）
    ITEMS = {
        "red": ("红糖", "购买糖果_红糖开始", 100),
        "purple": ("紫糖", "购买糖果_紫糖开始", 60),
    }
    # 弹窗内的识别与点击节点，两种糖果各一套
    RED_NODES = {
        "dialog": "购买糖果_检查购买界面",
        "title": "购买糖果_识别弹窗标题",
        "remain": "购买糖果_识别今日剩余次数",
        "held": "购买糖果_识别所持数量",
        "input": "购买糖果_数量输入框",
        "input_text": "购买糖果_输入数量",
        "input_reco": "购买糖果_识别数量输入框",
        "close": "购买糖果_关闭弹窗",
        "cancel": "购买糖果_红糖取消",
        "buy": "购买糖果_点击购买",
        "price": "购买糖果_识别价格行",
    }
    PURPLE_NODES = {
        "dialog": "购买糖果_紫糖检查购买界面",
        "title": "购买糖果_紫糖识别弹窗标题",
        "remain": "购买糖果_紫糖识别今日剩余次数",
        "held": "购买糖果_紫糖识别所持数量",
        "input": "购买糖果_紫糖数量输入框",
        "input_text": "购买糖果_紫糖输入数量",
        "input_reco": "购买糖果_紫糖识别数量输入框",
        "close": "购买糖果_紫糖关闭弹窗",
        "cancel": "购买糖果_紫糖取消",
        "buy": "购买糖果_紫糖点击购买",
        "price": "购买糖果_紫糖识别价格行",
    }
    # 顶部体力节点与 OCR 置信度下限：低于该分的 token 会污染数值解析（例如把图标读成 '2'）
    TOP_NODE = "购买糖果_识别顶部体力"
    OCR_MIN_SCORE = 0.6
    # 导航成功标志：回到主界面、已进入冒险页
    HOME_NODE = "返回主界面_检测主界面"
    ADVENTURE_NODE = "购买糖果_检查冒险页"
    # 持有上限、打开弹窗的最大尝试次数与总价复核次数
    MAX_HOLD = 999
    MAX_OPEN_TRY = 2
    MAX_PRICE_RETRY = 3
    # 水晶叶最低档与最高档单价，用于余额早失败与买不满告警
    MIN_PRICE = 30
    MAX_PRICE = 100
    # 红糖购买轮次计数：第二轮直接拒绝
    PASS_KEY = "buy_red_pass"
    MAX_PASS = 1

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行购买操作。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，支持以下参数名：
                - type/t：糖果类型，red/r 表示红糖，purple/p 表示紫糖
                - count/c：本次最多购买次数，默认 0 表示不购买

        Returns:
            bool：购买操作是否成功
        """
        try:
            args = ParamAnalyzer(argv)
            goods = args.get(["type", "t"])
            count = args.get(["count", "c"], 0)
            strict = bool(args.get(["skip_as_error", "e"], 0))

            if goods in ("red", "r"):
                key = "red"
            elif goods in ("purple", "p"):
                key = "purple"
            else:
                raise ValueError(f"无效的糖果类型：{goods}")

            name, entry, single = self.ITEMS[key]
            nodes = self.RED_NODES if key == "red" else self.PURPLE_NODES

            # 红糖购买每轮只允许一次：再次进入时按未购买处理，避免反复回到刷取流程
            if key == "red":
                counter = CounterManager.get(self.PASS_KEY, self.MAX_PASS, 0)
                if counter.count() < 0:
                    Prompter.log("跳过购买红糖，本轮已买")
                    # 严格模式下只有实际购买才允许回到刷取流程，否则由 on_error 收尾。
                    return not strict

            if not isinstance(count, int) or count <= 0:
                Prompter.log(f"{name}未设置次数，跳过购买")
                return not strict

            try:
                ok, before, bought = self._purchase(
                    context, key, name, entry, nodes, single, count, strict
                )
            finally:
                # 紫糖购买会停在冒险页，恢复到主界面以免影响后续节点
                if key == "purple":
                    Tasker(context).run("返回主界面")

            # 顶部体力只有红糖那套读数口径，紫糖读的是星星糖，不能拿来对账
            if strict and key == "red" and before is not None:
                self._reconcile_stamina(context, name, before)
            return ok
        except Exception as e:
            return Prompter.error("购买体力", e)

    def _purchase(
        self,
        context: Context,
        key: str,
        name: str,
        entry: str,
        nodes: dict[str, str],
        single: int,
        count: int,
        strict: bool = False,
    ) -> tuple[bool, int | None, int]:
        """导航到购买界面并按可买次数购买。

        Args:
            context：MaaFW 上下文对象
            key：糖果类型，red 或 purple
            name：日志用名称
            entry：弹窗入口节点
            nodes：该糖果弹窗用的识别与点击节点
            single：单次获得数量兜底值
            count：本次最多购买次数
            strict：为 True 时，凡是没真正买到的分支都返回 False

        Returns:
            tuple：流程是否可继续、购买前体力、实际买到次数
        """
        # 没有真正买到糖时，strict 模式下要算失败（用于跳过第二遍装备）
        skipped = not strict
        before: int | None = None
        # 先导航到带对应「+」的页面，导航失败不点「+」
        if not self._goto_page(context, key):
            Prompter.log(f"跳过购买{name}，购买界面未出现")
            return skipped, before, 0

        # 已在主界面，strict 且买红糖时记下购买前体力用于对账（紫糖口径不同，不读）
        if strict and key == "red":
            before = self._read_stamina(context)

        # 打开弹窗，识别弹出的是购买界面、上限提示还是没弹出来
        opened = False
        for _ in range(self.MAX_OPEN_TRY):
            last = Tasker.get_last_node_name(Tasker(context).run(entry))
            if last in (nodes["dialog"], nodes["title"]):
                opened = True
                break
            if last == "购买糖果_已满提示":
                Prompter.log(f"跳过购买{name}，已达购买上限")
                return skipped, before, 0
        if not opened:
            Prompter.log(f"跳过购买{name}，购买界面未出现")
            return skipped, before, 0

        # 读取弹窗内的各项数值，读不到一律按 0 处理，宁可跳过也不盲买
        rh = RecoHelper(context).refresh_screencap()
        remain, total = self._remain_pair(self._ocr_text(rh, nodes["remain"]))
        held = self._ints(self._ocr_text(rh, nodes["held"]))
        prices = self._ints(self._ocr_text(rh, nodes["price"]))
        balance = prices[0] if prices else None
        unit = prices[-1] if prices else None
        current = (
            held[0]
            if held
            else self._first_int(rh.recognize(self.TOP_NODE).concat())
        )
        if len(held) >= 2 and held[1] > held[0]:
            single = held[1] - held[0]

        # 次数读不到时保守按 0 处理，绝不盲买
        if remain is None or total is None:
            Prompter.log(f"跳过购买{name}，未能读取今日剩余次数")
            Tasker(context).run(nodes["close"])
            return skipped, before, 0

        spare = 0
        if current is not None and single:
            spare = max((self.MAX_HOLD - current) // single, 0)
        affordable = balance // unit if balance is not None and unit else 0
        used, to_buy, buy = self._plan_buy(count, remain, total, spare, affordable)
        Prompter.log(f"今日还剩 {remain}/{total} 次，已买 {used} 次，本次计划买 {buy} 次")

        if to_buy <= 0:
            Prompter.log(f"跳过购买{name}，今日已买 {used} 次，达到设定 {count}")
            Tasker(context).run(nodes["close"])
            return skipped, before, 0

        # 水晶叶余额早失败：低于最低档单价直接跳过，低于次数×最高档单价只告警
        if balance is not None and unit:
            if balance < self.MIN_PRICE:
                Prompter.log(f"跳过购买{name}，水晶叶余额 {balance} 不足")
                Tasker(context).run(nodes["close"])
                return skipped, before, 0
            if balance < count * self.MAX_PRICE:
                Prompter.log(f"水晶叶可能不够，余额 {balance}，{count} 次最多需 {count * self.MAX_PRICE}")

        if buy <= 0:
            reason = self._skip_reason(remain, current, balance, unit, single)
            Prompter.log(f"跳过购买{name}，{reason}")
            Tasker(context).run(nodes["close"])
            return skipped, before, 0

        # 只有某一约束严格小于其余约束时，才认为是它压小了购买次数
        if affordable < min(to_buy, spare):
            Prompter.log(f"水晶叶不够买{name}了喵~只买到 {buy} 次")
        elif spare < min(to_buy, affordable):
            if key == "red":
                Prompter.log(f"红糖将溢出，只买到上限 {buy} 次")
            else:
                Prompter.log(f"紫糖将达持有上限，只买到 {buy} 次")
        else:
            Prompter.log(f"购买{name} {buy} 次")

        # 价格是累计计价，输入数量后必须用整行总价复核，够钱才点购买
        bought = self._confirm_price(context, name, nodes, buy)
        if bought is None:
            Tasker(context).run(nodes["cancel"])
            return skipped, before, 0

        Tasker(context).run(nodes["buy"])
        return True, before, bought

    def _read_stamina(self, context: Context) -> int | None:
        """读一次顶部红糖体力。

        延迟导入避免与 eat_sugar 形成循环依赖（eat_sugar 依赖本模块的状态类）。

        Args:
            context：MaaFW 上下文对象

        Returns:
            int | None：当前体力，读不到时返回 None
        """
        from .eat_sugar import read_stamina

        return read_stamina(context)

    def _reconcile_stamina(self, context: Context, name: str, before: int) -> int | None:
        """购买后展示一次体力变化，仅日志展示，不做任何判断。

        Args:
            context：MaaFW 上下文对象
            name：日志用的糖果名（红糖 / 紫糖）
            before：购买前体力

        Returns:
            int | None：购买后体力，读不到时返回 None
        """
        after = self._read_stamina(context)
        shown = after if after is not None else "未读到"
        Prompter.log(f"{name} {before} → {shown}")
        return after

    def _confirm_price(
        self, context: Context, name: str, nodes: dict[str, str], buy: int
    ) -> int | None:
        """输入数量并复核整行总价，返回最终确认购买的数量。

        Args:
            context：MaaFW 上下文对象
            name：日志用名称
            nodes：该糖果弹窗用的识别与点击节点
            buy：初定购买数量

        Returns:
            int | None：可以下单的数量，买不起或数量输入未生效时返回 None
        """
        for attempt in range(self.MAX_PRICE_RETRY + 1):
            Tasker(context).run(
                nodes["input"], {nodes["input_text"]: {"input_text": str(buy)}}
            )
            rh = RecoHelper(context).refresh_screencap()
            typed = self._first_int(rh.recognize(nodes["input_reco"]).concat())
            if typed != buy:
                Prompter.log(
                    f"取消购买{name}，数量输入未生效，期望 {buy} 实得 {typed if typed is not None else '未识别'}"
                )
                return None

            prices = self._ints(self._ocr_text(rh, nodes["price"]))
            if len(prices) < 2:
                Prompter.log(f"取消购买{name}，未能识别价格行的余额与总价")
                return None
            balance, total = prices[0], prices[-1]
            if total <= balance:
                return buy
            if buy <= 1 or attempt == self.MAX_PRICE_RETRY:
                Prompter.log(f"取消购买{name}，买 {buy} 次需 {total} 叶，余额仅 {balance}")
                return None
            Prompter.log("少点看看…")
            buy -= 1

        return None

    def _goto_page(self, context: Context, key: str) -> bool:
        """导航到带对应「+」的页面。

        Args:
            context：MaaFW 上下文对象
            key：糖果类型，red 或 purple

        Returns:
            bool：是否到达目标页面
        """
        last = Tasker.get_last_node_name(Tasker(context).run("返回主界面"))
        if last != self.HOME_NODE:
            return False
        if key == "red":
            return True
        last = Tasker.get_last_node_name(Tasker(context).run("购买糖果_进入冒险页"))
        return last == self.ADVENTURE_NODE

    @classmethod
    def _ocr_text(cls, rh: RecoHelper, node: str) -> str:
        """取节点 OCR 文本，丢弃置信度过低的结果。

        低分 token 会拼进数值串造成误读（实测价格行把水晶叶图标读成 '2'，
        与 '14,803 / 70' 拼成 '214,803 / 70'，余额被当成 214）。
        过滤后为空则返回空串，交给上层的保守跳过逻辑。

        Args:
            rh：识别辅助器
            node：识别节点名

        Returns:
            str：拼接后的高置信文本，可能为空串
        """
        rh.recognize(node)
        if not rh.hit:
            return ""
        return "".join(
            result.text for result in rh.filtered_results if result.score >= cls.OCR_MIN_SCORE
        )

    @staticmethod
    def _plan_buy(count: int, remain: int, total: int, spare: int, affordable: int) -> tuple[int, int, int]:
        """按「今日累计购买次数」语义算出本次实际购买次数。

        Args:
            count：设定值，即今日累计想买到的次数
            remain：界面显示的今日剩余次数 X
            total：界面显示的今日上限 Y
            spare：持有上限余量
            affordable：水晶叶可负担次数

        Returns:
            tuple：今日已买次数、按设定值还需补的次数、本次实际购买次数
        """
        used = max(total - remain, 0)
        to_buy = max(min(count, total) - used, 0)
        return used, to_buy, min(to_buy, spare, affordable)

    @classmethod
    def _remain_pair(cls, text: str | None) -> tuple[int | None, int | None]:
        """解析「今日剩余购买次数：X/Y」中的剩余次数与今日上限。

        Args:
            text：识别到的文本

        Returns:
            tuple：剩余次数 X 与今日上限 Y，解析不到时对应位置为 None
        """
        match = re.search(r"(\d+)\s*/\s*(\d+)", text or "")
        if match:
            return int(match.group(1)), int(match.group(2))
        numbers = cls._ints(text)
        if len(numbers) >= 2:
            return numbers[0], numbers[1]
        return (numbers[0] if numbers else None), None

    @staticmethod
    def _ints(text: str | None) -> list[int]:
        """提取文本中的所有整数。

        Args:
            text：待提取的文本

        Returns:
            list：提取到的整数列表，无结果时为空列表
        """
        return [int(n) for n in re.findall(r"\d+", (text or "").replace(",", ""))]

    @classmethod
    def _first_int(cls, text: str | None, default=None):
        """提取文本中的第一个整数。

        Args:
            text：待提取的文本
            default：文本中没有整数时的返回值

        Returns:
            int | None：第一个整数，无结果时返回 default
        """
        numbers = cls._ints(text)
        return numbers[0] if numbers else default

    @staticmethod
    def _skip_reason(remain, current, balance, unit, single) -> str:
        """说明本次无法购买的原因。

        Args:
            remain：今日剩余购买次数
            current：当前持有数量
            balance：水晶叶余额
            unit：单次购买的价格
            single：单次获得数量

        Returns:
            str：无法购买的原因
        """
        if not remain:
            return "未识别到今日剩余购买次数"
        if current is None or not single:
            return "未识别到所持数量"
        if balance is None or not unit:
            return "未识别到水晶叶余额或价格行"
        if balance // unit <= 0:
            return "水晶叶不足"
        return "持有数量已达上限"


class RedReserve:
    """活动任务红糖预留的共享判断。

    由清红糖任务的预留开关驱动 清红糖_预留设置 节点配置，
    速战发起前的预留场次判断与体力不足弹窗内的购买上限都读这里的状态。

    Note:
        - 预留只在当日「每日活动作战」尚未完成时生效；
        - 完成日期沿用 periodic_check 的存储键与凌晨 3 点口径。
    """

    STORAGE_KEY = "last_每日活动作战_date"
    HOLD_TOTAL = 999
    threshold = 0

    @classmethod
    def configure(cls, reserve) -> None:
        """按开关配置预留阈值。

        Args:
            reserve：预留体力阈值，0 或非正数表示不预留
        """
        threshold = reserve if isinstance(reserve, int) and reserve > 0 else 0
        if threshold <= 0:
            cls.threshold = 0
            return
        if cls.done_today():
            cls.threshold = 0
            return
        cls.threshold = threshold

    @classmethod
    def done_today(cls) -> bool:
        """判断每日活动作战今天是否已完成。

        Returns:
            bool：今天已完成返回 True
        """
        last = LocalStorage.get(cls.STORAGE_KEY)
        if not last:
            return False
        return str(last) == str(get_game_date().date())

    @classmethod
    def active(cls) -> bool:
        """预留是否生效。

        Returns:
            bool：生效返回 True
        """
        return cls.threshold > 0

    @classmethod
    def hold_cap(cls) -> int:
        """预留生效时的持有上限。

        Returns:
            int：预留生效时返回 上限 - 预留值，否则返回原持有上限
        """
        if cls.active():
            return cls.HOLD_TOTAL - cls.threshold
        return cls.HOLD_TOTAL


@AgentServer.custom_action("red_reserve")
class RedReserveConfig(CustomAction):
    """活动体力预留配置自定义动作类。

    每次任务开始时按开关值重设预留状态，避免沿用上一次运行的残留。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """配置活动体力预留。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，reserve/r 为预留体力阈值，0 表示不预留

        Returns:
            bool：配置流程执行完毕返回 True
        """
        try:
            args = ParamAnalyzer(argv)
            reserve = args.get(["reserve", "r"], 0)
            RedReserve.configure(reserve)
            return True
        except Exception as e:
            return Prompter.error("配置活动体力预留", e)


@AgentServer.custom_action("red_supply")
class RedSupply(BuyStamina):
    """体力不足弹窗内就地购买红糖。

    不导航也不打开弹窗，直接在「是否购买朱珠糖？」弹窗里按可买次数购买：
    买到返回 True 交给速战继续；买不了点「取消」并返回 False，由 on_error 收尾。

    Note:
        由 eat_sugar.run_candy_fight 在发起速战时把本节点写进 速战_体力不足.next：
        调用方显式传入的 next 不会被 Tasker.run 的 monitor 重建覆盖，所以能生效。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """在体力不足弹窗内购买红糖。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，count/c 为本次最多购买次数

        Returns:
            bool：买到返回 True，买不了返回 False
        """
        try:
            args = ParamAnalyzer(argv)
            count = args.get(["count", "c"], 0)
            if not isinstance(count, int) or count <= 0:
                return self._cancel(context, "未设置红糖购买次数")

            nodes = self.RED_NODES
            rh = RecoHelper(context).refresh_screencap()
            remain, total = self._remain_pair(self._ocr_text(rh, nodes["remain"]))
            held = self._ints(self._ocr_text(rh, nodes["held"]))
            prices = self._ints(self._ocr_text(rh, nodes["price"]))
            balance = prices[0] if prices else None
            unit = prices[-1] if prices else None
            current = held[0] if held else self._first_int(rh.recognize(self.TOP_NODE).concat())
            single = self.ITEMS["red"][2]
            if len(held) >= 2 and held[1] > held[0]:
                single = held[1] - held[0]

            # 次数读不到时保守按 0 处理，绝不盲买
            if remain is None or total is None:
                return self._cancel(context, "未能读取今日剩余购买次数")

            hold = RedReserve.hold_cap()
            spare = 0
            if current is not None and single:
                spare = max((hold - current) // single, 0)
            affordable = balance // unit if balance is not None and unit else 0
            used, to_buy, buy = self._plan_buy(count, remain, total, spare, affordable)
            Prompter.log(f"今日还剩 {remain}/{total} 次，已买 {used} 次，本次计划买 {buy} 次")

            if to_buy <= 0:
                return self._cancel(context, f"今日已购买 {used} 次，达到设定值 {count}")
            if balance is not None and balance < self.MIN_PRICE:
                return self._cancel(context, f"水晶叶不足（余额 {balance}）")
            if balance is not None and balance < count * self.MAX_PRICE:
                Prompter.log(f"水晶叶可能不够，余额 {balance}，{count} 次最多需 {count * self.MAX_PRICE}")
            if buy <= 0:
                reason = self._skip_reason(remain, current, balance, unit, single)
                return self._cancel(context, f"当前无法购买（{reason}）")

            if self._confirm_price(context, "红糖", nodes, buy) is None:
                return self._cancel(context, "总价复核未通过")

            Tasker(context).run(nodes["buy"])
            Prompter.log(f"在体力不足弹窗内购买红糖 {buy} 次")
            return True
        except Exception as e:
            return Prompter.error("补糖", e)

    @staticmethod
    def _cancel(context: Context, reason: str) -> bool:
        """关掉体力不足弹窗并报告跳过原因。

        Args:
            context：MaaFW 上下文对象
            reason：跳过原因

        Returns:
            bool：固定返回 False
        """
        Prompter.log(f"跳过补糖，{reason}")
        Tasker(context).run(BuyStamina.RED_NODES["cancel"])
        return False

