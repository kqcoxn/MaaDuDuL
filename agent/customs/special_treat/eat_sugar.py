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

import re
import time

from agent.customs.utils import Prompter, MatrixOperator, LocalStorage
from agent.customs.maahelper import ParamAnalyzer, Tasker, RecoHelper

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
        - level 或 l：关卡编号（1-15）

    关卡布局：
        - 1-8 关：屏幕可见区域，起始坐标 (118, 238)，每行 4 个，共 2 行
        - 9-15 关：需要向上滑动后可见，起始坐标 (117, 343)，每行 4 个，共 2 行
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
            if level < 8:
                tasker.swipe(360, 210, 360, 596).wait()
                mo = MatrixOperator(118, 238, 163, 178)
                row = (level - 1) // 4 + 1
                col = (level - 1) % 4 + 1
                tasker.click(*mo.get_pos(row, col))

            # 关卡 9-15
            else:
                tasker.swipe(360, 596, 360, 210).wait()
                mo = MatrixOperator(117, 343, 163, 178)
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
    到手蜡关卡采用 5 列布局

    参数格式：
        - level 或 l：关卡编号（从 1 开始）

    关卡布局：
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
            if type(level) is int and level < 10:
                level = f"0{level}"

            Tasker(context).run(
                "清紫糖_查找关卡开始",
                {
                    "清紫糖_查找指定关卡1": {"expected": f"{level}"},
                    "清紫糖_查找指定关卡2": {"expected": f"{level}"},
                    "清紫糖_查找指定关卡3": {"expected": f"{level}"},
                },
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
    支持的心形关卡类型：龙族、精灵、幽灵、仙灵、魔女、自然灵、兽人。
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

            # 执行速刷
            Tasker(context).run("速战_开始")

            # 更新执行进度
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
