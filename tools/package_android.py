"""Stage MaaDuDuL resources for MaaFwApp without modifying development resources."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def stage(version: str) -> Path:
    manifest = json.loads((ROOT / "maa-project.json").read_text(encoding="utf-8"))
    target = ROOT / "install"
    if target.exists():
        raise FileExistsError("install/ already exists; use a fresh checkout for Android packaging")
    target.mkdir()
    for directory in ("tasks", "resource", "locales", "agent"):
        ignored = ["__pycache__", "*.pyc"] + (["config"] if directory == "agent" else [])
        shutil.copytree(ROOT / directory, target / directory, ignore=shutil.ignore_patterns(*ignored))
    shutil.copytree(ROOT / "tools/ci/config", target / "config")
    (target / "public").mkdir()
    shutil.copy2(ROOT / "public/logo.png", target / "public/logo.png")
    for filename in ("LICENSE", "README.md"):
        shutil.copy2(ROOT / filename, target / filename)

    interface = json.loads((ROOT / "interface.json").read_text(encoding="utf-8"))
    interface["version"] = version
    # MaaFwApp takes the actual executable/args from pi-profile.yaml. Preserve
    # the project's agent declaration and desktop command in the source file.
    (target / "interface.json").write_text(json.dumps(interface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    ocr = manifest["ocr"]
    model_dir = target / "resource/base/model/ocr"
    model_dir.mkdir(parents=True, exist_ok=True)
    for filename, source in ocr["files"].items():
        shutil.copy2(ROOT / ocr["submodulePath"] / source, model_dir / filename)
    print(f"Android resources staged at {target}")
    return target


if __name__ == "__main__":
    stage(sys.argv[1])
