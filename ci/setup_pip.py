# -*- coding: utf-8 -*-
"""
安装pip和依赖库的脚本

该脚本用于嵌入式Python环境中，执行以下操作:
1. 下载并安装pip
"""

import os
import sys
import urllib.request
import subprocess


def install_pip():
    """下载并安装pip到嵌入式Python环境"""
    print("Setting up pip...")

    # pip安装脚本的官方下载地址
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    # 将下载的脚本保存到当前目录
    get_pip_path = os.path.join(os.path.dirname(__file__), "get-pip.py")

    # 下载get-pip.py脚本
    print(f"Downloading {get_pip_url}...")
    urllib.request.urlretrieve(get_pip_url, get_pip_path)

    # 执行pip安装脚本（--no-warn-script-location 抑制脚本位置警告）
    print("Install pip...")
    subprocess.check_call([sys.executable, get_pip_path, "--no-warn-script-location"])

    # 删除临时下载的安装脚本
    os.unlink(get_pip_path)

    print("pip installed.")


if __name__ == "__main__":
    install_pip()
