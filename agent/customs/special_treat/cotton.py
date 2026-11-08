"""糖果自由（棉花糖）自动刷取相关自定义动作模块。

自动模式按三种优质棉花糖的持有数量，选择「两两之和最小」的组合关卡，
并把关卡定位到最新的三星关（列表滑到最底后，从右下往左上找第一个三星）。

Note:
    - 数量来源是关卡列表右侧「奖励列表」：逐个点开图标读名称与所持数量，再点一次关闭；
      列表里会混排中级棉花糖等档位，只统计名称带「优质」的那些；
    - 一关只会出现该关的两种棉花糖，因此要进两关才能凑齐三种；
    - 金星与罐内浅黄糖同色，只能先按星条底色定位每一格，再在条内按三等分逐格数金星。
"""

import os
import time

import numpy as np
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

from .eat_sugar import fight_finished
from agent.customs.maahelper import RecoHelper, Tasker
from agent.customs.maahelper.zh_hant import fold
from agent.customs.utils import Prompter

# 奖励列表里还有中级等其它档位，只有优质棉花糖才参与统计
CANDY_KEYWORD = "优质"

# 三种优质棉花糖的名称关键字，以及 OCR 常见误读的容错写法
COTTON_NAMES = ("防御", "输出", "辅助")
COTTON_ALIASES = {
    "方御": "防御",
    "防卸": "防御",
    "俞出": "输出",
    "输山": "输出",
    "辅肋": "辅助",
}

# 三个机器的入口坐标与产物组合（1280×720 基准）
# 红：不能选择防御职能 → 产物 辅助 + 输出
# 蓝：不能选择输出职能 → 产物 防御 + 辅助
# 绿：不能选择辅助职能 → 产物 防御 + 输出
MACHINES = {
    "输出/辅助": {"point": (223, 347), "candies": ("输出", "辅助")},
    "防御/辅助": {"point": (640, 347), "candies": ("防御", "辅助")},
    "防御/输出": {"point": (1053, 347), "candies": ("防御", "输出")},
}
# 取数只需进两个机器即可覆盖三种糖：蓝（防御+辅助）与绿（防御+输出）
COUNT_MACHINES = ("防御/辅助", "防御/输出")
# 机器在界面上按「不能选哪个职能」区分，日志里用它更直观
MACHINE_LABELS = {"输出/辅助": "无防御", "防御/辅助": "无输出", "防御/输出": "无辅助"}

# 糖果自由的速战没有体力/入场券分支：紫糖不足且今日恢复次数已满时，点「速战」只会弹
# 「今天已经无法继续恢复星星糖了」，不认这一条就会反复点速战直到超时。
COTTON_FIGHT_OVERRIDE = {
    "速战_打开速战面板": {
        "next": ["速战_确保可战斗", "清紫糖_星星糖不足", "速战_无法速战", "速战_体力不足"]
    }
}

# 关卡列表右侧奖励图标（1280 基准）；最右侧一个会被裁切，不取
ICON_POS = ((813, 343), (913, 343), (1013, 343), (1107, 343))
NAME_NODE = "糖果自由_识别奖励名称"
COUNT_NODE = "糖果自由_识别奖励数量"

# 关卡网格（1280 基准）：滑到底后可见三行三列，格子的位置随滚动变化，所以不写死坐标，
# 而是用每一格星条底色 (199,147,72) 找到星条，再按三等分逐格数金星。
# 金星 (255,183,31) 与罐内浅黄糖同色，只能框在星条内部数；实测一颗金星约占 620 像素，
# 空格子为 0 像素，两者差距足够大。
BAR_COLOR = (199, 147, 72)
BAR_TOLERANCE = 12
BAR_PANE_RIGHT = 730
BAR_ROW_GAP = 30
BAR_CELL_GAP = 60
BAR_MIN_ROW_PIXELS = 100
BAR_MIN_COLUMN_PIXELS = 3
BAR_WIDTH = (100, 220)
BAR_INSET = 6
BAR_STAR_PIXELS = 150

