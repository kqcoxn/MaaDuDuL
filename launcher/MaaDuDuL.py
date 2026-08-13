# pyinstaller --onefile --icon=../public/logo.ico --windowed MaaDuDuL.py

import platform
import subprocess
import sys
from pathlib import Path


def _get_install_roots() -> list[Path]:
    """Return likely install roots for source and PyInstaller execution."""
    if getattr(sys, "frozen", False):
        return [Path(sys.executable).resolve().parent]
    return [Path.cwd(), Path(__file__).resolve().parent.parent]


def _get_mfaa_path() -> Path:
    if platform.system() == "Windows":
        executable_names = ["MFAAvalonia.exe"]
    elif platform.system() in {"Darwin", "Linux"}:
        executable_names = [
            "MFAAvalonia",
            "MFAAvalonia.app/Contents/MacOS/MFAAvalonia",
        ]
    else:
        raise RuntimeError(f"不支持的操作系统: {platform.system()}")

    for root in _get_install_roots():
        for executable_name in executable_names:
            direct_path = root / executable_name
            nested_path = root / "MFAAvalonia" / executable_name
            if direct_path.is_file():
                return direct_path
            if nested_path.is_file():
                return nested_path

    raise FileNotFoundError("找不到 MFAAvalonia 可执行文件，请确认它与启动器位于同一目录")


def _get_mfaa_working_directory(mfaa_path: Path) -> Path:
    """Keep interface.json as the working-directory anchor for MFAAvalonia."""
    for parent in mfaa_path.parents:
        if (parent / "interface.json").is_file():
            return parent
    return mfaa_path.parent


if __name__ == "__main__":
    mfaa_path = _get_mfaa_path()
    subprocess.run(
        [str(mfaa_path)],
        cwd=str(_get_mfaa_working_directory(mfaa_path)),
        check=True,
    )
