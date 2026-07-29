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


def update_modifier_state(state: dict[str, bool], event_type: str, event_value: str) -> None:
    flag = MODIFIER_EVENT_FLAGS.get(event_type)
    if flag is not None:
        state[flag] = event_value == "PRESS"


def shortcut_display(raw_key: str, ctrl: bool = False, shift: bool = False, alt: bool = False, oskey: bool = False) -> str:
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
    return " + ".join(parts)


def is_ctrl_digit_shortcut(raw_key: str, ctrl: bool) -> bool:
    return ctrl and normalize_key_event(raw_key) in DIGIT_EVENT_IDS
