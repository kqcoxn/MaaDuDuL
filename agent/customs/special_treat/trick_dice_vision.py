"""识别720p骰盘中已经排齐的骰子；动画、遮挡和未知布局返回失败。"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SeenDie:
    value: int
    green: bool
    held: bool
    box: tuple[int, int, int, int]


def _components(mask: np.ndarray) -> list[int]:
    pixels = set(zip(*np.nonzero(mask), strict=True))
    sizes = []
    while pixels:
        pending = [pixels.pop()]
        size = 0
        while pending:
            y, x = pending.pop()
            size += 1
            for point in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if point in pixels:
                    pixels.remove(point)
                    pending.append(point)
        if size >= 18:
            sizes.append(size)
    return sizes


def read_dice(image: np.ndarray) -> tuple[SeenDie, ...] | None:
    if image.shape[:2] != (720, 1280):
        return None
    result = []
    for held, left, top, right, bottom in ((True, 666, 94, 1069, 156), (False, 680, 348, 1105, 414)):
        region = image[top:bottom, left:right, :3].astype(np.int16)
        b, g, r = region[..., 0], region[..., 1], region[..., 2]
        orange = (r > 170) & (g > 55) & (r > g * 1.3) & (b < 95)
        green_mask = (g > 115) & (g > r * 1.25) & (g > b * 1.2)
        colored = orange | green_mask
        occupied = np.flatnonzero(colored.sum(axis=0) >= 5)
        if not len(occupied):
            continue
        splits = np.split(occupied, np.flatnonzero(np.diff(occupied) > 3) + 1)
        for columns in splits:
            x1, x2 = int(columns[0]), int(columns[-1]) + 1
            if x2 - x1 < 30:
                continue
            core_rows = np.flatnonzero(colored[:, x1:x2].sum(axis=1) >= max(12, (x2 - x1) * 0.35))
            if not len(core_rows):
                return None
            y1, y2 = int(core_rows.min()), int(core_rows.max()) + 1
            width, height = x2 - x1, y2 - y1
            if not 45 <= width <= 63 or not 45 <= height <= 63 or abs(width - height) > 7:
                return None
            face = region[y1 + 3 : y2 - 3, x1 + 3 : x2 - 3]
            fb, fg, fr = face[..., 0], face[..., 1], face[..., 2]
            green = bool(green_mask[y1:y2, x1:x2].sum() > orange[y1:y2, x1:x2].sum())
            blue = (fb > 100) & (fb > fr * 1.2) & (fb > fg * 1.05)
            if green and blue.sum() > 45:
                value = 0
            else:
                white = (face.min(axis=2) > 175) & (face.max(axis=2) - face.min(axis=2) < 65)
                ys, xs = np.nonzero(white)
                if len(xs) < 45:
                    return None
                # 普通骰的1是叶子图案，有一条深色叶脉，不能将其两半误认为两个点。
                leaf = not green and xs.max() - xs.min() < 27 and ys.max() - ys.min() < 24
                value = 1 if leaf else len(_components(white))
                if value not in range(1, 7) or (green and value == 1):
                    return None
            result.append(SeenDie(value, green, held, (left + x1, top + y1, width, height)))
    if len(result) != 5 or sum(die.green for die in result) not in (1, 5):
        return None
    return tuple(result)


def hand_counts(dice: tuple[SeenDie, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    normal = tuple(sum(not die.green and die.value == value for die in dice) for value in range(1, 7))
    green = tuple(sum(die.green and die.value == value for die in dice) for value in (0, 2, 3, 4, 5, 6))
    return normal, green


def toggle_target(dice: tuple[SeenDie, ...], keep: tuple[int, ...], keep_green: tuple[int, ...]) -> SeenDie | None:
    """每次只操作一颗；同点骰保留数量足够后不重复点击，布局移动后重新识别。"""
    groups = ((False, tuple(range(1, 7)), keep), (True, (0, 2, 3, 4, 5, 6), keep_green))
    # 先释放多余骰子，重新观察布局，再补足目标保留数量。
    for release in (True, False):
        for green, faces, counts in groups:
            for value, needed in zip(faces, counts, strict=True):
                matches = [die for die in dice if die.green == green and die.value == value]
                held = [die for die in matches if die.held]
                if release and len(held) > needed:
                    return held[-1]
                if not release and len(held) < needed:
                    return next(die for die in matches if not die.held)
    return None
