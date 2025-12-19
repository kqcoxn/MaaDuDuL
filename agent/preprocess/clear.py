"""预处理清理模块。

本模块负责在任务执行前清理调试产生的临时文件。
"""

import shutil
from pathlib import Path


def _clear_on_error_images():
    """清理错误时产生的调试图片。

    删除 debug/on_error 目录及其所有内容。
    该目录用于存储任务执行出错时的截图，清理可避免历史图片占用空间。
    """
    # 获取项目根目录（当前文件的上两级目录）
    root = Path(__file__).resolve().parent.parent

    # 构建调试图片文件夹路径
    on_error_folder = root / "debug" / "on_error"

    # 如果文件夹存在则删除整个目录树
    if on_error_folder.exists():
        try:
            shutil.rmtree(on_error_folder)
        except Exception:
            # 删除失败时静默处理，避免中断预处理流程
            pass


def clear():
    """执行预处理清理操作。

    该函数是清理模块的对外接口，负责调用所有内部清理函数。
    即使清理过程出错也不会中断程序，仅输出提示信息。
    """
    try:
        _clear_on_error_images()
    except Exception as e:
        print(f"info:预处理时出现问题：\n{e}\n这可能不影响使用，但建议在交流群内反馈！")
