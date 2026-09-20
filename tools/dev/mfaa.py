"""Explicit preparation and launch of the local MFAA workspace.

No operation runs on import. All mutations are limited to the owned payload;
GUI binaries, configuration, logs and screenshots are never cleaned here.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
STATE = ".mddl-dev.json"
LOCK = ".mddl-dev.lock"
TREES = ("resource", "tasks", "locales", "agent")
EXCLUDED = {"__pycache__", "config", "debug", "logs", ".git"}


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Unsafe workspace path: {relative}")
    if not path.resolve().is_relative_to(root) or path == root:
        raise ValueError(f"Path escapes workspace: {path}")
    for item in (path, *path.parents):
        if item == root:
            break
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError(f"Linked workspace paths are not supported: {item}")
    return path


def inventory(root: Path) -> dict[str, Path]:
    found = {}
    for tree in TREES:
        base = safe_path(root, tree)
        if not base.exists():
            continue
        for directory, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [name for name in dirs if name not in EXCLUDED]
            for name in dirs:
                safe_path(root, (Path(directory) / name).relative_to(root).as_posix())
            for name in files:
                if name.endswith((".pyc", ".pyo")):
                    continue
                relative = (Path(directory) / name).relative_to(root).as_posix()
                found[relative] = safe_path(root, relative)
    for relative in ("interface.json", "public/logo.png"):
        path = safe_path(root, relative)
        if path.is_file():
            found[relative] = path
    return found


def digest(files: dict[str, Path]) -> str:
    result = hashlib.sha256()
    for name, path in sorted(files.items()):
        result.update(name.encode())
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".mddl-")
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def executable(workspace: Path) -> Path:
    names = ("MFAAvalonia.exe",) if sys.platform == "win32" else (
        "MFAAvalonia", "MFAAvalonia.app/Contents/MacOS/MFAAvalonia",
    )
    for name in names:
        path = workspace / name
        if path.is_file():
            return path
    raise ValueError(f"MFAA executable missing in {workspace}")


def ensure_gui_stopped(gui: Path) -> None:
    """Also detect GUIs opened outside the managed launcher."""
    if sys.platform == "win32":
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "@(Get-Process | Where-Object ProcessName -eq MFAAvalonia | "
             "Select-Object Id,Path) | ConvertTo-Json -Compress"],
            capture_output=True, text=True, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode:
            raise ValueError("Cannot inspect running MFAA processes; preparation cancelled.")
        processes = json.loads(result.stdout.strip() or "[]")
        if isinstance(processes, dict):
            processes = [processes]
        # Missing path may mean an elevated process that cannot be inspected.
        running = any(
            not item.get("Path") or os.path.normcase(item["Path"]) == os.path.normcase(str(gui))
            for item in processes
        )
    else:
        result = subprocess.run(["ps", "-ax", "-o", "comm="], capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError("Cannot inspect running MFAA processes; preparation cancelled.")
        running = any(Path(line.strip()).name == gui.name for line in result.stdout.splitlines())
    if running:
        raise ValueError("MFAA is running. Close the GUI and its Agent before preparing or starting another session.")


def prepare(workspace: Path) -> None:
    import jsonc

    sources = inventory(ROOT)
    source_digest = digest(sources)
    for name in (*TREES, "interface.json", "public/logo.png"):
        if not (ROOT / name).exists():
            raise ValueError(f"Missing source: {name}")
    # Validate all destinations before the first write, including junctions.
    old = inventory(workspace)
    for name in sources:
        safe_path(workspace, name)
    interface = jsonc.loads(sources["interface.json"].read_text(encoding="utf-8"))
    agents = interface["agent"]
    for agent in agents if isinstance(agents, list) else [agents]:
        agent["child_exec"] = os.path.abspath(sys.executable)
        agent["child_args"] = ["-u", "agent/main.py"]
    generated = json.dumps(interface, ensure_ascii=False, indent=4).encode("utf-8") + b"\n"
    state_path = safe_path(workspace, STATE)
    # A partial preparation cannot subsequently be mistaken for a ready workspace.
    state_path.unlink(missing_ok=True)
    for name, path in sources.items():
        data = generated if name == "interface.json" else path.read_bytes()
        target = safe_path(workspace, name)
        if not target.is_file() or target.read_bytes() != data:
            write_atomic(target, data)
    for name in old.keys() - sources.keys():
        safe_path(workspace, name).unlink()
    # Preserve empty resource overlays as well as file-containing directories.
    for tree in TREES:
        for directory, dirs, _ in os.walk(ROOT / tree):
            dirs[:] = [name for name in dirs if name not in EXCLUDED]
            relative = Path(directory).relative_to(ROOT).as_posix()
            safe_path(workspace, relative).mkdir(parents=True, exist_ok=True)
    if digest(inventory(ROOT)) != source_digest:
        raise ValueError("Source changed during preparation; run yarn dev:prepare again.")
    state = {
        "source": str(ROOT), "python": os.path.abspath(sys.executable),
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "source_digest": source_digest, "payload_digest": digest(inventory(workspace)),
    }
    write_atomic(state_path, (json.dumps(state, ensure_ascii=False, indent=4) + "\n").encode())
    print(f"Prepared: {workspace}\nPython: {state['python']}\nLogs and configuration preserved.")


def status(workspace: Path) -> bool:
    state_path = safe_path(workspace, STATE)
    print(f"Source: {ROOT}\nWorkspace: {workspace}\nPython: {os.path.abspath(sys.executable)}")
    if not state_path.is_file():
        print("Not prepared (or preparation was interrupted). Run yarn dev:prepare.")
        return False
    state = json.loads(state_path.read_text(encoding="utf-8"))
    ready = (
        state.get("source") == str(ROOT)
        and state.get("python") == os.path.abspath(sys.executable)
        and state.get("source_digest") == digest(inventory(ROOT))
        and state.get("payload_digest") == digest(inventory(workspace))
    )
    print(f"Prepared at: {state.get('prepared_at')}\nState: {'ready' if ready else 'stale; run yarn dev:prepare'}")
    return ready


def main(arguments=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "start", "status"))
    parser.add_argument("--workspace", default=os.environ.get("MDDL_MFAA_ROOT", str(ROOT / "MFAAvalonia")))
    args = parser.parse_args(arguments)
    workspace = Path(args.workspace).absolute()
    try:
        # Reject aliases of source directories before considering any mutation.
        if workspace.resolve() != workspace or workspace == ROOT or ROOT.is_relative_to(workspace):
            raise ValueError("Workspace must be a real, separate MFAA installation directory.")
        if workspace.is_relative_to(ROOT) and workspace.parts[len(ROOT.parts)] != "MFAAvalonia":
            raise ValueError("Inside this repository only MFAAvalonia is a permitted workspace.")
        if args.command == "status":
            ready = status(workspace)
            print(f"Management lock: {safe_path(workspace, LOCK).exists()}")
            return 0 if ready else 1
        gui = executable(workspace)
        ensure_gui_stopped(gui)
        lock = safe_path(workspace, LOCK)
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError(f"Workspace busy: {lock}. Close the managed GUI first. If interrupted, verify no GUI/Agent is running before removing this lock.") from None
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(str(os.getpid()))
            if args.command == "prepare":
                prepare(workspace)
            else:
                if not status(workspace):
                    return 1
                env = dict(os.environ, MDDL_DEV_MODE="1", MDDL_STATE_ROOT=str(workspace))
                # Keep the lock until GUI exit; do not launch duplicate managed sessions.
                return subprocess.run([str(gui)], cwd=workspace, env=env, check=False).returncode
        finally:
            lock.unlink(missing_ok=True)
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
