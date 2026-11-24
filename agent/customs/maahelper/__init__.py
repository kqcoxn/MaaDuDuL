from .tasker import Tasker
from .reco_helper import RecoHelper
from .argv_analyzer import ParamAnalyzer

# 初始化内置繁中处理器，供运行时识别文本转换使用。
from . import zh_hant as zh_hant
