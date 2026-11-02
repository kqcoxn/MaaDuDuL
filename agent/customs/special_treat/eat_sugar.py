"""
清紫糖 / 清红糖 模块

本模块实现了游戏内两种主要糖果资源（紫糖和红糖）的清理相关自定义动作。
包含克隆工厂、到手蜡、副本关卡、金币大作战等紫糖关卡的选择，
以及红糖关卡的循环定位与执行功能。
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.context import Context

import os
import re
import time

import numpy as np

from agent.customs.utils import CounterManager, Prompter, MatrixOperator, LocalStorage
from agent.customs.maahelper import ParamAnalyzer, Tasker, RecoHelper

from .store import RedReserve

# ============== 清紫糖 ==============


@AgentServer.custom_action("quick_fight")
class QuickFight(CustomAction):
    """快速战斗的自定义动作

    直接启动速战流程，支持指定作战次数。
    当指定次数时，会覆盖速战流程中的相关配置。

    参数格式：
        - times 或 t：作战次数（可选，默认为 -1 表示不限次数）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行快速战斗操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含作战次数

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            # 解析参数获取关卡编号
            args = ParamAnalyzer(argv)
            times: int = args.get(["times", "t"], -1)

            pipeline_override = {}
            if times > 0:
                Prompter.log(f"指定作战次数：{times} 次")
                pipeline_override = {
                    "速战_确保可战斗": {"next": "速战_指定作战次数"},
                    "速战_输入作战次数": {"input_text": str(times)},
                }

            Tasker(context).run("速战_开始", pipeline_override)

            return True
        except Exception as e:
            return Prompter.error("速战", e)


@AgentServer.custom_action("select_clone_level")
class SelectCloneLevel(CustomAction):
    """选择克隆工厂关卡的自定义动作

    根据传入的关卡编号，自动计算屏幕坐标并点击对应的关卡。

    参数格式：
        - level 或 l：关卡编号（1-18）

    关卡布局：
        - 1-8 关：屏幕可见区域，起始坐标 (118, 238)，每行 4 个，共 2 行
        - 9-18 关：需要向上滑动至底部后可见，起始坐标 (117, 174)，每行 4 个，共 3 行
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            # 解析参数获取关卡编号
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            tasker = Tasker(context)

            # 关卡 1-8
            if level <= 8:
                tasker.swipe(360, 210, 360, 596).wait(1)
                mo = MatrixOperator(118, 238, 163, 178)
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))

            # 关卡 9-18
            else:
                tasker.swipe(360, 596, 360, 210).wait(1)
                mo = MatrixOperator(117, 174, 163, 178)
                level -= 8
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))

            return True
        except Exception as e:
            return Prompter.error("选择克隆工厂关卡", e)


@AgentServer.custom_action("select_crayon_level")
class SelectCrayonLevel(CustomAction):
    """选择到手蜡关卡的自定义动作

    根据传入的关卡编号，自动计算屏幕坐标并点击对应的关卡。
    到手蜡关卡采用每页 2 行、每行 5 列的布局。

    参数格式：
        - level 或 l：关卡编号（1-12）

    关卡布局：
        - 第 1 页：1-10 关，左翻页按钮坐标 (244, 679)
        - 第 2 页：11-12 关，右翻页按钮坐标 (439, 679)
        - 起始坐标：(80, 264)
        - 间隔：横向 123px，纵向 276px
        - 每行 5 个关卡
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            tasker = Tasker(context)

            if level <= 10:
                tasker.click(244, 679).wait()
            else:
                tasker.click(439, 679).wait()
                level -= 10

            mo = MatrixOperator(80, 264, 123, 276)
            row = (level - 1) // 5 + 1
            col = (level - 1) % 5 + 1
            tasker.click(*mo.get_pos(row, col))

            return True
        except Exception as e:
            return Prompter.error("选择到手蜡关卡", e)


