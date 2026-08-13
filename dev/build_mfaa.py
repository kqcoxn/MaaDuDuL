import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import jsonc

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MFAA_ROOT = PROJECT_ROOT / "MFAAvalonia"
MFAA_RESOURCE_ROOT = MFAA_ROOT / "resource"
os.chdir(PROJECT_ROOT)


def _get_mfaa_executable() -> Path:
    """Return the MFAAvalonia executable for the current platform."""
    if platform.system() == "Windows":
        candidates = [MFAA_ROOT / "MFAAvalonia.exe"]
    else:
        candidates = [
            MFAA_ROOT / "MFAAvalonia",
            MFAA_ROOT / "MFAAvalonia.app" / "Contents" / "MacOS" / "MFAAvalonia",
        ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    expected = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"找不到 MFAAvalonia 可执行文件，已检查: {expected}")


def copy_files():
    try:
        # 先确认启动目标，避免路径错误时清理测试目录
        mfaa_executable = _get_mfaa_executable()

        # 确保目标目录存在
        MFAA_RESOURCE_ROOT.mkdir(parents=True, exist_ok=True)

        # 先删除目标目录中的现有文件
        if os.path.exists("MFAAvalonia/interface.json"):
            os.remove("MFAAvalonia/interface.json")

        # 清空 resource 目录
        if MFAA_RESOURCE_ROOT.exists():
            for item in os.listdir(MFAA_RESOURCE_ROOT):
                item_path = MFAA_RESOURCE_ROOT / item
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        # 删除debug目录
        if os.path.exists("MFAAvalonia/debug"):
            shutil.rmtree("MFAAvalonia/debug")

        # 删除logs目录
        if os.path.exists("MFAAvalonia/logs"):
            shutil.rmtree("MFAAvalonia/logs")

        # 删除agent目录
        if os.path.exists("MFAAvalonia/agent"):
            shutil.rmtree("MFAAvalonia/agent")

        # 删除locales目录
        if os.path.exists("MFAAvalonia/locales"):
            shutil.rmtree("MFAAvalonia/locales")

        # 删除 resource 中的 descs 目录
        if (MFAA_RESOURCE_ROOT / "descs").exists():
            shutil.rmtree(MFAA_RESOURCE_ROOT / "descs")

        # 复制interface.json并使用当前运行此脚本的Python
        interface_path = PROJECT_ROOT / "assets" / "interface.json"
        if interface_path.exists():
            with interface_path.open("r", encoding="utf-8") as f:
                interface_data = jsonc.load(f)

            # 使用绝对路径，避免 macOS 的 python/python3 命令差异
            if "agent" in interface_data:
                interface_data["agent"]["child_exec"] = str(
                    Path(sys.executable).resolve()
                )

            with (MFAA_ROOT / "interface.json").open("w", encoding="utf-8") as f:
                jsonc.dump(interface_data, f, ensure_ascii=False, indent=4)
        else:
            print("警告: assets/interface.json 不存在")

        # 复制locales文件夹，使interface.json中的相对路径在MFAA环境中可用
        if os.path.exists("assets/locales"):
            shutil.copytree("assets/locales", "MFAAvalonia/locales", dirs_exist_ok=True)
        else:
            print("警告: assets/locales 文件夹不存在")

        # 复制resource文件夹内容
        if os.path.exists("assets/resource"):
            for item in os.listdir("assets/resource"):
                src = os.path.join("assets/resource", item)
                dst = MFAA_RESOURCE_ROOT / item
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        else:
            print("警告: assets/resource 文件夹不存在")

        # 复制agent文件夹
        if os.path.exists("agent"):
            shutil.copytree("agent", "MFAAvalonia/agent", dirs_exist_ok=True)
        else:
            print("警告: agent 文件夹不存在")

        # 复制 descs 文件夹到 resource 目录下
        if os.path.exists("assets/resource/descs"):
            shutil.copytree(
                "assets/resource/descs",
                MFAA_RESOURCE_ROOT / "descs",
                dirs_exist_ok=True,
            )
        else:
            print("警告: assets/resource/descs 文件夹不存在")

        # 以开发模式启动 MFAAvalonia，Agent 会继承该环境变量
        env = os.environ.copy()
        env["MDDL_DEV_MODE"] = "1"
        subprocess.Popen(
            [str(mfaa_executable)],
            cwd=str(MFAA_ROOT),
            env=env,
        )
        print(f"MFAAvalonia 程序构建成功！（开发模式）{mfaa_executable.name}")

    except Exception as e:
        print(f"发生错误: {e}")
        raise


if __name__ == "__main__":
    copy_files()
