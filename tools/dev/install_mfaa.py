"""Install manifest-pinned MFAA and MaaFramework together; never launch the GUI."""

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from mfaa import LOCK, ROOT, STATE, ensure_gui_stopped, executable, framework_version, runtime_platform, safe_path


def fetch(url):
    request = Request(url, headers={"User-Agent": "MaaDuDuL-local-installer"})
    if urlsplit(url).scheme == "https" and urlsplit(url).netloc == "api.github.com":
        request.add_header("Accept", "application/vnd.github+json")
        token = os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            # Do not forward credentials to download hosts or through redirects.
            request.add_unredirected_header("Authorization", f"Bearer {token}")
    return urlopen(request, timeout=120)


class ReleaseAssetParser(HTMLParser):
    """Match the download link and digest inside the same release asset row."""

    def __init__(self, download_path: str):
        super().__init__()
        self.download_path = download_path
        self.rows = []
        self.matches = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "li":
            self.rows.append({"matched": False, "digests": []})
        if not self.rows:
            return
        if tag == "a" and attributes.get("href") == self.download_path:
            self.rows[-1]["matched"] = True
        if tag == "clipboard-copy":
            self.rows[-1]["digests"].append(attributes.get("value", ""))

    def handle_endtag(self, tag):
        if tag == "li" and self.rows:
            row = self.rows.pop()
            if row["matched"]:
                self.matches.append(row["digests"])


def resolve_asset(version: str, name: str, repository: str = "MaaXYZ/MFAAvalonia") -> dict:
    tag = quote(version, safe="")
    try:
        with fetch(f"https://api.github.com/repos/{repository}/releases/tags/{tag}") as response:
            release = json.load(response)
    except HTTPError as error:
        if error.code not in (403, 429):
            raise
        body = error.read(65536).decode("utf-8", errors="replace").lower()
        limited = (
            error.code == 429
            or error.headers.get("X-RateLimit-Remaining") == "0"
            or "rate limit" in body
        )
        if not limited:
            raise
        print("GitHub API rate limit reached; reading the official release asset page.", flush=True)
        download_path = f"/{repository}/releases/download/{tag}/{quote(name, safe='')}"
        parser = ReleaseAssetParser(download_path)
        with fetch(f"https://github.com/{repository}/releases/expanded_assets/{tag}") as response:
            parser.feed(response.read().decode("utf-8"))
        parser.close()
        if len(parser.matches) != 1 or len(parser.matches[0]) != 1:
            raise ValueError(
                f"Cannot identify a unique SHA-256 for {name} on the official release page. "
                "Set GH_TOKEN or GITHUB_TOKEN, or retry after the API rate limit resets."
            ) from error
        asset = {
            "name": name,
            "browser_download_url": "https://github.com" + download_path,
            "digest": parser.matches[0][0],
            # The page only displays rounded sizes; do not treat them as exact bytes.
            "size": None,
        }
    else:
        asset = next((item for item in release["assets"] if item["name"] == name), None)
        if not asset:
            raise ValueError(f"Release has no asset: {name}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", asset.get("digest") or ""):
        raise ValueError("GitHub did not provide a valid SHA-256 digest; installation cancelled.")
    return asset


def download_asset(asset: dict, directory: Path) -> Path:
    name = asset["name"]
    archive = safe_path(directory, name)
    size = asset.get("size")
    size_label = f" ({size / 1024 / 1024:.1f} MiB)" if size is not None else ""
    print(f"Downloading {name}{size_label}...", flush=True)
    digest = hashlib.sha256()
    with fetch(asset["browser_download_url"]) as response, archive.open("wb") as stream:
        if size is None and response.headers.get("Content-Length"):
            size = int(response.headers["Content-Length"])
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            stream.write(chunk)
    if "sha256:" + digest.hexdigest() != asset["digest"] or (size is not None and archive.stat().st_size != size):
        raise ValueError(f"Downloaded archive failed integrity verification: {name}")
    return archive


