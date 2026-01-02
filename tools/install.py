from pathlib import Path

import shutil
import sys
import platform

try:
    import jsonc
except ModuleNotFoundError as e:
    raise ImportError(
        "Missing dependency 'json-with-comments' (imported as 'jsonc').\n"
        f"Install it with:\n  {sys.executable} -m pip install json-with-comments\n"
        "Or add it to your project's requirements."
    ) from e

from configure import configure_ocr_model


working_dir = Path(__file__).parent.parent.resolve()
install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"
# 从命令行参数获取目标平台，如果没有提供则使用当前系统平台
target_os = len(sys.argv) > 2 and sys.argv[2] or platform.system().lower()


# # 下载 MaaFramework
# def install_deps():
#     if not (working_dir / "deps" / "bin").exists():
#         print("Please download the MaaFramework to \"deps\" first.")
#         print("请先下载 MaaFramework 到 \"deps\"。")
#         sys.exit(1)

#     shutil.copytree(
#         working_dir / "deps" / "bin",
#         install_path,
#         ignore=shutil.ignore_patterns(
#             "*MaaDbgControlUnit*",
#             "*MaaThriftControlUnit*",
#             "*MaaRpc*",
#             "*MaaHttp*",
#         ),
#         dirs_exist_ok=True,
#     )
#     shutil.copytree(
#         working_dir / "deps" / "share" / "MaaAgentBinary",
#         install_path / "MaaAgentBinary",
#         dirs_exist_ok=True,
#     )


def install_resource():

    configure_ocr_model()

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        working_dir / "assets" / "interface.json",
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = jsonc.load(f)

    interface["version"] = version

    # 根据目标平台设置Python路径
    if target_os in ["darwin", "macos", "linux"]:
        # macOS和Linux使用python/bin/python
        interface["agent"]["child_exec"] = "./python/bin/python"
    else:
        # Windows使用python/python.exe
        interface["agent"]["child_exec"] = "./python/python.exe"

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        jsonc.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(
        working_dir / "README.md",
        install_path,
    )
    shutil.copy2(
        working_dir / "LICENSE",
        install_path,
    )
    # 复制requirements.txt供用户手动更新依赖
    if (working_dir / "requirements.txt").exists():
        shutil.copy2(
            working_dir / "requirements.txt",
            install_path,
        )


def install_config():
    """安装config和descs配置文件夹"""
    # 创建install目录（如果不存在）
    install_path.mkdir(parents=True, exist_ok=True)

    # 复制config文件夹
    if (working_dir / "ci" / "config").exists():
        shutil.copytree(
            working_dir / "ci" / "config",
            install_path / "config",
            dirs_exist_ok=True,
        )


def install_agent():
    """安装agent代码，但排除config目录（已在install_config中处理）"""
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        ignore=shutil.ignore_patterns("config"),  # 排除agent/config，使用根目录的config
        dirs_exist_ok=True,
    )


if __name__ == "__main__":
    # install_deps()
    install_resource()
    install_chores()
    install_agent()
    install_config()

    print(f"Install to {install_path} successfully.")
