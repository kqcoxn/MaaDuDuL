"""依赖环境自动安装模块。

本模块负责检测项目版本变化，并在必要时自动安装或更新 Python 依赖包。
通过读取 interface.json 中的版本号与本地配置进行比对，
决定是否需要执行 pip install 操作。
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# ====================  路径初始化  ====================

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ====================  全局路径常量  ====================

PIP_CONFIG_PATH = Path("./config/mddl/pip_config.json")


# ====================  配置文件读写  ====================


def _read_interface_version() -> str:
    """读取 interface.json 中的版本号。

    Returns：
        版本号字符串，若文件不存在或读取失败则返回 "unknown"
    """
    interface_path = Path("./interface.json")
    if not interface_path.exists():
        return "unknown"

    try:
        with open(interface_path, "r", encoding="utf-8") as f:
            interface_data = json.load(f)
            return interface_data.get("version", "unknown")
    except Exception:
        return "unknown"


def _read_pip_config() -> dict:
    """读取 pip 安装配置文件。

    若配置文件不存在，则自动创建并使用默认配置。
    默认配置包括：
    - enable_pip_install：是否启用自动安装，默认 True
    - last_version：上次安装时的版本号，默认 "unknown"
    - mirrors：pip 镜像源地址列表，按顺序尝试，失败后用默认源兜底

    Returns：
        包含 pip 配置的字典
    """
    config_dir = Path("./config/mddl")
    config_dir.mkdir(parents=True, exist_ok=True)

    default_config = {
        "enable_pip_install": True,
        "last_version": "unknown",
        "mirrors": [
            "https://pypi.tuna.tsinghua.edu.cn/simple",
            "https://mirrors.ustc.edu.cn/pypi/simple",
            "https://mirrors.aliyun.com/pypi/simple",
        ],
    }

    if not PIP_CONFIG_PATH.exists():
        with open(PIP_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(PIP_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_config


def _update_pip_config(version) -> bool:
    """更新 pip 配置文件中的版本号。

    Args：
        version：要更新的版本号

    Returns：
        更新成功返回 True，失败返回 False
    """
    try:
        config = _read_pip_config()
        config["last_version"] = version

        with open(PIP_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        return False


# ====================  依赖安装  ====================


def _install_requirements(req_file=None, mirrors=None) -> bool:
    """安装 requirements.txt 中列出的依赖包。

    Args：
        req_file：依赖文件路径，默认为 "requirements.txt"
        mirrors：pip 镜像源地址列表，按顺序尝试，最后用默认源兜底

    Returns：
        安装成功返回 True，失败或文件不存在返回 False
    """
    req_path = Path(req_file) if req_file else Path("requirements.txt")
    if not req_path.exists():
        return False

    # 准备镜像源列表，最后添加默认源作为兜底
    mirror_list = []
    if mirrors:
        if isinstance(mirrors, list):
            mirror_list.extend(mirrors)
        else:
            mirror_list.append(mirrors)

    # 默认源兜底（PyPI 官方源）
    mirror_list.append(None)

    # 逐个尝试镜像源
    for idx, mirror in enumerate(mirror_list):
        try:
            if mirror:
                print(
                    f"正在使用镜像源安装或更新环境... ({idx + 1}/{len(mirror_list)}): {mirror}"
                )
            else:
                print(f"正在使用默认源安装或更新环境... ({idx + 1}/{len(mirror_list)})")

            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(req_path),
                "--no-warn-script-location",
            ]

            if mirror:
                cmd.extend(["-i", mirror])

            subprocess.check_call(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print("安装完成！")
            return True
        except Exception as e:
            if idx < len(mirror_list) - 1:
                print(f"当前镜像源失败，尝试下一个...")
                continue
            else:
                print("环境加载失败，请检查网络与环境后重新尝试！")
                return False

    return False


# ====================  主入口函数  ====================


def check_and_install_dependencies():
    """检查并自动安装或更新项目依赖。

    该函数会：
    1、读取当前项目版本号（从 interface.json）
    2、读取上次安装时的版本号（从 pip_config.json）
    3、若版本号不一致或当前版本为 unknown，则执行依赖安装
    4、安装成功后更新配置文件中的版本号

    注意：
    - 可通过修改 config/pip_config.json 中的 enable_pip_install 字段禁用自动安装
    - 可通过修改 mirrors 字段自定义 pip 镜像源列表，支持多个镜像源，按顺序尝试
    - 所有镜像源失败后会自动使用 PyPI 官方默认源兜底
    """
    pip_config = _read_pip_config()
    current_version = _read_interface_version()
    last_version = pip_config.get("last_version", "unknown")
    enable_pip_install = pip_config.get("enable_pip_install", True)
    mirrors = pip_config.get("mirrors", None)

    # 版本不一致时触发依赖安装
    if enable_pip_install and (
        current_version != last_version or current_version == "unknown"
    ):
        if _install_requirements(mirrors=mirrors):
            _update_pip_config(current_version)
