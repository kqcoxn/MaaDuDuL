"""诡计骰子：以整局期望总分为目标的有限状态动态规划。

计入剩余计分栏、上半区55分/40分奖励及一次全绿骰技能。
骰面暂按等概率；即时得分与后续期望一起决定登记或重掷。
普通骰计数按1..6，绿色骰计数按万能、2..6排列。
"""

from dataclasses import dataclass
from functools import cache
from itertools import product
from math import factorial

import numpy as np

LABELS = ("二点", "三点", "四点", "五点", "六点", "葫芦", "大顺", "快艇")
ALL_CATEGORIES = (1 << len(LABELS)) - 1
GREEN_FACES = (0, 2, 3, 4, 5, 6)


@cache
def _counts(n: int, faces: int = 6) -> tuple[tuple[int, ...], ...]:
    if faces == 1:
        return ((n,),)
    return tuple((first, *tail) for first in range(n + 1) for tail in _counts(n - first, faces - 1))


def score_hand(normal: tuple[int, ...], green: tuple[int, ...]) -> tuple[int, ...]:
    if (
        len(normal) != 6
        or len(green) != 6
        or min(*normal, *green) < 0
        or (sum(normal), sum(green)) not in ((4, 1), (0, 5))
    ):
        raise ValueError("需要四颗普通骰加一颗绿色骰，或五颗绿色骰")
    fixed = [a + b for a, b in zip(normal, (0, *green[1:]), strict=True)]
    best = [0] * 8
    for assignment in _counts(green[0]):
        counts = [a + b for a, b in zip(fixed, assignment, strict=True)]
        values = [counts[i] * (i + 1) for i in range(1, 6)]
        total = sum((i + 1) * count for i, count in enumerate(counts))
        values.append(total if sorted(count for count in counts if count) == [2, 3] else 0)
        values.append(30 if counts in ([1, 1, 1, 1, 1, 0], [0, 1, 1, 1, 1, 1]) else 0)
        values.append((70 if green[0] and counts[0] == 5 else 50) if 5 in counts else 0)
        best = [max(old, new) for old, new in zip(best, values, strict=True)]
    return tuple(best)


@dataclass(frozen=True)
class DiceDecision:
    category: int | None
    keep_normal: tuple[int, ...]
    keep_green: tuple[int, ...]
    expected_score: float  # 本轮及后续未填栏与最终奖励的期望，不含此前已登记分。
    stop_score: float  # 现在停止重掷并选择最佳登记栏时，对应的同口径期望。


@dataclass(frozen=True)
class SkillDecision:
    use: bool
    use_value: float
    save_value: float


class _DieGroup:
    def __init__(self, size: int) -> None:
        self.partial = [counts for n in range(size + 1) for counts in _counts(n)]
        self.index = {counts: i for i, counts in enumerate(self.partial)}
        self.full = _counts(size)
        self.full_index = {counts: i for i, counts in enumerate(self.full)}
        self.full_rows = np.array([self.index[counts] for counts in self.full])
        self.parents = []
        for n in range(size - 1, -1, -1):
            rows = [i for i, counts in enumerate(self.partial) if sum(counts) == n]
            children = [
                [self.index[tuple(c + (j == face) for j, c in enumerate(self.partial[i]))] for face in range(6)]
                for i in rows
            ]
            self.parents.append((np.array(rows), np.array(children)))
        self.holds = [
            [self.index[tuple(keep)] for keep in product(*(range(c + 1) for c in counts))] for counts in self.full
        ]
        width = max(map(len, self.holds))
        self.hold_rows = np.array([rows + [rows[0]] * (width - len(rows)) for rows in self.holds])
        self.probabilities = np.array(
            [factorial(size) / (6**size * np.prod([factorial(c) for c in counts])) for counts in self.full]
        )


class _RollModel:
    def __init__(self, normal: int, green: int) -> None:
        self.normal, self.green = _DieGroup(normal), _DieGroup(green)
        self.scores = np.array([[score_hand(n, g) for g in self.green.full] for n in self.normal.full], dtype=np.int16)

    def expectations(self, values: np.ndarray) -> np.ndarray:
        expected = np.empty((len(self.normal.partial), len(self.green.partial), *values.shape[2:]))
        # 先补齐所有普通骰部分保留，再沿绿色骰的部分保留反向求期望。
        green_full = np.empty((len(self.normal.partial), len(self.green.full), *values.shape[2:]))
        green_full[self.normal.full_rows] = values
        for rows, children in self.normal.parents:
            green_full[rows] = green_full[children].mean(axis=1)
        expected[:, self.green.full_rows] = green_full
        for rows, children in self.green.parents:
            expected[:, rows] = expected[:, children].mean(axis=2)
        return expected

    def reroll(self, values: np.ndarray) -> np.ndarray:
        expected = self.expectations(values)
        normal_best = expected[self.normal.hold_rows].max(axis=1)
        return normal_best[:, self.green.hold_rows].max(axis=2)


