"""Replace the core's bundled Maa binding with the project's pinned source binding.

MaaFwApp keeps core-provided packages even when requirements pin another version.
Keep its CPython/native dependencies, but replace maa completely to avoid mixed APIs.
"""

import argparse
import ast
import json
import zipfile
from pathlib import Path


def align_binding(bundle: Path, source: Path, version: str, python_version: str) -> None:
    manifest_path = bundle / "agent-core.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["python"] != python_version:
        raise ValueError(f"Unexpected core Python: {manifest['python']}")
    if any(bundle.rglob("libMaa*.so")):
        raise ValueError("Core contains native Maa libraries; review before mixing runtime versions")
    site = bundle / "site-packages"
    if (site / "maa").exists():
        raise ValueError("Expected upstream to pack the pure-Python maa package into pure.zip")
    files = {f"maa/{path.relative_to(source).as_posix()}": path.read_bytes() for path in source.rglob("*.py")}
    if "maa/agent/agent_server.py" not in files:
        raise ValueError(f"MaaFramework Python binding missing: {source}")
    # CPython 3.13 reports Android rather than Linux (PEP 738). Match the core's
    # platform adaptation without altering platform.system() process-wide.
    library = files["maa/library.py"].decode("utf-8")
    marker = "        platform_type = platform.system().lower()\n"
    if library.count(marker) != 1:
        raise ValueError("Maa binding loader changed; review its Android platform handling")
    library = library.replace(
        marker, marker + '        if platform_type == "android":\n            platform_type = LINUX\n'
    )
    ast.parse(library)
    files["maa/library.py"] = library.encode("utf-8")
    archive = site / "pure.zip"
    staged = archive.with_suffix(".tmp.zip")
    with zipfile.ZipFile(archive) as old, zipfile.ZipFile(staged, "w", zipfile.ZIP_DEFLATED) as new:
        if "maa/library.py" not in old.namelist():
            raise ValueError("Core layout changed: maa/library.py not present in pure.zip")
        for entry in old.infolist():
            top = entry.filename.split("/", 1)[0].lower()
            if top == "maa" or (top.startswith("maafw-") and top.endswith(".dist-info")):
                continue
            new.writestr(entry, old.read(entry))
        for name, content in files.items():
            new.writestr(name, content)
        new.writestr(f"maafw-{version}.dist-info/METADATA", f"Metadata-Version: 2.1\nName: MaaFw\nVersion: {version}\n")
    staged.replace(archive)
    manifest["provides"]["maafw"] = version
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Aligned {manifest['abi']} Python binding to MaaFramework {version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundles", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.manifest.read_text(encoding="utf-8"))
    for abi in ("arm64-v8a", "x86_64"):
        align_binding(
            args.bundles / abi / "bundle",
            args.source,
            config["maafw"]["version"],
            config["maintenance"]["android"]["agentPython"],
        )