def overlay_framework(archive: Path, candidate: Path, rid: str) -> list[str]:
    """Apply the same bin/plugins/share layout used by the desktop release packager."""
    roots = (f"runtimes/{rid}/native", f"plugins/{rid}", "libs/MaaAgentBinary")
    with zipfile.ZipFile(archive) as bundle:
        entries = [entry for entry in bundle.infolist() if not entry.is_dir()]
        # Official archives may have one wrapping directory.
        top = {entry.filename.split("/")[0] for entry in entries}
        strip_root = len(top) == 1 and not top.intersection({"bin", "lib", "plugins", "share", "include"})
        mapped = {}
        for entry in entries:
            safe_path(candidate, entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Linked runtime archive entry is not supported: {entry.filename}")
            relative = entry.filename.split("/", 1)[-1] if strip_root else entry.filename
            if relative.startswith("bin/plugins/"):
                target = f"plugins/{rid}/" + relative[len("bin/plugins/"):]
            elif relative.startswith("bin/"):
                target = f"runtimes/{rid}/native/" + relative[len("bin/"):]
            elif relative.startswith(("lib/", "plugins/")):
                target = f"plugins/{rid}/" + relative.split("/", 1)[1]
            elif relative.startswith("share/MaaAgentBinary/"):
                target = "libs/MaaAgentBinary/" + relative[len("share/MaaAgentBinary/"):]
            else:
                continue
            safe_path(candidate, target)
            if target in mapped:
                raise ValueError(f"Duplicate runtime archive target: {target}")
            mapped[target] = entry
        prefix, suffix = (
            ("", ".dll") if rid.startswith("win-") else ("lib", ".dylib" if rid.startswith("osx-") else ".so")
        )
        for name in ("MaaFramework", "MaaAgentClient", "MaaAgentServer", "MaaToolkit"):
            if f"runtimes/{rid}/native/{prefix}{name}{suffix}" not in mapped:
                raise ValueError(f"Framework archive is missing {name} for {rid}.")
        # Only replace runtime-owned files in the isolated candidate, never live files.
        old_files = []
        for root in roots:
            for path in safe_path(candidate, root).rglob("*"):
                safe_path(candidate, path.relative_to(candidate).as_posix())
                if path.is_file():
                    old_files.append(path)
        for path in old_files:
            path.unlink()
        for target, entry in mapped.items():
            destination = safe_path(candidate, target)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(entry) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
            mode = (entry.external_attr >> 16) & 0o777
            if mode:
                destination.chmod(mode)
    return sorted(mapped)


def install(workspace: Path, framework_only: bool = False) -> None:
    project = json.loads((ROOT / "maa-project.json").read_text(encoding="utf-8"))
    config = project["runtime"]["mfa"]
    version = config.get("version", "")
    if config.get("enabled") is False or not version.startswith("v") or any(c in version for c in "/\\"):
        raise ValueError("Enable runtime.mfa and specify an exact version in maa-project.json.")
    rid = runtime_platform()
    system, arch = rid.split("-")
    maafw_version = project["maafw"]["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", maafw_version):
        raise ValueError("Specify an exact maafw.version in maa-project.json.")
    name = f"MFAAvalonia-{version}-{system}-{arch}." + ("zip" if system == "win" else "tar.gz")
    if workspace.resolve() != workspace or workspace == ROOT or ROOT.is_relative_to(workspace):
        raise ValueError("Installation must be a real, separate directory.")
    if workspace.is_relative_to(ROOT) and workspace != ROOT / "MFAAvalonia":
        raise ValueError("Only the repository's MFAAvalonia directory is an allowed in-repository target.")
    if framework_only:
        executable(workspace)
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
        asset = None if framework_only else resolve_asset(version, name)
        framework_system = "macos" if system == "osx" else system
        framework_arch = "aarch64" if arch == "arm64" else "x86_64"
        framework_name = f"MAA-{framework_system}-{framework_arch}-v{maafw_version}.zip"
        framework_asset = resolve_asset(f"v{maafw_version}", framework_name, "MaaXYZ/MaaFramework")
        with tempfile.TemporaryDirectory(prefix=".mddl-install-", dir=workspace.parent) as temporary:
            temp = Path(temporary)
            archive = download_asset(asset, temp) if asset else None
            framework_archive = download_asset(framework_asset, temp)
            unpacked = temp / "unpacked"
            unpacked.mkdir()
            if archive and name.endswith(".zip"):
                with zipfile.ZipFile(archive) as bundle:
                    for entry in bundle.infolist():
                        safe_path(unpacked, entry.filename.rstrip("/"))
                    bundle.extractall(unpacked)
            elif archive:
                with tarfile.open(archive) as bundle:
                    bundle.extractall(unpacked, filter="data")
            payload = unpacked
            entries = list(payload.iterdir())
            if len(entries) == 1 and entries[0].is_dir() and entries[0].suffix != ".app":
                payload = entries[0]
            if not framework_only:
                executable(payload)
            # Reject links rather than risk an archive or existing tree escaping staging.
            for path in payload.rglob("*"):
                safe_path(payload, path.relative_to(payload).as_posix())
            candidate = temp / "candidate"
            shutil.copytree(workspace, candidate)
            protected = {"resource", "tasks", "locales", "agent", "public", "interface.json",
                         "config", "logs", "debug", ".git", ".mddl-runtime.json", LOCK, STATE}
            previous = workspace / ".mddl-runtime.json"
            record = json.loads(previous.read_text(encoding="utf-8")) if previous.is_file() else {}
            if not framework_only:
                for relative in record.get("files", []):
                    if Path(relative).parts[0] in protected:
                        continue
                    path = safe_path(candidate, relative)
                    if path.is_file():
                        path.unlink()
            files = list(record.get("files", [])) if framework_only else []
            for source in payload.rglob("*"):
                relative = source.relative_to(payload).as_posix()
                if source.is_file() and Path(relative).parts[0] not in protected:
                    destination = safe_path(candidate, relative)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                    files.append(relative)
            framework_files = overlay_framework(framework_archive, candidate, rid)
            actual = framework_version(candidate)
            if actual != maafw_version:
                raise ValueError(f"Staged MaaFramework is {actual}; expected {maafw_version}. Installation cancelled.")
            print(f"Verified staged MaaFramework: {actual}", flush=True)
            files = [relative for relative in files if (candidate / relative).is_file()]
            files = sorted(set(files + framework_files))
            executable(candidate)
            (candidate / STATE).unlink(missing_ok=True)
            (candidate / LOCK).unlink(missing_ok=True)
            if asset:
                record.update(version=version, asset=name, digest=asset["digest"])
            record.update(platform=rid, files=files, maafw={
                "version": actual, "asset": framework_name, "digest": framework_asset["digest"],
            })
            (candidate / ".mddl-runtime.json").write_text(json.dumps(record, indent=4) + "\n", encoding="utf-8")
            backup_root = (
                ROOT / ".local" / "mfaa-backups"
                if workspace == ROOT / "MFAAvalonia" else workspace.parent / ".mddl-mfaa-backups"
            )
            if backup_root.resolve() != backup_root:
                raise ValueError("Backup directory must not use symbolic links or junctions.")
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (workspace.name + "-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
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
            installed = f"MaaFramework {actual}" if framework_only else f"MFAA {version} + MaaFramework {actual}"
            print(f"Installed {installed}: {workspace}\nPrevious installation: {backup}\nNext: yarn dev:prepare")
    finally:
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=os.environ.get("MDDL_MFAA_ROOT", str(ROOT / "MFAAvalonia")))
    parser.add_argument(
        "--framework-only", action="store_true",
        help="Align MaaFramework in an existing MFAA installation without downloading the GUI.",
    )
    args = parser.parse_args()
    try:
        install(Path(args.workspace).absolute(), framework_only=args.framework_only)
        return 0
    except (OSError, ValueError, KeyError, tarfile.TarError, zipfile.BadZipFile) as error:
        print(f"Installation failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