class DiceSolver:
    """精确回合内保留搜索，以及剩余栏位和上半区奖励的整局Bellman表。"""

    def __init__(self) -> None:
        self.model = _RollModel(4, 1)
        self.skill_model = _RollModel(0, 5)
        self.sheet = np.zeros((256, 56), dtype=np.float64)
        self.sheet[0, 55] = 40
        upper = np.arange(56)
        for mask in range(1, 256):
            self.sheet[mask] = self._round_value(self.model, self._stop_values(mask, upper))
        # 有技能的普通回合可将机会带到下轮；全绿回合结束后只能转入无技能表。
        self.skill_sheet = self.sheet.copy()
        self.use_skill_values = self.sheet.copy()
        self.save_skill_values = self.sheet.copy()
        for mask in range(1, 256):
            use = self._round_value(self.skill_model, self._stop_values(mask, upper, self.skill_model))
            save = self._round_value(self.model, self._stop_values(mask, upper, skill_available=True))
            self.use_skill_values[mask], self.save_skill_values[mask] = use, save
            self.skill_sheet[mask] = np.maximum(use, save)

    @staticmethod
    def _round_value(model: _RollModel, stop: np.ndarray) -> np.ndarray:
        values = stop
        for _ in range(2):
            values = np.maximum(stop, model.reroll(values))
        return np.einsum("ngu,n,g->u", values, model.normal.probabilities, model.green.probabilities)

    def _stop_values(
        self, mask: int, upper: np.ndarray, model: _RollModel | None = None, skill_available: bool = False
    ) -> np.ndarray:
        model = self.model if model is None else model
        sheet = self.skill_sheet if skill_available else self.sheet
        values = []
        for category in range(8):
            if mask & (1 << category):
                points = model.scores[:, :, category, None]
                next_upper = np.minimum(55, upper + (points if category < 5 else 0))
                values.append(points + sheet[mask ^ (1 << category), next_upper])
        return np.max(values, axis=0)

    def _indices(
        self, normal: tuple[int, ...], green: tuple[int, ...], mask: int, upper: int
    ) -> tuple[_RollModel, int, int]:
        model = self.skill_model if sum(green) == 5 else self.model
        if normal not in model.normal.full_index or green not in model.green.full_index:
            raise ValueError("仅支持四颗普通骰加一颗绿色骰，或五颗绿色骰")
        if not 1 <= mask <= ALL_CATEGORIES or not 0 <= upper <= 55:
            raise ValueError("无效的计分表")
        return model, model.normal.full_index[normal], model.green.full_index[green]

    def choose_skill(self, mask: int, upper: int) -> SkillDecision:
        if not 1 <= mask <= ALL_CATEGORIES or not 0 <= upper <= 55:
            raise ValueError("无效的计分表")
        use, save = float(self.use_skill_values[mask, upper]), float(self.save_skill_values[mask, upper])
        # 等值时使用，包括最后一轮无增益的情况，避免把机会带出整局。
        return SkillDecision(use >= save - 1e-7, use, save)

    def score_options(
        self, normal: tuple[int, ...], green: tuple[int, ...], mask: int, upper: int, skill_available: bool = False
    ) -> list[tuple[int, int, float]]:
        """各可登记栏的(类别、即时分、含本轮和后续/奖励的剩余收益期望)。"""
        model, n, g = self._indices(normal, green, mask, upper)
        if skill_available and model is self.skill_model:
            raise ValueError("全绿回合的技能已经消耗，不能再次保留技能机会")
        sheet = self.skill_sheet if skill_available else self.sheet
        options = []
        for category in range(8):
            if mask & (1 << category):
                points = int(model.scores[n, g, category])
                next_upper = min(55, upper + (points if category < 5 else 0))
                future = sheet[mask ^ (1 << category), next_upper]
                options.append((category, points, float(points + future)))
        return options

    def decide(
        self,
        normal: tuple[int, ...],
        green: tuple[int, ...],
        remaining: int,
        mask: int,
        upper: int,
        skill_available: bool = False,
    ) -> DiceDecision:
        model, n, g = self._indices(normal, green, mask, upper)
        if not 0 <= remaining <= 2:
            raise ValueError("无效的投掷次数")
        stop_value, category = max(
            (value, c) for c, _, value in self.score_options(normal, green, mask, upper, skill_available)
        )
        if remaining == 0:
            return DiceDecision(category, normal, green, stop_value, stop_value)
        stop = self._stop_values(mask, np.array([upper]), model, skill_available)[:, :, 0]
        values = stop
        for _ in range(remaining - 1):
            values = np.maximum(stop, model.reroll(values))
        expected = model.expectations(values)
        best_value, hold_normal, hold_green = stop_value, normal, green
        # 单绿骰保留原来的并列规则；全绿骰枚举每一种部分保留，不能只有全留/全掷。
        full_green = int(model.green.full_rows[g])
        empty_green = model.green.index[(0,) * 6]
        green_holds = [full_green, *(row for row in model.green.holds[g] if row not in (full_green, empty_green))]
        if empty_green != full_green:
            green_holds.append(empty_green)
        for normal_row in model.normal.holds[n]:
            for green_row in green_holds:
                value = float(expected[normal_row, green_row])
                if value > best_value + 1e-7:
                    best_value = value
                    hold_normal, hold_green = model.normal.partial[normal_row], model.green.partial[green_row]
        return DiceDecision(
            None if best_value > stop_value + 1e-7 else category,
            hold_normal,
            hold_green,
            best_value,
            stop_value,
        )
