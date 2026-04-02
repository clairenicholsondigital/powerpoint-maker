from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


ALLOWED_TEXT_KEYS = {"title", "body", "subtitle", "description"}
ALLOWED_IMAGE_SUFFIXES = {"__image_url__", "__image_prompt__"}


def _is_editable_leaf_key(key: str) -> bool:
    if key in ALLOWED_TEXT_KEYS:
        return True
    return key in ALLOWED_IMAGE_SUFFIXES


def _detect_role(path: str, value: Any) -> str:
    if path.endswith("title"):
        return "title"
    if path.endswith("body") or path.endswith("description") or path.endswith("subtitle"):
        return "body"
    if path.endswith("__image_url__") or path.endswith("__image_prompt__"):
        return "image"
    if isinstance(value, str):
        return "body"
    return "body"


def _collect_editable_zones(value: Any, path: str = "") -> List[Dict[str, Any]]:
    zones: List[Dict[str, Any]] = []
    if isinstance(value, dict):
        for k, v in value.items():
            current_path = f"{path}.{k}" if path else k
            if _is_editable_leaf_key(k):
                zones.append(
                    {
                        "path": current_path,
                        "role": _detect_role(current_path, v),
                        "editable": True,
                    }
                )
                continue
            zones.extend(_collect_editable_zones(v, current_path))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            current_path = f"{path}[{i}]"
            zones.extend(_collect_editable_zones(item, current_path))
    return zones


def build_default_template_lock_constraints(content: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mode": "replace_content_only",
        "editable_zones": _collect_editable_zones(content),
        "locked_zones": ["structure", "styling"],
    }


def _tokenize_path(path: str) -> List[Any]:
    normalized = path.replace("[", ".").replace("]", "")
    tokens: List[Any] = []
    for token in normalized.split("."):
        if token == "":
            continue
        if token.isdigit():
            tokens.append(int(token))
        else:
            tokens.append(token)
    return tokens


def _get_path(data: Any, path: str) -> Any:
    current = data
    for token in _tokenize_path(path):
        if isinstance(token, int):
            if not isinstance(current, list) or token >= len(current):
                return None
            current = current[token]
        else:
            if not isinstance(current, dict) or token not in current:
                return None
            current = current[token]
    return current


def _set_path(data: Any, path: str, value: Any) -> None:
    tokens = _tokenize_path(path)
    if not tokens:
        return

    current = data
    for i, token in enumerate(tokens[:-1]):
        next_token = tokens[i + 1]
        if isinstance(token, int):
            if not isinstance(current, list):
                return
            while len(current) <= token:
                current.append({} if not isinstance(next_token, int) else [])
            current = current[token]
        else:
            if not isinstance(current, dict):
                return
            if token not in current:
                current[token] = [] if isinstance(next_token, int) else {}
            current = current[token]

    last = tokens[-1]
    if isinstance(last, int):
        if not isinstance(current, list):
            return
        while len(current) <= last:
            current.append(None)
        current[last] = value
    else:
        if not isinstance(current, dict):
            return
        current[last] = value


def enforce_template_lock_content(
    original_content: Dict[str, Any],
    proposed_content: Dict[str, Any],
    constraints: Dict[str, Any] | None,
) -> Dict[str, Any]:
    if not constraints:
        constraints = build_default_template_lock_constraints(original_content)

    editable_zones = constraints.get("editable_zones", [])
    filtered_content = deepcopy(original_content)

    for zone in editable_zones:
        if not zone.get("editable"):
            continue
        zone_path = zone.get("path")
        if not zone_path:
            continue
        new_value = _get_path(proposed_content, zone_path)
        if new_value is not None:
            _set_path(filtered_content, zone_path, new_value)

    return filtered_content
