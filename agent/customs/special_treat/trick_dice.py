"""诡计骰子：识别免费入场、当前回合和可登记的预览分数。

页面跳转由 Pipeline 控制。识别稳定手牌后，用整局动态规划比较
登记、保留、重掷和整局一次的全绿骰技能；逐次核对游戏预览。
"""

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

from agent.customs.maahelper import RecoHelper, Tasker
from agent.customs.utils import Prompter

from .trick_dice_strategy import ALL_CATEGORIES, LABELS, DiceDecision, DiceSolver, score_hand
from .trick_dice_vision import SeenDie, hand_counts, read_dice, toggle_target

ROWS = (
    ("二点", 161),
    ("三点", 213),
    ("四点", 264),
    ("五点", 315),
    ("六点", 367),
    ("葫芦", 472),
    ("大顺", 521),
    ("快艇", 573),
)


@dataclass
class _SheetState:
    mask: int | None = None
    upper: int = 0
    pending: tuple[int, int] | None = None
    plan_key: tuple[Any, ...] = ()
    plan: DiceDecision | None = None
    last_error: str = ""
    needs_clear: bool = False
    view_key: tuple[Any, ...] = ()
    last_cleared_key: tuple[Any, ...] = ()
    skill_available: bool | None = None
    skill_pending: bool = False
    skill_attempt_round: int = 0


_states: dict[int, _SheetState] = {}
_solver: DiceSolver | None = None


def _get_solver() -> DiceSolver:
    global _solver
    if _solver is None:
        _solver = DiceSolver()
    return _solver


def _state(task_id: int) -> _SheetState:
    return _states.setdefault(task_id, _SheetState())


def _reject(state: _SheetState, reason: str) -> CustomRecognition.AnalyzeResult:
    # 临时识别失败由后续帧重试，不在正常对局日志中刷屏。
    state.last_error = reason
    return RecoHelper.NoResult


def _recognize(context: Context, image: np.ndarray, node: str, override: dict[str, Any] | None = None) -> RecoHelper:
    helper = RecoHelper(context)
    helper.screencap = image
    return helper.recognize(node, override or {})


def _board(context: Context, image: np.ndarray) -> bool:
    return image.shape[:2] == (720, 1280) and _recognize(context, image, "诡计骰子_回合标记").hit


def _own_turn(image: np.ndarray) -> bool:
    # 实机 720p：自己的场地为橙色，对手为绿色。区域避开骰盘、头像及倒计时。
    b, g, r = image[20:70, 580:700, :3].mean(axis=(0, 1))
    return r > g * 1.2 and g > b * 1.2


def _number(context: Context, mask: np.ndarray) -> int | None:
    """将低对比度预览数字转成黑字白底，only_rec 避免漏检单个数字。"""
    ys, xs = np.nonzero(mask)
    if len(xs) < 12:
        return None
    glyph = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    # 投掷动画中计分项显示短横线，OCR 可能将其读成 1；不能登记动画占位符。
    if glyph.shape[0] < 12 or glyph.shape[1] < 6:
        return None
    canvas = np.full((glyph.shape[0] + 12, glyph.shape[1] + 12, 3), 255, dtype=np.uint8)
    canvas[6:-6, 6:-6][glyph] = 0
    result = _recognize(
        context,
        canvas,
        "诡计骰子_数字",
        {
            "recognition": {"type": "OCR", "param": {"roi": [0, 0, canvas.shape[1], canvas.shape[0]]}},
        },
    )
    if not result.hit or result.best_result is None:
        return None
    text = result.best_result.text.strip()
    return int(text) if re.fullmatch(r"\d{1,2}", text) and int(text) <= 70 else None


