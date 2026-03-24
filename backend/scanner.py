from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_JSON_SUFFIX = ".json"


def _relative_to_root(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def build_visible_tree(root_dir: Path, current_dir: Path | None = None) -> dict[str, Any]:
    current = current_dir or root_dir

    node: dict[str, Any] = {
        "name": current.name,
        "path": _relative_to_root(current, root_dir) if current != root_dir else current.name,
        "node_type": "folder",
        "children": [],
    }

    children = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    for child in children:
        if child.is_dir():
            node["children"].append(build_visible_tree(root_dir, child))
            continue

        if child.suffix.lower() == ALLOWED_JSON_SUFFIX:
            continue

        node["children"].append(
            {
                "name": child.name,
                "path": _relative_to_root(child, root_dir),
                "node_type": "file",
                "children": [],
            }
        )

    return node


def extract_content_from_json(json_path: Path) -> str:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    segments = data.get("segments", [])
    if not isinstance(segments, list):
        return ""

    pieces: list[str] = []
    for segment in segments:
        if isinstance(segment, dict):
            content = segment.get("content", "")
            if isinstance(content, str) and content.strip():
                pieces.append(content.strip())

    return "\n\n".join(pieces)


def load_documents(root_dir: Path) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []

    for json_path in root_dir.rglob("*.json"):
        content = extract_content_from_json(json_path)
        if not content:
            continue

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        file_info = data.get("file_info", {}) if isinstance(data, dict) else {}
        file_path = str(file_info.get("file_path", "")).strip()
        file_name = str(file_info.get("file_name", "")).strip()
        file_type = str(file_info.get("file_type", "")).strip()

        if not file_path:
            relative_json = _relative_to_root(json_path, root_dir)
            guessed = relative_json[:-5]
            file_path = f"{root_dir.name}/{guessed}"

        if not file_name:
            file_name = Path(file_path).name

        if not file_type:
            file_type = Path(file_name).suffix.lstrip(".").lower()

        documents.append(
            {
                "json_path": str(json_path),
                "file_path": file_path,
                "file_name": file_name,
                "file_type": file_type,
                "content": content,
            }
        )

    return documents