# 返回糖果自由页的返回键、滑动到底的起止点与最大次数
BACK_POINT = (43, 37)
# 读不到数量时转储现场（相对项目根，已被 .gitignore 的 debug/ 覆盖）
COTTON_DUMP_DIR = os.path.join("debug", "cotton")
SCROLL_FROM = (360, 560)
SCROLL_TO = (360, 220)
SCROLL_MAX = 8

# 关卡编号：滑到底时 07-12 应该全部可见，所以看到这六个编号就不再滑；
# 优质棉花糖只从第七关以后产出，三星关低于第七关时直接退出，不白跑一趟速战。
STAGE_NODE = "糖果自由_识别关卡编号"
STAGE_PANEL_NODE = "糖果自由_识别选中关卡"
# 机器选择页上每台机器的「N阶段」文字：这就是该机器当前的最新关
# （面板上的号码徽章字太小、深蓝压蓝底，OCR 不稳，优先用这里的阶段数）
# 复用既有的「识别关卡编号」节点（OCR 数字），只是把 roi 覆盖到阶段文字上，避免新增节点。
STAGE_TEXT_NODE = STAGE_NODE
MACHINE_STAGE_ROIS = {
    "输出/辅助": [230, 420, 150, 60],
    "防御/辅助": [600, 420, 170, 60],
    "防御/输出": [970, 420, 170, 60],
}
STAGE_BOTTOM = (7, 8, 9, 10, 11, 12)
STAGE_MIN = 8
STAGE_NEAR = 90
# 右侧面板顶部三颗大星星（比网格小金星大得多，更好认）
PANEL_STAR_ROI = (950, 110, 150, 70)
PANEL_STAR_WIDTH = (25, 45)
PANEL_STAR_PIXELS = (300, 650)
PANEL_STAR_GAP = 5


def dump_failure(shot) -> str:
    """把读数量失败时的画面转储成 npy，便于事后复现。

    Args:
        shot：当前截图（numpy）

    Returns:
        str：转储路径，失败时为空串
    """
    path = ""
    if shot is not None:
        try:
            os.makedirs(COTTON_DUMP_DIR, exist_ok=True)
            path = os.path.join(COTTON_DUMP_DIR, f"fail_{int(time.time() * 1000)}.npy")
            np.save(path, shot)
        except Exception as error:
            Prompter.log(f"保存糖果自由截图失败，{error}")
            path = ""
    return path


