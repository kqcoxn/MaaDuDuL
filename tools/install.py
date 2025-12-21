from pathlib import Path

import shutil
import sys

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


def install_config():
    """安装config和descs配置文件夹"""
    # 创建install目录（如果不存在）
    install_path.mkdir(parents=True, exist_ok=True)

    # 复制config文件夹
    if (working_dir / "config").exists():
        shutil.copytree(
            working_dir / "config",
            install_path / "config",
            dirs_exist_ok=True,
        )

    # 复制descs文件夹
    if (working_dir / "descs").exists():
        shutil.copytree(
            working_dir / "descs",
            install_path / "descs",
            dirs_exist_ok=True,
        )


def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )


if __name__ == "__main__":
    # install_deps()
    install_resource()
    install_chores()
    install_agent()
    install_config()

    print(f"Install to {install_path} successfully.")
