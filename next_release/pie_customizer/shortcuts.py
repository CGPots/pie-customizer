"""Shortcut normalization helpers."""

from __future__ import annotations


KEY_ALIASES = {
    "0": "ZERO",
    "1": "ONE",
    "2": "TWO",
    "3": "THREE",
    "4": "FOUR",
    "5": "FIVE",
    "6": "SIX",
    "7": "SEVEN",
    "8": "EIGHT",
    "9": "NINE",
    "SPACEBAR": "SPACE",
    "SPACE BAR": "SPACE",
    "ESC": "ESC",
    "ESCAPE": "ESC",
    "RETURN": "RET",
    "ENTER": "RET",
    "CMD": "OSKEY",
    "COMMAND": "OSKEY",
}

DISPLAY_NAMES = {
    "ZERO": "0",
    "ONE": "1",
    "TWO": "2",
    "THREE": "3",
    "FOUR": "4",
    "FIVE": "5",
    "SIX": "6",
    "SEVEN": "7",
    "EIGHT": "8",
    "NINE": "9",
    "SPACE": "Space",
    "RET": "Enter",
    "ESC": "Esc",
}

EVENT_VALUE_ITEMS = (
    ("PRESS", "Press", "Trigger when the shortcut is pressed"),
    ("RELEASE", "Release", "Trigger when the shortcut is released"),
    ("CLICK", "Click", "Trigger on a single click"),
    ("DOUBLE_CLICK", "Double Click", "Trigger on a double click"),
    ("CLICK_DRAG", "Drag", "Trigger when the shortcut is dragged"),
)

EVENT_VALUE_IDS = frozenset(item[0] for item in EVENT_VALUE_ITEMS)
EVENT_VALUE_NAMES = {item[0]: item[1] for item in EVENT_VALUE_ITEMS}
EVENT_VALUE_ALIASES = {
    "DRAG": "CLICK_DRAG",
}

MODIFIER_EVENT_TYPES = {
    "LEFT_CTRL",
    "RIGHT_CTRL",
    "LEFT_SHIFT",
    "RIGHT_SHIFT",
    "LEFT_ALT",
    "RIGHT_ALT",
    "OSKEY",
}

MODIFIER_EVENT_FLAGS = {
    "LEFT_CTRL": "ctrl",
    "RIGHT_CTRL": "ctrl",
    "LEFT_SHIFT": "shift",
    "RIGHT_SHIFT": "shift",
    "LEFT_ALT": "alt",
    "RIGHT_ALT": "alt",
    "OSKEY": "oskey",
}

DIGIT_EVENT_IDS = {
    "ZERO",
    "ONE",
    "TWO",
    "THREE",
    "FOUR",
    "FIVE",
    "SIX",
    "SEVEN",
    "EIGHT",
    "NINE",
}

PLAIN_POINTER_EVENT_IDS = {
    "LEFTMOUSE",
    "RIGHTMOUSE",
    "MIDDLEMOUSE",
    "WHEELUPMOUSE",
    "WHEELDOWNMOUSE",
    "WHEELINMOUSE",
    "WHEELOUTMOUSE",
    "WHEELLEFTMOUSE",
    "WHEELRIGHTMOUSE",
    "TRACKPADPAN",
    "TRACKPADZOOM",
    "MOUSEROTATE",
    "MOUSESMARTZOOM",
    "MOUSEMOVE",
    "INBETWEEN_MOUSEMOVE",
}

PLAIN_KEYBOARD_EVENT_IDS = {
    "SPACE",
    "TAB",
    "RET",
    "NUMPAD_ENTER",
    "BACK_SPACE",
    "DEL",
}

PLAIN_SHORTCUT_EVENT_IDS = PLAIN_POINTER_EVENT_IDS | PLAIN_KEYBOARD_EVENT_IDS


def normalize_key_event(raw_key: str) -> str:
    key = (raw_key or "").strip().upper()
    if not key:
        return ""
    key = key.replace(" ", "_") if key.startswith("NUMPAD ") else key
    return KEY_ALIASES.get(key, key)


def key_display_name(raw_key: str) -> str:
    normalized = normalize_key_event(raw_key)
    return DISPLAY_NAMES.get(normalized, normalized)


def key_storage_name(event_type: str) -> str:
    return key_display_name(event_type)


def normalize_event_value(raw_value: str) -> str:
    value = str(raw_value or "").strip().upper().replace(" ", "_")
    return EVENT_VALUE_ALIASES.get(value, value)


def event_value_display(raw_value: str) -> str:
    value = normalize_event_value(raw_value)
    return EVENT_VALUE_NAMES.get(value, value.replace("_", " ").title())


def update_modifier_state(state: dict[str, bool], event_type: str, event_value: str) -> None:
    flag = MODIFIER_EVENT_FLAGS.get(event_type)
    if flag is not None:
        state[flag] = event_value == "PRESS"


def shortcut_display(
    raw_key: str,
    ctrl: bool = False,
    shift: bool = False,
    alt: bool = False,
    oskey: bool = False,
    event_value: str = "",
) -> str:
    parts = []
    if ctrl:
        parts.append("Ctrl")
    if shift:
        parts.append("Shift")
    if alt:
        parts.append("Alt")
    if oskey:
        parts.append("Cmd/OS")
    key = key_display_name(raw_key)
    if key:
        parts.append(key)
    shortcut = " + ".join(parts)
    if shortcut and event_value:
        return f"{shortcut} · {event_value_display(event_value)}"
    return shortcut


def is_ctrl_digit_shortcut(raw_key: str, ctrl: bool) -> bool:
    return ctrl and normalize_key_event(raw_key) in DIGIT_EVENT_IDS


def is_unsafe_plain_shortcut(
    raw_key: str,
    ctrl: bool = False,
    shift: bool = False,
    alt: bool = False,
    oskey: bool = False,
) -> bool:
    """Return whether a shortcut would replace essential Blender input."""

    return normalize_key_event(raw_key) in PLAIN_SHORTCUT_EVENT_IDS and not any(
        (ctrl, shift, alt, oskey)
    )
