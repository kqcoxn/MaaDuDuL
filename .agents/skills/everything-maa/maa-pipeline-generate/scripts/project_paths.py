#!/usr/bin/env python3
"""Interface-driven project and pipeline path helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    interface_path: Path | None
    resource_dirs: tuple[Path, ...]


def find_project_context(start: Path | None = None) -> ProjectContext:
    env_root = os.getenv("MAAHUB_ROOT") or os.getenv("PROJECT_ROOT")
    if env_root:
        return _context_for_root(Path(env_root).resolve(), require_interface=False)

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        context = _context_for_root(candidate, require_interface=False)
        if context.interface_path is not None:
            return context
    raise RuntimeError("无法定位项目根目录，请设置 MAAHUB_ROOT 或 PROJECT_ROOT 环境变量")


def find_project_root(start: Path | None = None) -> Path:
    return find_project_context(start).root


def resolve_pipeline_path(
    pipeline_file: str | Path,
    project_root: Path | None = None,
) -> Path:
    context = _context_for_root(
        (project_root or find_project_root()).resolve(),
        require_interface=True,
    )
    path = Path(pipeline_file)
    if path.is_absolute():
        return path

    # Paths with a directory component are project-relative. They may target a
    # new file, so existence must not affect resolution.
    if len(path.parts) > 1:
        return context.root / path

    candidates = [
        resource_dir / "pipeline" / path
        for resource_dir in context.resource_dirs
        if (resource_dir / "pipeline" / path).is_file()
    ]
    unique_candidates = _unique_paths(candidates)
    if len(unique_candidates) == 1:
        return unique_candidates[0]
    if len(unique_candidates) > 1:
        rendered = ", ".join(str(item) for item in unique_candidates)
        raise RuntimeError(f"pipeline 文件名 `{path}` 在多个声明资源中匹配: {rendered}")

    pipeline_dirs = _unique_paths(
        [resource_dir / "pipeline" for resource_dir in context.resource_dirs]
    )
    if len(pipeline_dirs) == 1:
        return pipeline_dirs[0] / path
    rendered = ", ".join(str(item) for item in pipeline_dirs)
    raise RuntimeError(f"无法唯一确定新 pipeline 文件 `{path}` 的资源目录: {rendered}")


def _context_for_root(root: Path, *, require_interface: bool) -> ProjectContext:
    interface_path = _find_interface(root)
    if interface_path is None:
        if require_interface:
            raise RuntimeError(f"项目 {root} 中找不到主 Interface")
        return ProjectContext(root, None, ())

    # A caller may start the ancestor search inside a boilerplate project's
    # assets directory. In that layout, assets/interface.json describes the
    # parent directory, not assets itself.
    if interface_path.parent == root and root.name == "assets":
        root = root.parent

    interface = _load_json(interface_path)
    if not isinstance(interface, dict):
        raise RuntimeError(f"主 Interface {interface_path} 顶层不是 JSON object")
    return ProjectContext(root, interface_path, _declared_resource_dirs(interface_path, interface))


def _find_interface(root: Path) -> Path | None:
    candidates = (
        root / "interface.json",
        root / "interface.jsonc",
        root / "assets" / "interface.json",
        root / "assets" / "interface.jsonc",
    )
    return next((path for path in candidates if path.is_file()), None)


def _declared_resource_dirs(interface_path: Path, interface: dict[str, Any]) -> tuple[Path, ...]:
    resources = interface.get("resource")
    if resources is None:
        return ()
    if not isinstance(resources, list):
        raise RuntimeError("主 Interface 的 resource 字段不是数组")

    dirs: list[Path] = []
    for index, group in enumerate(resources):
        if not isinstance(group, dict):
            raise RuntimeError(f"主 Interface 的 resource[{index}] 不是 JSON object")
        raw_paths = group.get("path")
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        if not isinstance(raw_paths, list) or not all(
            isinstance(path, str) and bool(path) for path in raw_paths
        ):
            raise RuntimeError(
                f"主 Interface 的 resource[{index}].path 不是字符串或字符串数组"
            )
        for raw_path in raw_paths:
            path = Path(raw_path)
            if path.is_absolute():
                raise RuntimeError(
                    f"主 Interface 的 resource[{index}].path 必须是相对路径: {raw_path}"
                )
            dirs.append((interface_path.parent / path).resolve())
    return _unique_paths(dirs)


def _unique_paths(paths: list[Path]) -> tuple[Path, ...]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            result.append(path)
    return tuple(result)


def _load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_normalize_jsonc(text))


def _normalize_jsonc(text: str) -> str:
    return _strip_trailing_commas(_strip_comments(text))


def _strip_comments(text: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False
    i = 0

    while i < len(text):
        char = text[i]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            i += 1
        elif char == "/" and i + 1 < len(text) and text[i + 1] == "/":
            start = i
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            output.extend(" " * (i - start))
        elif char == "/" and i + 1 < len(text) and text[i + 1] == "*":
            start = i
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            if i + 1 >= len(text):
                raise ValueError("unterminated block comment")
            i += 2
            output.extend(
                "\n" if text[position] == "\n" else " "
                for position in range(start, i)
            )
        else:
            output.append(char)
            i += 1

    return "".join(output)


def _strip_trailing_commas(text: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False

    for i, char in enumerate(text):
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            output.append(char)
            continue
        if char == ",":
            next_index = i + 1
            while next_index < len(text) and text[next_index].isspace():
                next_index += 1
            if next_index < len(text) and text[next_index] in "]}":
                continue
        output.append(char)

    return "".join(output)
