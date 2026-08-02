"""Validation helpers for imported Pie Customizer presets."""

from __future__ import annotations


MAX_PRESET_MENUS = 256
VALID_KEYMAP_CONTEXTS = {
    "VIEW_3D",
    "OBJECT_MODE",
    "MESH",
    "WINDOW",
    "IMAGE",
    "NODE_EDITOR",
    "CUSTOM",
}
VALID_EVENT_VALUES = {"PRESS", "RELEASE", "CLICK", "DOUBLE_CLICK"}
VALID_SLOT_TYPES = {"SEPARATOR", "OPERATOR", "PROPERTY", "MENU"}
VALID_OPERATOR_CONTEXTS = {"INVOKE_DEFAULT", "EXEC_DEFAULT"}


def normalize_preset_items(items) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("pie_menus must be a list")
    if len(items) > MAX_PRESET_MENUS:
        raise ValueError(f"A preset can contain at most {MAX_PRESET_MENUS} menus")

    return [_normalize_menu(item, index) for index, item in enumerate(items)]


def _normalize_menu(item, index: int) -> dict:
    if not isinstance(item, dict):
        raise ValueError(f"pie_menus[{index}] must be an object")

    slots = item.get("slots", [])
    if not isinstance(slots, list):
        raise ValueError(f"pie_menus[{index}].slots must be a list")

    return {
        "uid": _text(item.get("uid", "")),
        "enabled": _boolean(item.get("enabled", True), f"pie_menus[{index}].enabled"),
        "name": _text(item.get("name", "")),
        "keymap_context": _enum(
            item.get("keymap_context", "VIEW_3D"),
            VALID_KEYMAP_CONTEXTS,
            f"pie_menus[{index}].keymap_context",
        ),
        "custom_keymap_name": _text(item.get("custom_keymap_name", "3D View")),
        "custom_space_type": _text(item.get("custom_space_type", "VIEW_3D")),
        "custom_region_type": _text(item.get("custom_region_type", "WINDOW")),
        "key": _text(item.get("key", "")),
        "event_value": _enum(
            item.get("event_value", "PRESS"),
            VALID_EVENT_VALUES,
            f"pie_menus[{index}].event_value",
        ),
        "ctrl": _boolean(item.get("ctrl", False), f"pie_menus[{index}].ctrl"),
        "shift": _boolean(item.get("shift", False), f"pie_menus[{index}].shift"),
        "alt": _boolean(item.get("alt", False), f"pie_menus[{index}].alt"),
        "oskey": _boolean(item.get("oskey", False), f"pie_menus[{index}].oskey"),
        "slots": [_normalize_slot(slot, index, slot_index) for slot_index, slot in enumerate(slots[:8])],
    }


def _normalize_slot(item, menu_index: int, slot_index: int) -> dict:
    path = f"pie_menus[{menu_index}].slots[{slot_index}]"
    if not isinstance(item, dict):
        raise ValueError(f"{path} must be an object")

    slot_type = _enum(item.get("slot_type", "SEPARATOR"), VALID_SLOT_TYPES, f"{path}.slot_type")
    default_enabled = slot_type != "SEPARATOR"
    return {
        "enabled": _boolean(item.get("enabled", default_enabled), f"{path}.enabled"),
        "label": _text(item.get("label", "")),
        "icon": _text(item.get("icon", "NONE")) or "NONE",
        "slot_type": slot_type,
        "command": _text(item.get("command", "")),
        "operator_context": _enum(
            item.get("operator_context", "INVOKE_DEFAULT"),
            VALID_OPERATOR_CONTEXTS,
            f"{path}.operator_context",
        ),
    }


def _enum(value, allowed: set[str], path: str) -> str:
    text = _text(value)
    if text not in allowed:
        raise ValueError(f"Invalid value for {path}: {text!r}")
    return text


def _boolean(value, path: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ValueError(f"Invalid boolean for {path}")


def _text(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Text values must be strings or scalar JSON values")
    return str(value)
