from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition, RecognitionResult, RectType
from maa.context import Context
from maa.controller import Controller

import time


def cprint(content: str = "", interval: int = 0.1):
    interval /= 2
    time.sleep(interval)
    print("info:" + content)
    time.sleep(interval)


class Prompter:
    @staticmethod
    def log(
        content: str = "",
        is_continuous=False,
        use_default_prefix=True,
        use_pre_devider=False,
        use_post_devider=False,
    ):
        if use_default_prefix and not (use_pre_devider or use_post_devider):
            content = f" > {content}"
        if use_pre_devider:
            cprint("——" * 5)
        cprint(content) if is_continuous else print("info:" + content)
        if use_post_devider:
            cprint("——" * 5)

    @staticmethod
    def error(
        content: str,
        e: Exception = None,
        reco_detail=None,
        use_defult_postfix=True,
    ):
        if use_defult_postfix:
            content += "失败，请立即停止运行程序！"
        cprint("——" * 5)
        cprint(f"{content}")
        if e is not None:
            cprint("错误详情：")
            cprint(f"{e}")
        cprint("——" * 5)
        return (
            False
            if reco_detail == None
            else CustomRecognition.AnalyzeResult(
                box=None, detail={} if reco_detail == True else reco_detail
            )
        )
