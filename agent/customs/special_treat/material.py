"""装备材料刷取相关自定义动作模块。

本模块提供装备材料获取途径的星级关卡定位与装备刷取轮次控制，
速战部分复用通用「速战」流水线（由 eat_sugar.run_candy_fight 编排）。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

import numpy as np

from agent.customs.utils import CounterManager, Prompter
from agent.customs.maahelper import ParamAnalyzer, RecoHelper, Tasker

from .eat_sugar import FIGHT_LOGGED_EXITS, fight_finished, run_candy_fight


@AgentServer.custom_action("material_fight")
class MaterialFight(CustomAction):
    """装备材料速战自定义动作类。

    以 eat_sugar.run_candy_fight 发起速战，候选里带入券不足 / 饥饿提示 / 补糖分支。

    Note:
        只有走到速战的正常收尾节点（跳过动画 / 确认奖励 / 等级提升）才算刷取成功，其余情况返回 False，
        交给流水线的 on_error 收尾，避免无条件回跳造成死循环。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行装备材料速战。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需额外参数）

        Returns:
            bool：是否正常打完并领取了战斗奖励
        """
        try:
            detail = run_candy_fight(context)
            if detail is None:
                Prompter.log("预留体力不足，跳过本次刷取")
                return False

            if not fight_finished(detail):
                last_node = Tasker.get_last_node_name(detail)
                if last_node not in FIGHT_LOGGED_EXITS:
                    Prompter.log(f"速战未正常结束，最后节点 {last_node}，跳过本次刷取")
                return False
            return True
        except Exception as e:
            return Prompter.error("装备材料速战", e)


@AgentServer.custom_action("find_material_stage")
class FindMaterialStage(CustomAction):
    """装备材料三星关卡定位自定义动作类。

    在「获取详情」的关卡列表里找最右侧的三星关卡并点「前往」。
    卡槽数量随关卡数变化，因此先把列表归一到最新关卡端，再按「前往」按钮位置
    动态推导每张卡的星条 ROI，从右到左挑第一个满足星数的关卡；
    本屏没有就向更早关卡翻一屏，两次截图基本一致说明已到头，此时返回 False。

    参数格式（custom_action_param）：
        - star 或 n：判定所需的星数，默认 3
        - max 或 m：最大滑动次数，默认 6
    """

    # 「前往」按钮识别节点：卡槽数量随关卡数变化，位置一律由按钮中心推导
    GOTO_NODE = "装备材料_识别前往"
    # 关卡列表区域，同时也是判断「是否到头」的截图比较区域
    LIST_ROI = (233, 357, 816, 283)
    # 由「前往」按钮中心 x 推导该卡星条 ROI 的偏移量（1280x720 基准）
    STAR_OFFSET_X = -33
    STAR_TOP = 519
    STAR_WIDTH = 67
    STAR_HEIGHT = 16
    # 归一到最新关卡端 / 向更早关卡翻屏的滑动起止点与耗时
    SWIPE_LATEST = (1000, 373, 267, 373)
    SWIPE_EARLIER = (333, 373, 1000, 373)
    SWIPE_MS = 800
    NORMALIZE_MAX = 3
    # 「前往」识别失败时的固定 4 卡槽兜底
    STAR_ROIS = ((354, 520, 70, 21), (539, 520, 70, 21), (724, 520, 70, 21), (909, 520, 70, 21))
    GOTO_POINTS = ((387, 597), (572, 597), (757, 597), (942, 597))
    # 判断「是否到头」的平均像素差阈值与坐标基准宽度
    SAME_DIFF = 1.0
    BASE_WIDTH = 1280

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行三星关卡定位与「前往」点击。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数，支持星数阈值与最大滑动次数

        Returns:
            bool：找到并点击了「前往」返回 True，否则返回 False
        """
        try:
            args = ParamAnalyzer(argv)
            need = args.get(["star", "n"], 3)
            limit = args.get(["max", "m"], 6)
            if not isinstance(need, int) or need <= 0:
                need = 3
            if not isinstance(limit, int) or limit <= 0:
                limit = 6

            tasker = Tasker(context)
            shot = self._to_latest(tasker)
            for moved in range(limit + 1):
                spot = self._pick(context, shot, need)
                if spot:
                    Prompter.log(f"点击前往 {spot}")
                    tasker.click(*spot)
                    return True
                if moved == limit:
                    break
                tasker.swipe(*self.SWIPE_EARLIER, duration=self.SWIPE_MS).wait(1)
                current = tasker.screenshot()
                if self._same(shot, current):
                    Prompter.log("关卡列表已到头，没有满足星级的关卡")
                    return False
                shot = current

            Prompter.log(f"已滑动 {limit} 次仍未找到满足星级的关卡")
            return False
        except Exception as e:
            return Prompter.error("选择三星关卡", e)

    def _to_latest(self, tasker: Tasker) -> np.ndarray:
        """把关卡列表归一到最新关卡端，保证扫描起点固定。

        Args:
            tasker：任务执行器

        Returns:
            np.ndarray：归一后的截图
        """
        shot = tasker.screenshot()
        for _ in range(self.NORMALIZE_MAX):
            tasker.swipe(*self.SWIPE_LATEST, duration=self.SWIPE_MS).wait(1)
            current = tasker.screenshot()
            if self._same(shot, current):
                return current
            shot = current
        return shot

    def _pick(self, context: Context, shot: np.ndarray, need: int) -> tuple[int, int] | None:
        """按「前往」按钮动态定位卡槽，取最右侧满足星数的按钮中心。

        Args:
            context：MaaFW 上下文对象
            shot：当前截图
            need：所需星数

        Returns:
            tuple | None：需要点击的按钮中心，没有满足条件的关卡时返回 None
        """
        rh = RecoHelper(context)
        rh.screencap = shot
        centers = self._goto_centers(rh)
        scale = self._scale(shot)
        if centers:
            for center in sorted(centers, key=lambda c: c[0], reverse=True):
                stars = self._count_stars(shot, self._star_roi(center[0], scale), scale)
                Prompter.log("让我看看…")
                if stars >= need:
                    return center
            return None

        stars = self._stars(shot)
        Prompter.log(f"当前星级 {stars}")
        slot = self._rightmost(stars, need)
        return self.GOTO_POINTS[slot] if slot >= 0 else None

    def _goto_centers(self, rh: RecoHelper) -> list[tuple[int, int]]:
        """识别关卡列表里所有「前往」按钮的中心。

        Args:
            rh：识别辅助器，使用其缓存截图

        Returns:
            list：按钮中心坐标，未识别到时为空列表
        """
        rh.recognize(self.GOTO_NODE)
        if not rh.hit:
            return []
        return [RecoHelper.get_res_center(res) for res in rh.filtered_results]

    def _star_roi(self, center_x: int, scale: float) -> tuple[int, int, int, int]:
        """由「前往」按钮中心 x 推导该卡的星条 ROI。

        Args:
            center_x：按钮中心 x（截图坐标）
            scale：截图宽度与 1280 的比例

        Returns:
            tuple：星条 ROI，基于 1280x720 的 (x, y, w, h)
        """
        x = round(center_x / scale) + self.STAR_OFFSET_X
        return (x, self.STAR_TOP, self.STAR_WIDTH, self.STAR_HEIGHT)

    def _scale(self, img: np.ndarray) -> float:
        """计算截图宽度与 1280 的比例。

        Args:
            img：当前截图

        Returns:
            float：缩放比例
        """
        return img.shape[1] / self.BASE_WIDTH

    def _stars(self, img: np.ndarray) -> list[int]:
        """统计 4 个卡槽各自的星数。

        Args:
            img：当前截图

        Returns:
            list：按卡槽从左到右排列的星数
        """
        scale = img.shape[1] / self.BASE_WIDTH
        return [self._count_stars(img, roi, scale) for roi in self.STAR_ROIS]

    @staticmethod
    def _count_stars(img: np.ndarray, roi: tuple[int, int, int, int], scale: float = 1.0) -> int:
        """统计单个卡槽三星行内的星数。

        金色判据不依赖通道顺序（按每像素的通道大小关系比较），
        以合格列上金色像素数的游程数作为星数。

        Args:
            img：当前截图
            roi：三星行区域，基于 1280x720 的 (x, y, w, h)
            scale：截图宽度与 1280 的比例

        Returns:
            int：星数
        """
        x, y, w, h = roi
        x0, y0 = round(x * scale), round(y * scale)
        x1, y1 = round((x + w) * scale), round((y + h) * scale)
        strip = np.asarray(img[y0:y1, x0:x1], dtype=np.int16)
        if strip.size < 3:
            return 0
        channels = np.sort(strip[:, :, :3], axis=2)
        low, mid, high = channels[:, :, 0], channels[:, :, 1], channels[:, :, 2]
        gold = (high > 150) & (mid > 110) & (mid < 235) & (low < 140) & (high - low > 60)
        per_col = gold.sum(axis=0)
        peak = int(per_col.max())
        if peak <= 0:
            return 0
        runs = 0
        prev = False
        for hit in per_col > max(1.0, peak * 0.25):
            if hit and not prev:
                runs += 1
            prev = bool(hit)
        return runs

    @staticmethod
    def _rightmost(stars: list[int], need: int) -> int:
        """取最右侧满足星数要求的卡槽下标。

        Args:
            stars：各卡槽星数
            need：所需星数

        Returns:
            int：卡槽下标，没有满足的卡槽时返回 -1
        """
        for i in range(len(stars) - 1, -1, -1):
            if stars[i] >= need:
                return i
        return -1

    def _same(self, before: np.ndarray, after: np.ndarray) -> bool:
        """判断两次截图是否基本一致，用于确认关卡列表是否到底。

        Args:
            before：滑动前的截图
            after：滑动后的截图

        Returns:
            bool：两次截图一致返回 True
        """
        if before.shape != after.shape:
            return False
        scale = after.shape[1] / self.BASE_WIDTH
        x, y, w, h = self.LIST_ROI
        x0, y0 = round(x * scale), round(y * scale)
        x1, y1 = round((x + w) * scale), round((y + h) * scale)
        region = (slice(y0, y1), slice(x0, x1))
        diff = np.abs(before[region].astype(np.int16) - after[region].astype(np.int16))
        return float(diff.mean()) < self.SAME_DIFF


@AgentServer.custom_action("equip_pass_gate")
class EquipPassGate(CustomAction):
    """装备材料刷取轮次闸门。

    「两遍装备」的链路里第二遍由购买红糖触发，而每日检查只应判定一次：
    第一遍放行并走每日检查，同一轮的第二遍直接跳过每日检查放行。

    Note:
        计数键 equip_pass 由「清红糖_复位装备轮次」在每个任务轮次开始时重置。
    """

    COUNTER_KEY = "equip_pass"

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """判断是否跳过每日检查。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需额外参数）

        Returns:
            bool：返回 True 走每日检查，False 跳过（由 on_error 直接进入刷取）
        """
        try:
            counter = CounterManager.get(self.COUNTER_KEY, 0, 0)
            attempt = counter.count()
            if attempt > 1:
                Prompter.log(f"第 {attempt} 遍装备刷取，跳过每日检查")
                return False
            return True
        except Exception as e:
            return Prompter.error("装备刷取轮次检查", e)