@AgentServer.custom_action("select_duplicate_level")
class SelectDuplicateLevel(CustomAction):
    """选择副本关卡的自定义动作

    根据传入的关卡编号，通过 Pipeline 查找并选择对应的副本关卡。
    自动将小于 10 的关卡编号格式化为两位数字（如 1 转换为 "01"）。

    参数格式：
        - level 或 l：关卡编号（整数型）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行副本关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])
            Prompter.log(f"选择关卡：{level}")

            tasker = Tasker(context)
            if level < 7:
                tasker.swipe(360, 210, 360, 596).wait()
                mo = MatrixOperator(125, 160, 230, 230)
                row = (level - 1) // 3 + 1
                col = (level - 1) % 3 + 1
                tasker.click(*mo.get_pos(row, col))
            else:
                tasker.swipe(360, 596, 360, 210).wait()
                mo = MatrixOperator(125, 320, 230, 230)
                level -= 6
                row = (level - 1) // 3 + 1
                col = (level - 1) % 3 + 1
                tasker.click(*mo.get_pos(row, col))

            tasker.run(
                "速战", {"速战": {"custom_recognition_param": "e=速战_确认奖励"}}
            )

            return True
        except Exception as e:
            return Prompter.error("选择副本关卡", e)


@AgentServer.custom_action("select_gold_level")
class SelectGoldLevel(CustomAction):
    """选择金币大作战关卡的自定义动作

    根据传入的关卡编号，自动定位并选择金币大作战副本中的对应关卡。
    仅支持 13-20 关，小于 13 的关卡会报错。

    参数格式：
        - level 或 l：关卡编号（13-20）

    关卡定位规则：
        - 13-18 关：点击右上角区域后查找
        - 19-20 关：点击右下角区域后查找
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行金币大作战关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含关卡编号

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            # 解析参数获取关卡编号
            args = ParamAnalyzer(argv)
            level: int = args.get(["level", "l"])

            Prompter.log(f"选择关卡：{level}")
            if type(level) is not int:
                level = int(level)

            # 获取当前楼层
            rh = RecoHelper(context).recognize("清紫糖_检测金币B1入口")
            current_floor = 2 if rh.hit and len(rh.filtered_results) > 0 else 1
            Prompter.log(f"当前楼层：{current_floor}")

            # 进入对应区域
            if level < 13:
                Prompter.error("金币大作战仅支持 13-24 关")
            elif level < 21:
                if current_floor == 2:
                    rh.click()
                    time.sleep(0.8)
                if level < 19:
                    Tasker(context).run("清紫糖_金币右上角")
                else:
                    Tasker(context).run("清紫糖_金币右下角")
            elif level < 25:
                if current_floor == 1:
                    Tasker(context).run("清紫糖_金币右下角")
                    time.sleep(0.8)
                    RecoHelper(context).recognize("清紫糖_检测金币B2入口").click()
                    time.sleep(0.8)
            else:
                Prompter.error("金币大作战仅支持 13-24 关")
            time.sleep(0.8)

            # 选择关卡
            Tasker(context).run(
                "清紫糖_直接查找关卡",
                {
                    "清紫糖_查找指定关卡1": {"expected": f"{level}"},
                    "清紫糖_查找指定关卡2": {"expected": f"{level}"},
                    "清紫糖_查找指定关卡3": {"expected": f"{level}"},
                },
            )

            return True
        except Exception as e:
            return Prompter.error("选择金币大作战关卡", e)


# ============== 清红糖 ==============