def read_stages(context: Context) -> list[tuple[int, int, int]]:
    """读关卡网格里的关卡编号及其中心点。

    Returns:
        list：[(关卡号, 中心 x, 中心 y), ...]，读不到时为空列表
    """
    rh = RecoHelper(context).refresh_screencap()
    rh.recognize(STAGE_NODE)
    marks = []
    if not rh.hit:
        return marks
    for result in rh.filtered_results:
        text = (result.text or "").strip()
        if not text.isdigit():
            continue
        box = result.box
        marks.append((int(text), box[0] + box[2] // 2, box[1] + box[3] // 2))
    return marks


def record_stages(text: str) -> None:
    """把各机器的最新关写进 debug 日志，不占用 focus（界面日志）。

    Args:
        text：形如「无防御 4 阶段 / 无输出 3 阶段」的说明文字
    """
    try:
        os.makedirs(COTTON_DUMP_DIR, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(COTTON_DUMP_DIR, "stages.log"), "a", encoding="utf-8") as file:
            file.write(f"[{stamp}] {text}\n")
    except Exception:
        pass


def read_machine_stages(context: Context) -> dict[str, int]:
    """在机器选择页读每台机器的「N阶段」，即该机器当前的最新关。

    Args:
        context：MaaFW 上下文对象

    Returns:
        dict：{组合名: 阶段数}，读不到的机器为 0
    """
    rh = RecoHelper(context).refresh_screencap()
    stages: dict[str, int] = {}
    for key, roi in MACHINE_STAGE_ROIS.items():
        rh.recognize(STAGE_TEXT_NODE, {"roi": roi})
        digits = "".join(ch for ch in (rh.concat() or "") if ch.isdigit())
        stages[key] = int(digits) if digits else 0
    return stages


def read_selected_stage(context: Context) -> int:
    """读右侧面板里选中关卡的编号（选中后那块号码牌最准，不受网格 OCR 漏读影响）。

    Returns:
        int：关卡号，读不到时返回 0
    """
    # 进机器后面板是渐进渲染的，号码牌可能晚一拍才出现，读不到就再抓两帧
    for _ in range(3):
        rh = RecoHelper(context).refresh_screencap()
        rh.recognize(STAGE_PANEL_NODE)
        if rh.hit:
            for result in rh.filtered_results:
                text = (result.text or "").strip()
                if text.isdigit():
                    return int(text)
        time.sleep(0.5)
    return 0


def stage_from_grid(stages: list[tuple[int, int, int]], cell: tuple[int, int]) -> int:
    """用关卡号码牌与格子的位置关系推断某个三星格属于第几关。

    号码牌在罐子正上方，所以取「横向对齐、纵向在上方 STAGE_NEAR 以内」里最近的那个。

    Args:
        stages：read_stages 的结果，元素为 (关卡号, 中心 x, 中心 y)
        cell：三星格中心点 (x, y)

    Returns:
        int：推断出的关卡号，推断不出时返回 0
    """
    x, y = cell
    number, best_gap = 0, None
    for value, center_x, center_y in stages:
        if abs(center_x - x) > 45:
            continue
        gap = y - center_y
        if gap < 0 or gap > STAGE_NEAR:
            continue
        if best_gap is None or gap < best_gap:
            number, best_gap = value, gap
    return number


def pick_latest_three_star(grid: list[tuple[int, int, int]]) -> tuple[int, int] | None:
    """按「右下 → 往左 → 上一行」的顺序找最新的三星关。

    新版关卡在最下面一行最右侧，所以先看右下角，再向左、再向上逐格找，
    第一个三星格就是最新的三星关。

    Args:
        grid：read_grid 的结果，元素为 (中心 x, 中心 y, 金星数)

    Returns:
        tuple | None：(x, y)，没有三星关时为 None
    """
    for x, y, stars in sorted(grid, key=lambda cell: (-cell[1], -cell[0])):
        if stars >= 3:
            return x, y
    return None


def match_candy(name: str) -> str:
    """从奖励名称里认出是哪种棉花糖。

    容忍 OCR 把「防御」读成「方御」这类误读。

    Args:
        name：OCR 读到的名称文本

    Returns:
        str：棉花糖类型，认不出时返回空串
    """
    name = fold(name)
    for candy in COTTON_NAMES:
        if candy in name:
            return candy
    for wrong, right in COTTON_ALIASES.items():
        if wrong in name:
            return right
    return ""


def read_reward(context: Context, point: tuple[int, int]) -> tuple[str, int]:
    """点开一个奖励图标读名称与所持数量，读完再点一次关掉面板。

    奖励列表里除了棉花糖还会有晶体、绷带这类东西，点它们不弹名称面板，
    这时识别不到任何文本，所以两种 OCR 结果都要按「可能为空」处理；
    面板没弹出来时也不能再补一次点击，否则会把下一个图标的面板点开。

    Args:
        context：MaaFW 上下文对象
        point：奖励图标坐标（1280 基准）

    Returns:
        tuple：名称与数量；不是棉花糖或没弹面板时数量为 -1
    """
    tasker = Tasker(context)
    tasker.click(*point).wait()
    rh = RecoHelper(context)
    opened = False
    for _ in range(3):  # 面板有弹出动画，识别不到就再抓一帧重试
        rh.refresh_screencap().recognize(NAME_NODE)
        if rh.hit:
            opened = True
            break
        tasker.wait(0.4)
    name = rh.concat() or ""
    value = -1
    if opened and CANDY_KEYWORD in fold(name) and match_candy(name):
        rh.recognize(COUNT_NODE)
        digits = "".join(ch for ch in (rh.concat() or "") if ch.isdigit())
        value = int(digits) if digits else -1
    if opened:
        tasker.click(*point).wait()  # 再点一次同一个图标即关闭面板
        tasker.wait(0.3)
    return name, value


def choose_combo(counts: dict[str, int]) -> str:
    """选出要刷的组合：持有最多的那种不用补，刷另外两种。

    Args:
        counts：三种棉花糖的持有数量

    Returns:
        str：组合名，取值属于 MACHINES；数量不全时返回空串
    """
    if any(candy not in counts for candy in COTTON_NAMES):
        return ""
    most = max(COTTON_NAMES, key=lambda candy: counts[candy])
    for combo, info in MACHINES.items():
        if most not in info["candies"]:
            return combo
    return ""


def group_runs(indexes: np.ndarray, gap: int) -> list[tuple[int, int]]:
    """把一维下标按「相邻间隔不超过 gap」合并成若干连续区间。

    Args:
        indexes：升序下标
        gap：允许的最大间隔

    Returns:
        list：[(起点, 终点), ...]
    """
    runs: list[tuple[int, int]] = []
    start = previous = int(indexes[0])
    for value in indexes[1:]:
        value = int(value)
        if value - previous > gap:
            runs.append((start, previous))
            start = value
        previous = value
    runs.append((start, previous))
    return runs


def read_grid(shot: np.ndarray) -> list[tuple[int, int, int]]:
    """读出关卡网格里每一格的星条位置与金星数量。

    星条底色是固定的，用它把格子找出来，就不受列表滚动位置影响；金星只在星条内部数，
    避开同色的罐内浅黄糖。截图是 BGR 还是 RGB 都一样，比较时只用到通道的最大/中间/最小值。

    Args:
        shot：当前截图

    Returns:
        list：[(格子中心 x, 星条顶边 y, 金星数), ...]，1280 基准
    """
    scale = shot.shape[1] / 1280
    pane = shot[:, : round(BAR_PANE_RIGHT * scale)].astype(np.int16)
    top, bottom = pane.max(axis=2), pane.min(axis=2)
    middle = pane.sum(axis=2) - top - bottom
    bar = (
        (np.abs(top - BAR_COLOR[0]) <= BAR_TOLERANCE)
        & (np.abs(middle - BAR_COLOR[1]) <= BAR_TOLERANCE)
        & (np.abs(bottom - BAR_COLOR[2]) <= BAR_TOLERANCE)
    )
    gold = (top >= 235) & (middle - bottom >= 60) & (bottom <= 160)
    cells: list[tuple[int, int, int]] = []
    rows = np.where(bar.sum(axis=1) >= BAR_MIN_ROW_PIXELS * scale)[0]
    if rows.size == 0:
        return cells
    for row_start, row_end in group_runs(rows, round(BAR_ROW_GAP * scale)):
        columns = np.where(bar[row_start : row_end + 1].sum(axis=0) >= BAR_MIN_COLUMN_PIXELS * scale)[0]
        if columns.size == 0:
            continue
        for left, right in group_runs(columns, round(BAR_CELL_GAP * scale)):
            width = right - left + 1
            if not BAR_WIDTH[0] * scale <= width <= BAR_WIDTH[1] * scale:
                continue
            inset = round(BAR_INSET * scale)
            x0, x1 = left + inset, right - inset
            y0, y1 = row_start + inset, row_end - inset
            slot = (x1 - x0 + 1) / 3
            stars = 0
            for index in range(3):
                slot_start = x0 + round(index * slot)
                slot_end = x0 + round((index + 1) * slot) - 1
                if gold[y0 : y1 + 1, slot_start : slot_end + 1].sum() >= BAR_STAR_PIXELS * scale * scale:
                    stars += 1
            cells.append((round((left + right) / 2 / scale), round(row_start / scale), stars))
    return cells


def panel_star_count(shot: np.ndarray) -> int:
    """数关卡详情面板右上那排大星星。

    选中的关卡会在右侧面板顶部用三颗大星星标出星级，比网格里的小金星大得多、也更好数。

    Args:
        shot：当前截图

    Returns:
        int：认出的星星数量，面板不在或不像星星时返回 0
    """
    scale = shot.shape[1] / 1280
    x, y, width, height = [round(value * scale) for value in PANEL_STAR_ROI]
    pane = shot[y : y + height, x : x + width].astype(np.int16)
    top, bottom = pane.max(axis=2), pane.min(axis=2)
    middle = pane.sum(axis=2) - top - bottom
    gold = (top >= 235) & (middle - bottom >= 60) & (bottom <= 160)

    columns = np.where(gold.sum(axis=0) >= 2 * scale)[0]
    if columns.size == 0:
        return 0
    count = 0
    for left, right in group_runs(columns, round(PANEL_STAR_GAP * scale)):
        star_width = (right - left + 1) / scale
        pixels = gold[:, left : right + 1].sum() / (scale * scale)
        if (
            PANEL_STAR_WIDTH[0] <= star_width <= PANEL_STAR_WIDTH[1]
            and PANEL_STAR_PIXELS[0] <= pixels <= PANEL_STAR_PIXELS[1]
        ):
            count += 1
    return count


def select_latest_three_star(context: Context, machine: str = "") -> bool:
    """在**当前机器**里定位最新的三星关，并确认它是第 8 关或更后面。

    三台机器的关卡进度是各自独立的（例如 4 / 3 / 2 阶段），所以必须在真正要打的那台
    机器里判断，不能用别的机器上读到的结果。

    判定顺序：先星级、后关卡号。
    1. 滑到底 → 网格按「右下 → 往左 → 上一行」找最新三星格；找不到直接结束本轮；
    2. 点开该格 → 用右侧面板顶部的大星星复核（不一致只提示，非三星关的速战按钮本来就是灰的）；
    3. 读关卡号：面板号码牌 → 号码牌与格子的几何关系推断；读不到时提示后继续，
       读到但小于 STAGE_MIN 才结束本轮。

    Args:
        context：MaaFW 上下文对象

    Returns:
        bool：定位成功且关卡合适返回 True
    """
    tasker = Tasker(context)
    stages: list[tuple[int, int, int]] = []
    last = None
    for _ in range(SCROLL_MAX):
        stages = read_stages(context)
        numbers = {number for number, _, _ in stages}
        if all(number in numbers for number in STAGE_BOTTOM) or numbers == last:
            break
        last = numbers
        tasker.swipe(*SCROLL_FROM, *SCROLL_TO).wait()
        tasker.wait(0.4)

    tasker.wait(0.3)
    Prompter.log("让我看看")
    chosen = pick_latest_three_star(read_grid(tasker.screenshot()))
    if chosen is None:
        Prompter.log("没有识别到7关后三星，再练练喵")
        return False

    x, y = chosen
    tasker.click(x, y - 20).wait()  # 星条上方就是罐子本体
    tasker.wait(0.8)

    stars = panel_star_count(tasker.screenshot())
    if stars and stars < 3:
        # 网格与面板不一致时按正常流程继续：非三星关的「速战」按钮是灰的，本来就打不了
        Prompter.log(f"网格和面板星数识别不一致（面板 {stars} 星），按正常流程继续")

    stage = read_selected_stage(context) or stage_from_grid(stages, chosen)
    if not stage:
        Prompter.log("未能读取关卡编号，按最新三星关继续")
        return True
    if stage < STAGE_MIN:
        Prompter.log(
            f"识别到{MACHINE_LABELS.get(machine, machine)}最新三星关是第 {stage} 关"
            "没有优质棉花糖，再练练喵"
        )
        return False
    Prompter.log(f"选择第 {stage} 关")
    return True


@AgentServer.custom_action("cotton_auto")
class CottonAuto(CustomAction):
    """糖果自由自动刷取：读数量 → 选组合 → 选最新三星关 → 速战。"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行自动刷取。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需参数）

        Returns:
            bool：是否完成一次速战
        """
        try:
            tasker = Tasker(context)
            counts: dict[str, int] = {}

            # 先读每台机器的最新关，再开始读棉花糖数量
            machine_stages = read_machine_stages(context)
            stage_text = " / ".join(
                f"{MACHINE_LABELS.get(key, key)} {value} 阶段"
                for key, value in machine_stages.items()
                if value
            )
            # 只做后台记录，不占 focus
            record_stages(stage_text or "未读到")

            latest_stage = 0
            for key in COUNT_MACHINES:
                tasker.click(*MACHINES[key]["point"]).wait()
                tasker.wait(1.2)
                # 顺带看一眼这台机器当前选中的最新关（只用于数量读不全时的提示，不做拦截）
                latest_stage = (
                    machine_stages.get(key, 0) or read_selected_stage(context) or latest_stage
                )
                found: list[tuple[str, int]] = []
                for point in ICON_POS:
                    name, value = read_reward(context, point)
                    if value >= 0:
                        found.append((name, value))
                    if len(found) >= 2:
                        break
                # 名称识别不出的那种，用该机器已知的产物组合反推
                known = {match_candy(n): v for n, v in found if match_candy(n)}
                unknown = [v for n, v in found if not match_candy(n)]
                pair = MACHINES[key]["candies"]
                missing = [c for c in pair if c not in known]
                if len(unknown) == 1 and len(missing) == 1:
                    known[missing[0]] = unknown[0]
                for candy, value in known.items():
                    if candy in counts and counts[candy] != value:
                        Prompter.log(f"{candy} 两次读数不一致（{counts[candy]} / {value}），取较小值")
                    counts[candy] = min(value, counts.get(candy, value))
                if not found:
                    # 没读到优质棉花糖时静默转储现场，不打日志（这台机器本来就可能还没有优质棉花糖）
                    dump_failure(tasker.screenshot())
                tasker.click(*BACK_POINT).wait()
                tasker.wait(0.8)
                if len(counts) >= len(COTTON_NAMES):
                    break

            if len(counts) < len(COTTON_NAMES):
                if latest_stage and latest_stage < STAGE_MIN:
                    Prompter.log(
                        f"识别到{MACHINE_LABELS.get(key, key)}最新关是第 {latest_stage} 关"
                        "没有优质棉花糖，再练练喵"
                    )
                elif counts:
                    Prompter.log(
                        "棉花糖数量未读全，只读到 "
                        + " / ".join(f"{c} {counts[c]}" for c in COTTON_NAMES if c in counts)
                    )
                else:
                    dump_failure(tasker.screenshot())
                    Prompter.log("棉花糖数量都未成功读取")
                return False

            Prompter.log("棉花糖数量 " + " / ".join(f"{c} {counts[c]}" for c in COTTON_NAMES))
            combo = choose_combo(counts)
            Prompter.log(f"选择组合 {combo}")

            # 进组合机器后，在这台机器里定位最新三星关并校验关卡
            tasker.click(*MACHINES[combo]["point"]).wait()
            tasker.wait(1.2)
            if not select_latest_three_star(context, combo):
                return False

            detail = tasker.run(
                "速战",
                {"速战": {"custom_recognition_param": "e=速战_确认奖励"}, **COTTON_FIGHT_OVERRIDE},
            )
            if not fight_finished(detail):
                last_node = Tasker.get_last_node_name(detail)
                if last_node == "清紫糖_星星糖不足":
                    Prompter.log("紫糖不足，跳过本次自动刷取")
                else:
                    Prompter.log(f"速战没打成，最后节点 {last_node}，跳过本次自动刷取")
                return False
            return True
        except Exception as error:
            return Prompter.error("糖果自由自动刷取", error)
