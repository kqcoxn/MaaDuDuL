"""Install the exact MFAA version declared in maa-project.json; never launch it."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import tarfile
import tempfile
from urllib.request import Request, urlopen
import zipfile

from mfaa import ROOT, LOCK, STATE, ensure_gui_stopped, executable, safe_path


def fetch(url):
    return urlopen(Request(url, headers={"User-Agent": "MaaDuDuL-local-installer"}), timeout=120)


def install(workspace: Path) -> None:
    config = json.loads((ROOT / "maa-project.json").read_text(encoding="utf-8"))["runtime"]["mfa"]
    version = config.get("version", "")
    if config.get("enabled") is False or not version.startswith("v") or any(c in version for c in "/\\"):
        raise ValueError("Enable runtime.mfa and specify an exact version in maa-project.json.")
    system = {"Windows": "win", "Linux": "linux", "Darwin": "osx"}.get(platform.system())
    arch = {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine().lower())
    if not system or not arch:
        raise ValueError("Unsupported operating system or CPU architecture.")
    name = f"MFAAvalonia-{version}-{system}-{arch}." + ("zip" if system == "win" else "tar.gz")
    if workspace.resolve() != workspace or workspace == ROOT or ROOT.is_relative_to(workspace):
        raise ValueError("Installation must be a real, separate directory.")
    if workspace.is_relative_to(ROOT) and workspace != ROOT / "MFAAvalonia":
        raise ValueError("Only the repository's MFAAvalonia directory is an allowed in-repository target.")
    if workspace.exists():
        if not workspace.is_dir():
            raise ValueError("Installation target is not a directory.")
        # Existing non-MFAA directories must never be adopted as installations.
        if any(workspace.iterdir()):
            ensure_gui_stopped(executable(workspace))
        if safe_path(workspace, LOCK).exists():
            raise ValueError("MFAA workspace is busy; close the managed GUI first.")
        for path in workspace.rglob("*"):
            safe_path(workspace, path.relative_to(workspace).as_posix())
    workspace.mkdir(parents=True, exist_ok=True)
    lock = safe_path(workspace, LOCK)
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    try:
        with fetch(f"https://api.github.com/repos/MaaXYZ/MFAAvalonia/releases/tags/{version}") as response:
            release = json.load(response)
        asset = next((item for item in release["assets"] if item["name"] == name), None)
        if not asset:
            raise ValueError(f"Release has no asset: {name}")
        expected = asset.get("digest") or ""
        if not expected.startswith("sha256:"):
            raise ValueError("GitHub did not provide a SHA-256 digest; installation cancelled.")
        print(f"Downloading {name} ({asset['size'] / 1024 / 1024:.1f} MiB)...", flush=True)
        with tempfile.TemporaryDirectory(prefix=".mddl-install-", dir=workspace.parent) as temporary:
            temp = Path(temporary)
            archive = temp / name
            digest = hashlib.sha256()
            with fetch(asset["browser_download_url"]) as response, archive.open("wb") as stream:
                while chunk := response.read(1024 * 1024):
                    digest.update(chunk)
                    stream.write(chunk)
            if "sha256:" + digest.hexdigest() != expected or archive.stat().st_size != asset["size"]:
                raise ValueError("Downloaded archive failed integrity verification.")
            unpacked = temp / "unpacked"
            unpacked.mkdir()
            if name.endswith(".zip"):
                with zipfile.ZipFile(archive) as bundle:
                    for entry in bundle.infolist():
                        safe_path(unpacked, entry.filename.rstrip("/"))
                    bundle.extractall(unpacked)
            else:
                with tarfile.open(archive) as bundle:
                    bundle.extractall(unpacked, filter="data")
            payload = unpacked
            entries = list(payload.iterdir())
            if len(entries) == 1 and entries[0].is_dir() and entries[0].suffix != ".app":
                payload = entries[0]
            executable(payload)
            # Reject links rather than risk an archive or existing tree escaping staging.
            for path in payload.rglob("*"):
                safe_path(payload, path.relative_to(payload).as_posix())
            candidate = temp / "candidate"
            shutil.copytree(workspace, candidate)
            protected = {"resource", "tasks", "locales", "agent", "public", "interface.json",
                         "config", "logs", "debug", ".git", ".mddl-runtime.json", LOCK, STATE}
            previous = workspace / ".mddl-runtime.json"
            if previous.is_file():
                for relative in json.loads(previous.read_text(encoding="utf-8")).get("files", []):
                    if Path(relative).parts[0] in protected:
                        continue
                    path = safe_path(candidate, relative)
                    if path.is_file():
                        path.unlink()
            files = []
            for source in payload.rglob("*"):
                relative = source.relative_to(payload).as_posix()
                if source.is_file() and Path(relative).parts[0] not in protected:
                    destination = safe_path(candidate, relative)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    files.append(relative)
            executable(candidate)
            (candidate / STATE).unlink(missing_ok=True)
            (candidate / LOCK).unlink(missing_ok=True)
            (candidate / ".mddl-runtime.json").write_text(json.dumps({
                "version": version, "platform": f"{system}-{arch}",
                "asset": name, "digest": expected, "files": files,
            }, indent=4) + "\n", encoding="utf-8")
            backup_root = ROOT / ".local" / "mfaa-backups" if workspace == ROOT / "MFAAvalonia" else workspace.parent / ".mddl-mfaa-backups"
            if backup_root.resolve() != backup_root:
                raise ValueError("Backup directory must not use symbolic links or junctions.")
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (workspace.name + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
            # Same-volume renames; keep the previous installation for manual rollback.
            if any((workspace / name).exists() for name in ("MFAAvalonia.exe", "MFAAvalonia", "MFAAvalonia.app")):
                ensure_gui_stopped(executable(workspace))
            workspace.rename(backup)
            try:
                candidate.rename(workspace)
            except OSError:
                backup.rename(workspace)
                raise
            (backup / LOCK).unlink(missing_ok=True)
            print(f"Installed {version}: {workspace}\nPrevious installation: {backup}\nNext: yarn dev:prepare")
    finally:
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=os.environ.get("MDDL_MFAA_ROOT", str(ROOT / "MFAAvalonia")))
    args = parser.parse_args()
    try:
        install(Path(args.workspace).absolute())
        return 0
    except (OSError, ValueError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Installation failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