@AgentServer.custom_recognition("find_level")
class FindLevel(CustomRecognition):
    """关卡查找识别器。

    优先匹配完整 OCR 结果，未命中时仅合并可能组成关卡名的文本碎片，
    解决新版 ppocr 将类似 "9-3" 拆分成多个文本框的问题，并排除星级等装饰文本。

    参数格式（custom_recognition_param）：
        - chapter 或 c：章节号
        - stage 或 s：关卡号
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        try:
            args = ParamAnalyzer(argv)
            chapter = args.get(["chapter", "c"])
            stage = args.get(["stage", "s"])

            rh = RecoHelper(context, argv).recognize("识别", {"recognition": "OCR"})
            if not rh.hit:
                Prompter.log("OCR 未识别到任何文本")
                return RecoHelper.NoResult

            pattern = re.compile(
                rf"^\s*{re.escape(str(chapter))}.*?{re.escape(str(stage))}\D*$"
            )

            # 优先使用完整 OCR 结果，保留精确的点击范围。
            for item in rh.filtered_results:
                if pattern.search(item.text.strip()):
                    return RecoHelper.rt(result=item)

            # 合并前排除星级等装饰文本，避免污染关卡名。
            level_parts = [
                item
                for item in rh.filtered_results
                if re.search(r"\d", item.text)
                or re.fullmatch(r"\s*[-–—]\s*", item.text)
            ]
            merged = RecoHelper.merge_nearby(level_parts, radius=20)

            for item in merged:
                if pattern.search(item.text.strip()):
                    return RecoHelper.rt(result=item)

            return RecoHelper.NoResult
        except Exception as e:
            return Prompter.error("查找关卡", e, reco_detail=True)


@AgentServer.custom_action("select_heart_type")
class SelectHeartType(CustomAction):
    """选择心形关卡类型的自定义动作。

    根据参数指定的心形关卡类型，点击对应的关卡入口坐标。
    支持的心形关卡类型：龙族、精灵、幽灵、仙灵、魔女、自然灵、兽人、秘灵。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行选择心形关卡类型的操作。

        Args:
            context: MaaFramework 上下文对象。
            argv: 自定义动作运行参数。

        Returns:
            bool: 操作成功返回 True，失败返回 False。

        Raises:
            Exception: 选择关卡过程中发生异常时，通过 Prompter 记录错误并返回 False。
        """
        try:
            args = ParamAnalyzer(argv)
            level: str = args.get(["type", "t"])

            # 根据关卡类型确定点击坐标
            target = [408, 168]
            if level == "龙族":
                target = [408, 168]
            elif level == "精灵":
                target = [638, 185]
            elif level == "幽灵":
                target = [883, 171]
            elif level == "仙灵":
                target = [662, 341]
            elif level == "魔女":
                target = [900, 323]
            elif level == "自然灵":
                target = [381, 463]
            elif level == "兽人":
                target = [868, 488]
            elif level == "秘灵":
                target = [642, 490]
            else:
                Prompter.error("无效的心形关卡类型")
                return False
            Tasker(context).click(*target)

            return True
        except Exception as e:
            return Prompter.error("选择心形关卡", e)


@AgentServer.custom_action("select_red_level")
class SelectRedLevel(CustomAction):
    """选择红糖关卡的自定义动作

    根据传入的关卡区间，循环定位并执行关卡。支持持久化记录当前执行进度，
    确保每次执行时自动推进到下一个关卡。

    参数格式：
        - start_level 或 sl：起始关卡，格式为"章-关"（如"24-9"）
        - end_level 或 el：结束关卡，格式为"章-关"（如"25-3"）

    关卡规则：
        - 每章固定10关
        - 循环执行从起始关卡到结束关卡之间的所有关卡
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行红糖关卡选择操作

        参数：
            context：MaaFramework 上下文对象
            argv：自定义动作参数，包含起始和结束关卡

        返回：
            bool：操作成功返回 True，失败返回 False

        异常：
            捕获所有异常并通过 Prompter.error 输出错误信息
        """
        try:
            args = ParamAnalyzer(argv)
            start_level: str = args.get(["start_level", "sl"])
            end_level: str = args.get(["end_level", "el"])

            # 解析关卡区间
            start_chapter, start_stage = self._parse_level(start_level)
            end_chapter, end_stage = self._parse_level(end_level)

            if start_chapter is None or end_chapter is None:
                return Prompter.error("选择红糖关卡", "关卡格式错误，应为'章-关'格式")

            # 获取持久化的执行进度
            storage_key = "red_level_progress"
            current_progress = LocalStorage.get(storage_key)

            # 检查进度是否在有效区间内，若不在则重置
            if current_progress and not self._is_progress_in_range(
                current_progress, start_chapter, start_stage, end_chapter, end_stage
            ):
                current_progress = None

            # 确定本次要执行的关卡
            target_chapter, target_stage = self._get_target_level(
                start_chapter, start_stage, end_chapter, end_stage, current_progress
            )

            Prompter.log(f"本次目标关卡：{target_chapter}-{target_stage}")

            # 检查当前界面的关卡，判断是第几章，若不在目标章节跳转到目标章节
            current_chapter_results = (
                RecoHelper(context).recognize("清红糖_识别当前章节").filtered_results
            )

            # 从关卡名中解析章节号
            detected_chapter = None
            if current_chapter_results:
                for result in current_chapter_results:
                    chapter = self._parse_chapter_from_level_name(result.text)
                    if chapter is not None:
                        detected_chapter = chapter
                        Prompter.log(f"识别到当前章节：{detected_chapter}")
                        break

            # 如果当前章节与目标章节不同，则进行跳转
            if detected_chapter != target_chapter:
                chapter_diff = target_chapter - detected_chapter
                direction = "后" if chapter_diff > 0 else "前"
                Prompter.log(f"向{direction}跳转 {abs(chapter_diff)} 章")
                if chapter_diff > 0:
                    Tasker(context).run(
                        "清红糖_章节后跳",
                        {"清红糖_章节后跳": {"repeat": chapter_diff}},
                    )
                else:
                    Tasker(context).run(
                        "清红糖_章节前跳",
                        {"清红糖_章节前跳": {"repeat": abs(chapter_diff)}},
                    )
            else:
                Prompter.log(f"当前已在目标章节")

            # 查找章节内关卡的位置，并选中关卡
            Prompter.log(f"查找并选中关卡：{target_stage}")
            Tasker(context).run(
                "清红糖_查找关卡开始",
                {
                    "清红糖_查找关卡": {
                        "custom_recognition_param": f"c={target_chapter}&s={target_stage}"
                    }
                },
            )

            # 执行速刷（走我们自己的速战包装，带入场券不足/饥饿提示/补糖分支与预留场次）
            detail = run_candy_fight(context)
            if detail is None:
                Prompter.log("预留体力不足，跳过区间战斗")
                return False
            # 没打到收尾节点（入场券不足/关卡不可用/挨饿等）不算成功，也不推进进度
            if not fight_finished(detail):
                Prompter.log(
                    f"区间战斗没打成，最后节点 {Tasker.get_last_node_name(detail)}，本轮跳过且不推进进度"
                )
                return False

            # 更新执行进度（只有真的打完才推进）
            next_chapter, next_stage = self._get_next_level(
                target_chapter,
                target_stage,
                start_chapter,
                start_stage,
                end_chapter,
                end_stage,
            )
            LocalStorage.set(storage_key, f"{next_chapter}-{next_stage}")
            Prompter.log(f"已记录下次执行关卡：{next_chapter}-{next_stage}")

            return True
        except Exception as e:
            return Prompter.error("选择红糖关卡", e)

    def _parse_level(self, level_str: str):
        """解析关卡字符串为章节和关卡编号

        参数：
            level_str：关卡字符串，格式为"章-关"（如"24-9"）

        返回：
            tuple: (章节编号, 关卡编号)，解析失败返回 (None, None)
        """
        try:
            parts = level_str.split("-")
            if len(parts) != 2:
                return None, None
            chapter = int(parts[0])
            stage = int(parts[1])
            if chapter < 1 or stage < 1 or stage > 10:
                return None, None
            return chapter, stage
        except (ValueError, AttributeError):
            return None, None

    def _parse_chapter_from_level_name(self, level_name: str):
        """从关卡名称中解析章节号

        参数：
            level_name：关卡名称，格式为"章-关"（如"24-9"）

        返回：
            int: 章节号，解析失败返回 None
        """
        try:
            # 清理文本中的多余字符
            cleaned = level_name.strip().replace(" ", "")
            parts = cleaned.split("-")
            if len(parts) >= 2:
                chapter = int(parts[0])
                return chapter
            return None
        except (ValueError, AttributeError):
            return None

    def _get_target_level(
        self,
        start_chapter: int,
        start_stage: int,
        end_chapter: int,
        end_stage: int,
        current_progress: str,
    ):
        """确定本次要执行的目标关卡

        参数：
            start_chapter：起始章节
            start_stage：起始关卡
            end_chapter：结束章节
            end_stage：结束关卡
            current_progress：持久化记录的当前进度（格式"章-关"）

        返回：
            tuple: (目标章节, 目标关卡)
        """
        if current_progress is None:
            # 首次执行，从起始关卡开始
            return start_chapter, start_stage

        # 有进度记录，从记录的关卡继续
        chapter, stage = self._parse_level(current_progress)
        if chapter is None:
            return start_chapter, start_stage
        return chapter, stage

    def _get_next_level(
        self,
        current_chapter: int,
        current_stage: int,
        start_chapter: int,
        start_stage: int,
        end_chapter: int,
        end_stage: int,
    ):
        """计算下一个要执行的关卡

        参数：
            current_chapter：当前章节
            current_stage：当前关卡
            start_chapter：起始章节
            start_stage：起始关卡
            end_chapter：结束章节
            end_stage：结束关卡

        返回：
            tuple: (下一章节, 下一关卡)，如果已完成所有关卡则回到起始关卡
        """
        # 检查是否已完成所有关卡，回到起始关卡继续循环
        if current_chapter == end_chapter and current_stage == end_stage:
            return start_chapter, start_stage

        # 计算下一关卡
        if current_stage < 10:
            # 同一章的下一关
            return current_chapter, current_stage + 1
        else:
            # 下一章的第1关
            return current_chapter + 1, 1

    def _is_progress_in_range(
        self,
        progress: str,
        start_chapter: int,
        start_stage: int,
        end_chapter: int,
        end_stage: int,
    ) -> bool:
        """检查进度是否在有效区间内

        参数：
            progress：当前进度，格式为"章-关"
            start_chapter：起始章节
            start_stage：起始关卡
            end_chapter：结束章节
            end_stage：结束关卡

        返回：
            bool：进度在区间内返回 True，否则返回 False
        """
        chapter, stage = self._parse_level(progress)
        if chapter is None:
            return False

        # 将关卡转换为可比较的数值（章*10 + 关）
        progress_value = chapter * 10 + stage
        start_value = start_chapter * 10 + start_stage
        end_value = end_chapter * 10 + end_stage

        return start_value <= progress_value <= end_value


# ============== 速战包装 ==============

# 每场速战消耗的红糖（14-9 微微辣实测 10）；章节单价不同会导致场次偏多，届时改为读单价
STAMINA_PER_FIGHT = 10
# 顶部体力识别节点，与购买糖果共用（ROI 由红色糖果球锚点动态给出）
STAMINA_NODE = "购买糖果_识别顶部体力"
# 单次读取最多扫几遍（单次读数不可信，按多读一致性判定）
STAMINA_READS = 3
# 红糖容量上限：超过它的读数一律判为无效（例如把别的文字读成 15354）
STAMINA_CAP = 999
# 双取字框交叉读取：宽框（左余量与右侧都放宽，容下三位数字+斜杠+三位数字+加号）与常规框
STAMINA_BALL_ROI_WIDE = (-16, 16, 220, 48)
# 读数失败现场转储目录（相对项目根，已被 .gitignore 的 debug/ 覆盖）
STAMINA_DUMP_DIR = os.path.join("debug", "stamina")
# 读数前的画面稳定门闩：复用速战面板识别节点（OCR「速战」）
STAMINA_GATE_NODE = "速战_打开速战面板"
STAMINA_GATE_TRY = 3
STAMINA_GATE_WAIT = 0.4


# 最近一次扫描的现场信息，供失败转储使用
_PROBE: dict = {}


# 锚点参数：顶部横带高度、红球簇宽度范围、红球右边界到数字的偏移与取字框（1280 基准）
STAMINA_BAND_HEIGHT = 60
STAMINA_BALL_WIDTH = (20, 60)
# 只在顶栏左段找球：实测糖果球右边界 512（冒险页）~701（关卡页），
# 右侧真正的红色徽标在 1100 之后，取 900 兼顾覆盖与排除
STAMINA_BALL_X_MAX = 900
STAMINA_BALL_ROI = (4, 24, 120, 34)
# 锚点失败时的兜底取字框：主界面、关卡页
# 关卡页顶栏因左侧有返回箭头+标题而整体右移，取字框要相应右挪
STAMINA_FALLBACK_ROIS = ([590, 26, 130, 34], [700, 22, 160, 44])

# 我们自己发起速战时追加的候选：Tasker.run 只在调用方给了 next 时才沿用，
# 因此这里显式写入即可盖过 monitor 重建，无需修改共享的 速战.json
FIGHT_OVERRIDE = {
    "速战_打开速战面板": {
        "next": [
            "速战_确保可战斗",
            "清红糖_入场券不足",
            "速战_无法速战",
            "速战_体力不足",
            "清红糖_饥饿提示",
        ]
    },
    "速战_体力不足": {"next": ["清红糖_补糖"]},
}


def find_red_ball(img: np.ndarray) -> int | None:
    """在顶部横带里定位红色糖果球，返回其右边界 x（1280 基准）。

    红糖就是那颗红球，球右边的数字就是体力；球会随页面整体移动，
    所以用球做锚点比固定 ROI 可靠。只在左半屏找，避免把右侧的红色角标
    当成糖果球（实测球右边界主界面 583、关卡页 697，右侧徽标都在 1100 之后）。

    Args:
        img：当前截图

    Returns:
        int | None：红球右边界，找不到时返回 None
    """
    scale = img.shape[1] / 1280
    band = np.asarray(img[: round(STAMINA_BAND_HEIGHT * scale)], dtype=np.int16)
    band = band[:, : min(band.shape[1], round(STAMINA_BALL_X_MAX * scale))]
    if band.size < 3:
        return None

    # Maa 的截图是 BGR：先按原顺序试（RGB 输入可直接命中），不中再翻转通道重试。
    # 不用「通道排序法」，实测它会把灰蓝元素也算成红，在真实 Maa 帧上多出 x≈15..74 的假簇。
    for source in (band, band[:, :, ::-1]):
        anchor = leftmost_ball(source, scale)
        if anchor is not None:
            return anchor
    return None


def red_mask(band: np.ndarray) -> np.ndarray:
    """红色掩码（按 R/G/B 直取，调用方需保证通道顺序）。

    Args:
        band：顶部横带（RGB 或翻转后的 BGR）

    Returns:
        np.ndarray：布尔掩码
    """
    red, green, blue = band[:, :, 0], band[:, :, 1], band[:, :, 2]
    return (red > 150) & (red - green > 70) & (red - blue > 60)


def leftmost_ball(band: np.ndarray, scale: float) -> int | None:
    """取最左侧宽度落在糖果球区间的红色簇右边界。

    Args:
        band：顶部横带
        scale：截图宽度与 1280 的比例

    Returns:
        int | None：红球右边界（1280 基准），没有合格簇时返回 None
    """
    hits = red_mask(band).sum(axis=0) > 0
    start = None
    for index, hit in enumerate(hits):
        if hit and start is None:
            start = index
        elif not hit and start is not None:
            width = (index - start) / scale
            if STAMINA_BALL_WIDTH[0] <= width <= STAMINA_BALL_WIDTH[1]:
                return round(index / scale)
            start = None
    if start is not None:
        width = (len(hits) - start) / scale
        if STAMINA_BALL_WIDTH[0] <= width <= STAMINA_BALL_WIDTH[1]:
            return round(len(hits) / scale)
    return None


def display_text(raw: str) -> str:
    """把 OCR 原文裁成只含数字与分隔符的展示文本。

    加号按钮、叶子图标常被 OCR 一并读入（如 202/202+、X、Y），日志里只保留数字部分；
    裁空时回退原文，避免把真实异常信息吞掉。
    """
    cleaned = re.sub(r"[^0-9/,.]", "", raw or "")
    return cleaned or (raw or "")


def parse_stamina(text: str) -> int | None:
    """从「当前/上限」文本里取出当前体力。

    采纳条件：至少两个数字、上限大于 0、且两个值都不超过 STAMINA_CAP。
    买糖后体力可超过显示上限（833/202 这类真实读数必须采纳），但不能超过容量上限；
    单个数字（金币、叶子）或荒谬值（把弹窗里的文字读成 15.354,603 → 354603）一律拒绝。

    Args:
        text：OCR 原文

    Returns:
        int | None：当前体力，不合规时返回 None
    """
    tokens = re.findall(r"\d+", text.replace(",", ""))
    if len(tokens) < 2:
        return None
    # 游戏里的数字不会有前导零（真实 2 显示 2，不会显示 02），出现 02/021 必是错读首位
    if re.match(r"^0\d+", tokens[0]) or re.match(r"^0\d+", tokens[1]):
        return None
    current, cap = int(tokens[0]), int(tokens[1])
    if cap <= 0 or current > STAMINA_CAP or cap > STAMINA_CAP:
        return None
    return current


def has_leading_zero(text: str) -> bool:
    """判断文本里的数字是否出现前导零（如 02、021）。

    Args:
        text：OCR 原文

    Returns:
        bool：存在前导零的数字返回 True
    """
    return any(re.match(r"^0\d+", token) for token in re.findall(r"\d+", text.replace(",", "")))


def read_roi(rh: RecoHelper, roi: list[int], only_rec: bool) -> tuple[str, int | None]:
    """按指定 ROI 读一次体力。

    Args:
        rh：识别辅助器
        roi：取字框
        only_rec：为 True 时跳过文字检测、整框直接识别。
            相机里「111」这种三连数字，检测常把三个 1 并成一个框而只认出一个「1」，
            跳过检测就能整行读回 111/204。

    Returns:
        tuple：OCR 原文与解析出的体力（无效为 None）
    """
    override = {"roi": roi}
    if only_rec:
        override["only_rec"] = True
    text = rh.recognize(STAMINA_NODE, override).concat() or ""
    return text, parse_stamina(text)


def cross_read(left: tuple[str, int | None], right: tuple[str, int | None]) -> tuple[str, int | None]:
    """交叉两个取字框的结果，取更可信的一个。

    Args:
        left：宽框的 (原文, 体力)
        right：常规框的 (原文, 体力)

    Returns:
        tuple：采纳的 (原文, 体力)，无法裁决时为 (原文, None)
    """
    left_text, left_value = left
    right_text, right_value = right

    if left_value is not None and right_value is not None:
        if left_value == right_value:
            return right_text, right_value
        # 前导零已由 parse_stamina 判无效，这里只作兜底：优先不带前导零的那个
        if has_leading_zero(left_text) and not has_leading_zero(right_text):
            return right_text, right_value
        if has_leading_zero(right_text) and not has_leading_zero(left_text):
            return left_text, left_value
        Prompter.log(f"两种取字框读到 {left_value} 和 {right_value}，不一致")
        return right_text, None

    if left_value is not None:
        return left_text, left_value
    if right_value is not None:
        return right_text, right_value
    return right_text, None


def dump_stamina_failure() -> str:
    """把最近一次扫描的现场转储成 npy，并输出一行诊断日志。

    截图用 numpy 直接存 .npy（仓库没有 PIL），目录 debug/stamina/ 已被 .gitignore 忽略。

    Returns:
        str：截图路径，保存失败时为空串
    """
    image = _PROBE.get("image")
    path = ""
    if image is not None:
        try:
            os.makedirs(STAMINA_DUMP_DIR, exist_ok=True)
            path = os.path.join(STAMINA_DUMP_DIR, f"fail_{int(time.time() * 1000)}.npy")
            np.save(path, image)
        except Exception as error:
            Prompter.log(f"保存体力识别截图失败，{error}")
            path = ""

    anchor = _PROBE.get("anchor")
    if anchor is None:
        Prompter.log(f"未能读取红糖体力，锚点未找到，截图存在 {path}")
    else:
        Prompter.log(f"未能读取红糖体力，锚点 {anchor}，截图存在 {path}")
        Prompter.log(
            f"宽框 {_PROBE.get('wide')} 读到 {display_text(_PROBE.get('wide_text', ''))}，"
            f"常规框 {_PROBE.get('normal')} 读到 {display_text(_PROBE.get('normal_text', ''))}，"
            f"整框 {display_text(_PROBE.get('pure_text', ''))}"
        )
    return path


def scan_stamina(context: Context) -> tuple[str, int | None]:
    """扫一次顶部红糖体力：锚点处双框交叉读取，失败再试兜底 ROI。

    Args:
        context：MaaFW 上下文对象

    Returns:
        tuple：最后一次 OCR 原文与解析出的体力（解析不到为 None）
    """
    rh = RecoHelper(context).refresh_screencap()
    anchor = find_red_ball(rh.screencap) if rh.screencap is not None else None
    # 记录现场，供失败时转储复现（截图是 BGR/RGB 都只是通道顺序，形状即屏幕分辨率）
    _PROBE.clear()
    _PROBE["image"] = rh.screencap
    _PROBE["anchor"] = anchor

    text = ""
    if anchor is not None:
        offsets = (STAMINA_BALL_ROI_WIDE, STAMINA_BALL_ROI)
        boxes = [[anchor + x, top, width, height] for x, top, width, height in offsets]
        _PROBE["wide"] = boxes[0]
        _PROBE["normal"] = boxes[1]
        left_text, left_value = read_roi(rh, boxes[0], only_rec=False)
        right_text, right_value = read_roi(rh, boxes[1], only_rec=False)
        _PROBE["wide_text"] = left_text
        _PROBE["normal_text"] = right_text
        value_text, value = cross_read((left_text, left_value), (right_text, right_value))
        text = value_text

        # 再整框读一次（跳过检测）：三连数字被检测并成一个框时，这里能读回完整数值
        pure_text, pure_value = read_roi(rh, boxes[1], only_rec=True)
        _PROBE["pure_text"] = pure_text
        if pure_value is not None:
            if value is not None and pure_value != value:
                Prompter.log(
                    f"体力两种读法不一致（检测 {value} / 整框 {pure_value}），采用整框读数"
                )
            return pure_text, pure_value
        if value is not None:
            return text, value

    for roi in STAMINA_FALLBACK_ROIS:
        text, stamina = read_roi(rh, roi, only_rec=False)
        if stamina is not None:
            return text, stamina
    return text, None


def read_stamina(context: Context) -> int | None:
    """读取顶部红糖体力：多次读取做一致性判定，读到什么就信什么。

    Note:
        - 仅用于红糖/体力口径（红球锚点 + 兜底 ROI）；紫糖顶部是星星糖，读数口径不同，不要复用；
        - 采纳条件：至少两个数字、无前导零、上限大于 0 且不超容量上限；
        - 单次读数不可信，最多读 STAMINA_READS 次、每次重新截图：
          前两次一致即采纳；否则读第三次，出现两次的采纳，三次全不同则以最新为准；
        - 不与历史读数做比较（体力大额消耗是真实变化，历史比较只会误伤）。

    Args:
        context：MaaFW 上下文对象

    Returns:
        int | None：当前体力，读不到时返回 None
    """
    reads: list[tuple[str, int]] = []
    for _ in range(STAMINA_READS):
        text, stamina = scan_stamina(context)
        if stamina is None:
            continue
        reads.append((text, stamina))
        if len(reads) >= 2 and reads[-1][1] == reads[-2][1]:
            Prompter.log(f"读到红糖 {display_text(text)}")
            return stamina

    if not reads:
        # 全部读不到：转储现场，方便从 npy 里复现并量出数字真实位置
        dump_stamina_failure()
        return None

    for text, stamina in reads:
        if sum(1 for _, other in reads if other == stamina) >= 2:
            Prompter.log(f"读到红糖 {display_text(text)}")
            return stamina

    _, latest = reads[-1]
    Prompter.log(f"三次读到红糖不一致 {'/'.join(str(v) for _, v in reads)}，取最后一次 {latest}")
    return latest


def wait_fight_ready(context: Context) -> bool:
    """用「速战」按钮做门闩，确认画面已渲染完成。

    点「前往」后会有一段淡入过渡，此时顶栏数字可能还没画全，
    所以先等速战按钮出现，再读体力。

    Args:
        context：MaaFW 上下文对象

    Returns:
        bool：画面已稳定返回 True，重试仍不稳定返回 False
    """
    for _ in range(STAMINA_GATE_TRY):
        if RecoHelper(context).refresh_screencap().recognize(STAMINA_GATE_NODE).hit:
            return True
        Tasker(context).wait(STAMINA_GATE_WAIT)
    return False


def plan_fights(context: Context) -> tuple[bool, int | None]:
    """按活动任务预留决定本次速战是否开打、打几场。

    Note:
        - 每场速战消耗的红糖按 STAMINA_PER_FIGHT 估算（14-9 微微辣实测 10）；
        - 预留生效时，凡是无法确定体力（门闩失败或读数无效）都停止本轮，保护要留给活动的体力；
          预留未生效时一律放行。

    Args:
        context：MaaFW 上下文对象

    Returns:
        tuple：是否允许开打、指定场次（None 表示不指定，沿用原「最大」流程）
    """
    reserve = RedReserve.threshold
    if reserve <= 0:
        return True, None
    if RedReserve.done_today():
        return True, None

    # 先确认画面已稳（速战按钮可见），避免读到淡入过渡帧的半渲染数字；稳不了就停，别赌
    if not wait_fight_ready(context):
        Prompter.log("速战按钮未出现，画面未稳定，停止本轮刷取保护预留")
        return False, None

    stamina = read_stamina(context)
    if stamina is None:
        # 预留已生效，读数无效就停下，避免把要留给活动的体力花掉
        Prompter.log("预留生效但体力读数无效，停止本轮刷取保护预留")
        return False, None

    fights = stamina // STAMINA_PER_FIGHT - reserve // STAMINA_PER_FIGHT
    if fights <= 0:
        Prompter.log(f"已为活动任务预留 {stamina} 红糖，停止刷取")
        return False, None

    Prompter.log(f"当前红糖 {stamina}，预留 {reserve}，本次速战 {fights} 场")
    return True, fights


# 速战可能的正常收尾节点：跳过动画 / 领取奖励 / 等级提升
FIGHT_DONE_NODES = ("速战_确认奖励", "速战_等级提升", "速战_跳过动画")

# 这些失败出口自己已经打过原因，收尾判定不再补一句，避免前端重复
FIGHT_LOGGED_EXITS = (
    "清红糖_入场券不足",
    "清红糖_饥饿提示",
    "速战_无法速战",
    "速战_体力不足",
    "清红糖_补糖",
)


def fight_finished(detail) -> bool:
    """判断一次速战是否走到了正常收尾节点。

    速战有几条「打不了」的出口（入场券不足、关卡不可用、挨饿），
    它们同样会让任务正常返回，所以不能只看任务有没有抛异常。

    Args:
        detail：Tasker.run 返回的任务详情

    Returns:
        bool：走到了正常收尾节点返回 True
    """
    return Tasker.get_last_node_name(detail) in FIGHT_DONE_NODES


def run_candy_fight(context: Context):
    """用我们自己的 next 覆盖发起一次速战。

    在同一次嵌套 run 内把入场券不足、饥饿提示与补糖挂进候选列表，
    使这些分支能在速战自身的扫描循环里被命中，而不是等 run 结束后再补救；
    预留生效时按剩余场次直接指定作战次数。

    Args:
        context：MaaFW 上下文对象

    Returns:
        TaskDetail | None：速战任务的执行结果，预留不足未开打时返回 None
    """
    ok, fights = plan_fights(context)
    if not ok:
        return None

    override = {node: dict(patch) for node, patch in FIGHT_OVERRIDE.items()}
    if fights:
        override["速战_确保可战斗"] = {"next": ["速战_指定作战次数"]}
        override["速战_输入作战次数"] = {"input_text": str(fights)}
    return Tasker(context).run("速战_开始", override)


@AgentServer.custom_action("candy_fight")
class CandyFight(CustomAction):
    """红糖速战包装自定义动作类。

    以我们自己的 next 覆盖发起速战，候选里包含入场券不足、饥饿提示与补糖；
    只有真的打完（走到速战收尾节点）才算成功，打不了时返回 False 交给 on_error。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """发起一次带自定义分支的速战。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需额外参数）

        Returns:
            bool：正常打完并领到奖励返回 True
        """
        try:
            detail = run_candy_fight(context)
            if detail is None:
                Prompter.log("预留体力不足，跳过本次速战")
                return False
            if not fight_finished(detail):
                last_node = Tasker.get_last_node_name(detail)
                if last_node not in FIGHT_LOGGED_EXITS:
                    Prompter.log(f"速战没打成，最后节点 {last_node}，本轮跳过")
                return False
            return True
        except Exception as e:
            return Prompter.error("红糖速战", e)