def _score_box(mask: np.ndarray, y: int) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(mask)
    return (172 + int(xs.min()), y - 15 + int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def _has_score_tooltip(image: np.ndarray) -> bool:
    return bool(_tooltip_rows(image))


def _tooltip_rows(image: np.ndarray) -> set[str]:
    covered = set()
    for label, y in ROWS:
        cell = image[y - 15 : y + 16, 172:283, :3]
        white = (cell[..., 2] > 240) & (cell[..., 1] > 220) & (cell[..., 0] > 190)
        # 万能点数的绿色胶囊可能盖住气泡右半边；左侧仍有连续的白底。
        # 普通计分底色不满足白色条件，胶囊数字也不会出现在左侧区域。
        if white.mean() > 0.3 or white[:, :38].mean() > 0.4:
            covered.add(label)
    return covered


def _request_clear(state: _SheetState, image: np.ndarray) -> None:
    state.needs_clear = bool(state.view_key) and state.view_key != state.last_cleared_key and _has_score_tooltip(image)


def _scores(context: Context, image: np.ndarray) -> list[tuple[int, str, tuple[int, int, int, int]]]:
    candidates = []
    covered = _tooltip_rows(image)
    for label, y in ROWS:
        if label in covered:
            continue
        cell = image[y - 15 : y + 16, 172:283, :3].astype(np.int16)
        b, g, r = cell[..., 0], cell[..., 1], cell[..., 2]
        # 已登记的深红数字不是可选项；弹出的白色说明框也不能当作计分格。
        if ((r > 155) & (r < 210) & (g < 125) & (b < 85)).sum() > 25:
            continue
        gold = (r > 213) & (r < 241) & (g > 140) & (g < 180) & (b > 85) & (b < 125)
        value = _number(context, gold)
        target_mask = gold
        # 绿色埃尔芬预览胶囊右侧为可替换后的总分，避开左侧头像图标。
        if ((g > r * 1.1) & (g > b * 1.1)).sum() > 60:
            white = (r > 235) & (g > 235) & (b > 235)
            white[:, :73] = False
            wild_value = _number(context, white)
            if wild_value is not None and wild_value >= (value or 0):
                value = wild_value
                target_mask = white
        if value is not None:
            candidates.append((value, label, _score_box(target_mask, y)))
    return candidates


def _verified_scores(
    context: Context, image: np.ndarray, state: _SheetState, normal: tuple[int, ...], green: tuple[int, ...]
) -> list[tuple[int, str, tuple[int, int, int, int]]] | None:
    if state.mask is None:
        return None
    candidates = _scores(context, image)
    # 投掷和切换回合时预览会暂时全部隐藏，等待下一帧即可。
    if not candidates:
        return None
    expected = {label for category, label in enumerate(LABELS) if state.mask & (1 << category)}
    seen = {label for _, label, _ in candidates}
    # 说明气泡遮住相邻栏不影响骰面和其余预览。只允许明确被气泡遮住的栏缺失，
    # 不能把 OCR 漏字、动画或与模型不符的分数当成有效画面。
    if seen - expected or not (expected - seen) <= _tooltip_rows(image):
        _reject(state, "计分预览未就绪")
        return None
    model = score_hand(normal, green)
    for value, label, _ in candidates:
        category = LABELS.index(label)
        if value != model[category]:
            _reject(state, f"{label}预览{value}与骰面计算{model[category]}不一致")
            return None
    state.needs_clear = False
    return candidates


def _clear_target(context: Context, image: np.ndarray, state: _SheetState) -> tuple[int, int, int, int] | None:
    if state.pending is not None:
        return None
    candidates = _scores(context, image)
    if state.mask is not None:
        candidates = [candidate for candidate in candidates if state.mask & (1 << LABELS.index(candidate[1]))]
    if not candidates:
        return None
    if state.plan is not None and state.plan.category is not None:
        blocked_y = ROWS[state.plan.category][1]
    else:
        blocked_y = next((y for label, y in ROWS if label in _tooltip_rows(image)), ROWS[0][1])
    # 点击另一处已核实的预览，仅移动说明气泡；不点登记按钮，也不改变已填分。
    _, label, box = max(candidates, key=lambda candidate: abs(ROWS[LABELS.index(candidate[1])][1] - blocked_y))
    return box if abs(ROWS[LABELS.index(label)][1] - blocked_y) > 60 else None


def _load_sheet(context: Context, image: np.ndarray, state: _SheetState) -> bool:
    round_result = _recognize(context, image, "诡计骰子_轮次")
    if not round_result.hit or round_result.best_result is None:
        return False
    round_number = int(round_result.best_result.text[0])
    if round_number == 1:
        state.mask, state.upper = ALL_CATEGORIES, 0
        return True
    mask, upper, filled = 0, 0, 0
    covered = _tooltip_rows(image)
    for category, (label, y) in enumerate(ROWS):
        cell = image[y - 15 : y + 16, 172:283, :3].astype(np.int16)
        b, g, r = cell[..., 0], cell[..., 1], cell[..., 2]
        # 上次选分留下的说明气泡可能遮住相邻栏；不把气泡文字当成已填数字。
        # 只有其他已确认栏的数量等于 round-1 时，才可断言遮挡栏仍未填写。
        if label in covered:
            mask |= 1 << category
            continue
        red = (r > 155) & (r < 210) & (g < 125) & (b < 85)
        if red.sum() <= 25:
            mask |= 1 << category
            continue
        value = _number(context, red)
        if value is None:
            return False
        filled += 1
        if category < 5:
            upper += value
    if filled != round_number - 1:
        return False
    state.mask, state.upper = mask, min(55, upper)
    return True


def _skill_count(context: Context, image: np.ndarray) -> int | None:
    result = _recognize(context, image, "诡计骰子_技能次数")
    if result.hit and result.best_result is not None and result.best_result.text in ("0", "1"):
        return int(result.best_result.text)
    return None


def _skill_choice(context: Context, image: np.ndarray, state: _SheetState) -> bool:
    if state.skill_available is False:
        return False
    if state.mask is None and not _load_sheet(context, image, state):
        return False
    if not state.mask:
        return False
    round_result = _recognize(context, image, "诡计骰子_轮次")
    if not round_result.hit or round_result.best_result is None:
        return False
    round_number = int(round_result.best_result.text[0])
    if state.skill_attempt_round == round_number:
        return False
    count = _skill_count(context, image)
    if count is not None:
        state.skill_available = bool(count)
    if count != 1:
        return False
    return _get_solver().choose_skill(state.mask, state.upper).use


def _plan(
    context: Context, image: np.ndarray, remaining: int, state: _SheetState, dice: tuple[SeenDie, ...]
) -> DiceDecision | None:
    normal, green = hand_counts(dice)
    state.view_key = (normal, green, remaining)
    if state.mask is None and not _load_sheet(context, image, state):
        _request_clear(state, image)
        _reject(state, "无法确认已填计分栏")
        return None
    if not state.mask:
        return None
    if sum(green) == 5:
        state.skill_available = False
    elif state.skill_available is None:
        count = _skill_count(context, image)
        if count is not None:
            state.skill_available = bool(count)
    if state.skill_pending:
        Prompter.log("小聪明已生效" if sum(green) == 5 else "技能骰色未确认")
        state.skill_pending = False
    available = state.skill_available is True
    key = (normal, green, remaining, state.mask, state.upper, available)
    if key != state.plan_key:
        candidates = _verified_scores(context, image, state, normal, green)
        if candidates is None:
            return None
        solver = _get_solver()
        state.plan = solver.decide(normal, green, remaining, state.mask, state.upper, available)
        state.plan_key, state.last_error = key, ""
    return state.plan


@AgentServer.custom_action("trick_dice_init")
class TrickDiceInit(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            if len(_states) >= 8:
                _states.pop(next(iter(_states)))
            _states[argv.task_detail.task_id] = _SheetState()
            # 连续对局复用同一Tasker时，每局重新计算命中上限，保留单局保护。
            for name in (
                "免费入场",
                "选择计分",
                "登记组合",
                "确认计分",
                "投掷",
                "保留骰子",
                "使用小聪明",
                "收起说明",
                "等待对手",
                "结算下一步",
                "结算退出",
            ):
                if not context.clear_hit_count(f"诡计骰子_{name}"):
                    return False
            _get_solver()
            return True
        except Exception as error:
            Prompter.log(f"策略初始化失败：{type(error).__name__}")
            return False


@AgentServer.custom_action("trick_dice_skill")
class TrickDiceSkill(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        state = _state(argv.task_detail.task_id)
        tasker = Tasker(context)
        for attempt in range(3):
            if tasker.stopping:
                return False
            image = tasker.screenshot()
            if not _board(context, image) or not _own_turn(image):
                return True
            count = _skill_count(context, image)
            if count == 0:
                state.skill_available, state.skill_pending, state.plan_key = False, True, ()
                return True
            remaining = _recognize(context, image, "诡计骰子_投掷数字")
            if not remaining.hit or remaining.best_result is None or remaining.best_result.text != "3":
                return True
            if attempt == 0:
                if not _skill_choice(context, image, state):
                    return True
                round_result = _recognize(context, image, "诡计骰子_轮次")
                if not round_result.hit or round_result.best_result is None:
                    return True
                state.skill_attempt_round = int(round_result.best_result.text[0])
            # 最多点击两次；只有次数仍为1且尚未首掷时才允许补点。
            if count != 1 or attempt == 2:
                break
            button = _recognize(context, image, "诡计骰子_技能按钮")
            if not button.hit or button.best_result is None:
                break
            x, y = RecoHelper.get_res_center(button.best_result)
            tasker.click(x, y)
            tasker.wait(0.3)
        Prompter.log("小聪明未确认")
        return True


def _pending_score_matches(context: Context, image: np.ndarray, state: _SheetState) -> bool:
    if state.pending is None:
        return False
    category, points = state.pending
    helper = _recognize(
        context,
        image,
        "诡计骰子_已填分数",
        {"recognition": {"type": "OCR", "param": {"roi": [195, ROWS[category][1] - 16, 78, 34]}}},
    )
    return bool(helper.hit and helper.best_result is not None and helper.best_result.text == str(points))


def _commit_ready(context: Context, image: np.ndarray, state: _SheetState) -> bool:
    if state.pending is None or state.mask is None or not _board(context, image):
        return False
    if _own_turn(image):
        # 双方均已登记时可能直接进入下一回合，不一定能观察到绿色的对手回合。
        round_result = _recognize(context, image, "诡计骰子_轮次")
        if not round_result.hit or round_result.best_result is None:
            return False
        if int(round_result.best_result.text[0]) <= 9 - state.mask.bit_count():
            return False
    else:
        b, g, r = image[20:70, 580:700, :3].mean(axis=(0, 1))
        if not (g > r * 1.15 and g > b * 1.15):
            return False
    return _pending_score_matches(context, image, state)


@AgentServer.custom_recognition("trick_dice_commit_ready")
class TrickDiceCommitReady(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        state = _state(argv.task_detail.task_id)
        if not _commit_ready(context, argv.image, state) or state.pending is None:
            return RecoHelper.NoResult
        category, points = state.pending
        return RecoHelper.rt(text=f"{category}:{points}")


@AgentServer.custom_action("trick_dice_select")
class TrickDiceSelect(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            best = argv.reco_detail.raw_detail["best"]["detail"]["text"]
            label, points = best.rsplit(":", 1)
            category, score = LABELS.index(label), int(points)
            state = _state(argv.task_detail.task_id)
            if state.mask is None or not state.mask & (1 << category):
                return False
            tasker = Tasker(context)
            image = tasker.screenshot()
            if not _board(context, image):
                return False
            # 识别与动作之间可能已切换回合，登记入账后不再点击旧预览。
            if state.pending == (category, score) and _commit_ready(context, image, state):
                return True
            if not _own_turn(image):
                return False
            dice = read_dice(image)
            if dice is None:
                return False
            normal, green = hand_counts(dice)
            if state.plan is None or (normal, green) != state.plan_key[:2] or state.plan.category != category:
                Prompter.log("登记状态已变化，停止")
                return False
            # 登记后的第二次确认仅复核同一手牌、同一栏；说明气泡可能挡住相邻栏。
            candidates = (
                _scores(context, image)
                if state.pending == (category, score)
                else _verified_scores(context, image, state, normal, green)
            )
            if candidates is None:
                return False
            current = next((box for value, name, box in candidates if name == label and value == score), None)
            if current is None:
                return False
            x, y, w, h = current
            tasker.click(x + w // 2, y + h // 2)
            state.pending = (category, score)
            return True
        except Exception as error:
            Prompter.log(f"计分失败：{type(error).__name__}")
            return False


@AgentServer.custom_action("trick_dice_commit")
class TrickDiceCommit(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        state = _state(argv.task_detail.task_id)
        if state.pending is None or state.mask is None:
            return False
        category, points = state.pending
        tasker = Tasker(context)
        receipt = argv.reco_detail.raw_detail.get("best", {}).get("detail", {}).get("text")
        verified = receipt == f"{category}:{points}"
        for _ in range(8):
            if tasker.stopping:
                return False
            # 对手回合已填分数会由深红转成金色，因此直接读实际分格。
            # 识别阶段已核实的回执不再依赖下一帧，避免切场动画再次遮住分数。
            if verified or _pending_score_matches(context, tasker.screenshot(), state):
                state.mask &= ~(1 << category)
                if category < 5:
                    state.upper = min(55, state.upper + points)
                state.pending, state.plan_key, state.plan = None, (), None
                state.needs_clear, state.last_cleared_key = False, ()
                Prompter.log(f"登记{LABELS[category]}：{points}分")
                return True
            tasker.wait(0.2)
        Prompter.log("登记未确认，停止")
        return False


@AgentServer.custom_action("trick_dice_clear")
class TrickDiceClear(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        state = _state(argv.task_detail.task_id)
        if not state.needs_clear or not state.view_key or state.view_key == state.last_cleared_key:
            return True
        state.last_cleared_key, state.needs_clear = state.view_key, False
        tasker = Tasker(context)
        image = tasker.screenshot()
        if _board(context, image) and _own_turn(image) and _has_score_tooltip(image):
            target = _clear_target(context, image, state)
            if target is not None:
                x, y, w, h = target
                tasker.click(x + w // 2, y + h // 2)
        # 强制下一轮重新验证，禁止沿用一次清理前的缓存结论。
        state.plan_key = ()
        return True


@AgentServer.custom_recognition("trick_dice_entry")
class TrickDiceEntry(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        try:
            helper = _recognize(context, argv.image, "诡计骰子_入场次数")
            if not helper.hit or helper.best_result is None:
                return RecoHelper.NoResult
            match = re.search(r"(?:次数)?\s*(\d+)\s*/\s*(\d+)", helper.best_result.text)
            if not match or not 0 < int(match[1]) <= int(match[2]) <= 80:
                return RecoHelper.NoResult
            button = _recognize(context, argv.image, "诡计骰子_入场按钮")
            return (
                RecoHelper.rt(button.best_result)
                if button.hit and button.best_result is not None
                else RecoHelper.NoResult
            )
        except Exception as error:
            Prompter.log(f"入场识别异常：{type(error).__name__}")
            return RecoHelper.NoResult


@AgentServer.custom_recognition("trick_dice_opponent")
class TrickDiceOpponent(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        if not _board(context, argv.image):
            return RecoHelper.NoResult
        b, g, r = argv.image[20:70, 580:700, :3].mean(axis=(0, 1))
        return RecoHelper.rt() if g > r * 1.15 and g > b * 1.15 else RecoHelper.NoResult


@AgentServer.custom_recognition("trick_dice_move")
class TrickDiceMove(CustomRecognition):
    def analyze(self, context: Context, argv: CustomRecognition.AnalyzeArg) -> CustomRecognition.AnalyzeResult:
        try:
            image = argv.image
            if not _board(context, image) or not _own_turn(image):
                return RecoHelper.NoResult
            mode = argv.custom_recognition_param.strip('"')
            state = _state(argv.task_detail.task_id)
            if _commit_ready(context, image, state):
                return RecoHelper.NoResult
            if mode == "clear":
                if not state.needs_clear:
                    return RecoHelper.NoResult
                target = _clear_target(context, image, state) if _has_score_tooltip(image) else None
                return RecoHelper.rt(box=target) if target is not None else RecoHelper.NoResult
            roll = _recognize(context, image, "诡计骰子_投掷次数")
            if not roll.hit or roll.best_result is None:
                return RecoHelper.NoResult
            count = _recognize(context, image, "诡计骰子_投掷数字")
            if not count.hit or count.best_result is None:
                return RecoHelper.NoResult
            remaining = int(count.best_result.text)
            if mode == "skill":
                if remaining != 3 or not _skill_choice(context, image, state):
                    return RecoHelper.NoResult
                button = _recognize(context, image, "诡计骰子_技能按钮")
                return (
                    RecoHelper.rt(button.best_result)
                    if button.hit and button.best_result is not None
                    else RecoHelper.NoResult
                )
            if remaining == 3 and mode == "roll" and _skill_choice(context, image, state):
                button = _recognize(context, image, "诡计骰子_技能按钮")
                if button.hit and button.best_result is not None:
                    return RecoHelper.NoResult
            if remaining < 3:
                dice = read_dice(image)
                if dice is None:
                    return RecoHelper.NoResult
                plan = _plan(context, image, remaining, state, dice)
                if plan is None:
                    return RecoHelper.NoResult
                if plan.category is not None:
                    if mode != "score":
                        return RecoHelper.NoResult
                    normal, green = hand_counts(dice)
                    candidates = (
                        _scores(context, image)
                        if state.pending is not None
                        else _verified_scores(context, image, state, normal, green)
                    )
                    if candidates is None:
                        return RecoHelper.NoResult
                    for value, label, box in candidates:
                        if LABELS.index(label) == plan.category:
                            return RecoHelper.rt(box=box, text=f"{label}:{value}")
                    _request_clear(state, image)
                    return RecoHelper.NoResult
                target = toggle_target(dice, plan.keep_normal, plan.keep_green)
                if mode == "hold":
                    if target is None:
                        return RecoHelper.NoResult
                    x, y, w, h = target.box
                    return RecoHelper.rt(box=(x + w // 2, y + h // 2, 1, 1), text=str(target.value))
                if target is not None:
                    return RecoHelper.NoResult
            if mode != "roll" or remaining == 0:
                return RecoHelper.NoResult
            # 长按提示仅在可投掷时出现；模板定位实际骰盅，禁止按文字偏移盲点。
            if not _recognize(context, image, "诡计骰子_长按提示").hit:
                return RecoHelper.NoResult
            cup = _recognize(context, image, "诡计骰子_骰盅")
            if not cup.hit or cup.best_result is None:
                return RecoHelper.NoResult
            x, y = RecoHelper.get_res_center(cup.best_result)
            return RecoHelper.rt(box=(x, y, 1, 1))
        except Exception as error:
            Prompter.log(f"决策识别异常：{type(error).__name__}")
            return RecoHelper.NoResult
