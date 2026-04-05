"""自定义识别参数解析器模块

本模块提供用于解析 MaaFramework 自定义识别参数的工具类。
支持多种参数格式的自动解析，包括 JSON、查询字符串等。
"""

from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction

import json
import re
from urllib.parse import parse_qs, unquote


# ====================  参数解析器  ====================


class ParamAnalyzer:
    """自定义识别参数解析器

    将 MaaFramework 传递的自定义识别参数字符串解析为 Python 字典对象。
    支持的参数格式：
    - JSON 格式（对象或数组）
    - 查询字符串格式（key=value&key2=value2）

    Note:
        - 无法解析的参数将返回空字典
        - 查询字符串中重复的 key 会被转换为数组
    """

    def __init__(self, argv: CustomRecognition.AnalyzeArg | CustomAction.RunArg):
        """初始化参数解析器

        Args:
            argv: MaaFramework 传递的识别参数对象

        Returns:
            None

        Note:
            解析结果存储在 self.argv 字典中
        """
        self.argv: dict = self._parse_param(
            argv.custom_recognition_param
            if isinstance(argv, CustomRecognition.AnalyzeArg)
            else argv.custom_action_param
        )

    def _parse_param(self, param: str) -> dict:
        """解析参数字符串为字典

        依次尝试以下解析方式：
        1. JSON 格式解析（对象或数组）
        2. 查询字符串格式解析（key=value 形式）
        3. 解析失败则返回空字典

        Args:
            param: 待解析的参数字符串

        Returns:
            dict: 解析后的参数字典，解析失败返回空字典 {}

        Note:
            - 查询字符串中单值 key 会被解析为字符串，多值 key 会被解析为列表
            - 保留空白值以支持布尔型参数
        """
        param = param.strip()

        # 去除外层的引号
        if (param.startswith('"') and param.endswith('"')) or (
            param.startswith("'") and param.endswith("'")
        ):
            param = param[1:-1]

        # 尝试 JSON 格式解析
        if param.startswith("{") or param.startswith("["):
            try:
                return json.loads(param)
            except json.JSONDecodeError:
                pass

        # 尝试查询字符串格式解析
        if "=" in param:
            try:
                parsed = parse_qs(param, keep_blank_values=True)
                result = {}
                for key, value_list in parsed.items():
                    # 解码 URL
                    cleaned_values = [
                        unquote(v).strip('"').strip("'") for v in value_list
                    ]
                    result[key] = (
                        cleaned_values[0]
                        if len(cleaned_values) == 1
                        else cleaned_values
                    )
                return result
            except Exception:
                pass

        # 解析失败返回空字典
        return {}

    def get(self, key: str | list[str], default=None):
        """获取参数值

        Args:
            key: 参数键名，可以是单个字符串或字符串列表。
                 当传入列表时，按顺序查找，返回第一个命中的值
            default: 默认值，当 key 不存在时返回。
                     若为 None 且未获取到值，则抛出 KeyError

        Returns:
            参数值，若 key 不存在则返回 default
            如果值是数字字符串，自动转换为 int 或 float 类型

        Raises:
            KeyError: 当 default 为 None 且无法获取到值时
        """
        if isinstance(key, list):
            for k in key:
                if k in self.argv:
                    return self._convert_to_number(self.argv[k])
            if default is None:
                raise KeyError(f"参数 {key} 不存在且未提供默认值")
            return default

        if key in self.argv:
            return self._convert_to_number(self.argv[key])
        if default is None:
            raise KeyError(f"参数 '{key}' 不存在且未提供默认值")
        return default

    def _convert_to_number(self, value):
        """将字符串值转换为数字类型

        Args:
            value: 待转换的值

        Returns:
            如果值是数字字符串，返回 int 或 float；否则返回原值
        """
        if not isinstance(value, str):
            return value

        # 尝试转换为整数
        try:
            return int(value)
        except ValueError:
            pass

        # 尝试转换为浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 无法转换则返回原值
        return value

    def split_list(
        self, key: str | list[str], separators: str = None, default=None
    ) -> list:
        """获取参数值并按分隔符拆分为列表

        适用于需要将单个输入框的内容拆分为多个元素的场景。
        默认支持的分隔符：中文逗号、英文逗号、斜杠、反斜杠、空格、中文分号、英文分号

        Args:
            key: 参数键名，可以是单个字符串或字符串列表。
                 当传入列表时，按顺序查找，返回第一个命中的值
            separators: 自定义分隔符字符串，为 None 时使用默认分隔符
            default: 默认值，当 key 不存在时返回。
                     若为 None 且未获取到值，则返回空列表 []

        Returns:
            list: 拆分后的列表，已自动过滤空字符串和去除两端空白

        Example:
            >>> # 输入: "角色1,角色2/角色3 角色4"
            >>> args.split_list("invite_list")
            ['角色1', '角色2', '角色3', '角色4']

            >>> # 使用自定义分隔符
            >>> args.split_list("data", separators="|;")
            ['item1', 'item2', 'item3']
        """
        # 获取原始字符串值
        raw_value = self.get(key, default=None)

        # 如果未获取到值，返回默认值
        if raw_value is None:
            return default if default is not None else []

        # 如果已经是列表，直接返回（过滤空值）
        if isinstance(raw_value, list):
            return [str(item).strip() for item in raw_value if str(item).strip()]

        # 转换为字符串
        raw_value = str(raw_value).strip()
        if not raw_value:
            return []

        # 使用默认分隔符或自定义分隔符
        if separators is None:
            separators = "，,\\/ ;；、"  # 中文逗号、英文逗号、斜杠、反斜杠、空格、中文分号、英文分号、中文顿号

        # 构建正则表达式：匹配一个或多个分隔符
        # 特殊字符需要转义
        escaped_separators = re.escape(separators)
        pattern = f"[{escaped_separators}]+"

        # 拆分并过滤空字符串
        result = [item.strip() for item in re.split(pattern, raw_value) if item.strip()]

        return result