@AgentServer.custom_action("candy_loop_gate")
class CandyLoopGate(CustomAction):
    """清红糖「购买红糖 → 心形」循环的兜底计数。

    购买成功后流程会经 购买红糖周期记录 回到 心形开始，形成循环；
    这里按轮次计数，超过上限就返回 False，交给流水线的 on_error 结束本轮，
    避免买得到糖却一直重跑。

    参数格式（custom_action_param）：
        - k：计数器键名，默认 buy_red_loop
        - m：最大轮次，默认 3
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """执行轮次计数。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数

        Returns:
            bool：还在上限内返回 True，超过上限返回 False
        """
        try:
            args = ParamAnalyzer(argv)
            key = args.get(["key", "k"], "buy_red_loop")
            limit = args.get(["max", "m", "mc"], 3)
            if not isinstance(limit, int) or limit <= 0:
                limit = 3
            if CounterManager.get(key, limit, 0).count() < 0:
                Prompter.log(f"购买与刷取已循环 {limit} 轮，结束本轮清红糖")
                return False
            return True
        except Exception as e:
            return Prompter.error("购买与刷取轮次", e)


@AgentServer.custom_action("red_stamina_check")
class RedStaminaCheck(CustomAction):
    """清红糖开局体力检查。

    开局体力连一场速战都不够时直接结束本轮，避免进关卡后才发现打不了。
    活动体力预留不在这里判断，由 run_candy_fight 在发起速战前处理。
    """

    MIN_STAMINA = 10

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        """检查开局红糖体力是否够一场速战。

        Args:
            context：MaaFW 上下文对象
            argv：自定义动作参数（本动作无需额外参数）

        Returns:
            bool：体力够继续返回 True，不足返回 False（由 on_error 回大厅收尾）
        """
        try:
            stamina = read_stamina(context)
            if stamina is None:
                Prompter.log("未能读取红糖体力，跳过开局检查")
                return True
            if stamina < self.MIN_STAMINA:
                Prompter.log(f"红糖不足，当前 {stamina}，结束本轮")
                return False
            return True
        except Exception as e:
            return Prompter.error("检查开局体力", e)
