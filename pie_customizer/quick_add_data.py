"""Pure helpers for capturing Blender buttons without importing Blender."""

from __future__ import annotations

from collections.abc import Iterable
from collections import deque


SUPPORTED_RNA_PROPERTY_TYPES = frozenset({"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"})

SPACE_RNA_TYPES = {
    "VIEW_3D": "SpaceView3D",
    "IMAGE_EDITOR": "SpaceImageEditor",
    "NODE_EDITOR": "SpaceNodeEditor",
    "SEQUENCE_EDITOR": "SpaceSequenceEditor",
    "CLIP_EDITOR": "SpaceClipEditor",
    "DOPESHEET_EDITOR": "SpaceDopeSheetEditor",
    "GRAPH_EDITOR": "SpaceGraphEditor",
    "NLA_EDITOR": "SpaceNLA",
    "TEXT_EDITOR": "SpaceTextEditor",
    "CONSOLE": "SpaceConsole",
    "INFO": "SpaceInfo",
    "OUTLINER": "SpaceOutliner",
    "PROPERTIES": "SpaceProperties",
    "FILE_BROWSER": "SpaceFileBrowser",
    "SPREADSHEET": "SpaceSpreadsheet",
}

NESTED_SPACE_PROPERTY_OWNERS = {
    "VIEW_3D": {
        "overlay": "View3DOverlay",
        "shading": "View3DShading",
    },
    "NODE_EDITOR": {"overlay": "SpaceNodeOverlay"},
    "IMAGE_EDITOR": {
        "overlay": "SpaceImageOverlay",
        "uv_editor": "SpaceUVEditor",
    },
}

SPACE_KEYMAP_SETTINGS = {
    "VIEW_3D": ("VIEW_3D", "3D View", "VIEW_3D", "WINDOW"),
    "IMAGE_EDITOR": ("IMAGE", "Image", "IMAGE_EDITOR", "WINDOW"),
    "NODE_EDITOR": ("NODE_EDITOR", "Node Editor", "NODE_EDITOR", "WINDOW"),
    "SEQUENCE_EDITOR": ("CUSTOM", "Sequencer", "SEQUENCE_EDITOR", "WINDOW"),
    "CLIP_EDITOR": ("CUSTOM", "Clip Editor", "CLIP_EDITOR", "WINDOW"),
    "DOPESHEET_EDITOR": ("CUSTOM", "Dopesheet", "DOPESHEET_EDITOR", "WINDOW"),
    "GRAPH_EDITOR": ("CUSTOM", "Graph Editor", "GRAPH_EDITOR", "WINDOW"),
    "NLA_EDITOR": ("CUSTOM", "NLA Editor", "NLA_EDITOR", "WINDOW"),
    "TEXT_EDITOR": ("CUSTOM", "Text", "TEXT_EDITOR", "WINDOW"),
    "CONSOLE": ("CUSTOM", "Console", "CONSOLE", "WINDOW"),
    "INFO": ("CUSTOM", "Info", "INFO", "WINDOW"),
    "OUTLINER": ("CUSTOM", "Outliner", "OUTLINER", "WINDOW"),
    "PROPERTIES": ("CUSTOM", "Property Editor", "PROPERTIES", "WINDOW"),
    "FILE_BROWSER": ("CUSTOM", "File Browser", "FILE_BROWSER", "WINDOW"),
    "SPREADSHEET": ("CUSTOM", "Spreadsheet Generic", "SPREADSHEET", "WINDOW"),
}

CONTEXT_ROOT_PRIORITY = (
    "tool_settings",
    "space_data",
    "scene",
    "object",
    "active_object",
    "edit_object",
    "pose_object",
    "view_layer",
    "workspace",
    "screen",
    "region_data",
    "material",
    "world",
    "collection",
)


def normalize_rna_value(property_type: str, is_array: bool, value):
    """Return a literal-safe value, or raise when the RNA value is unsupported."""

    if property_type not in SUPPORTED_RNA_PROPERTY_TYPES:
        raise TypeError(f"Unsupported RNA property type: {property_type}")

    if property_type == "ENUM" and isinstance(value, set):
        if not all(isinstance(item, str) for item in value):
            raise TypeError("Enum flag values must contain strings")
        return set(value)

    if is_array:
        if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
            raise TypeError("RNA array value is not iterable")
        normalized = tuple(value)
        if not all(_is_scalar(item) for item in normalized):
            raise TypeError("RNA array contains a non-literal value")
        return normalized

    if not _is_scalar(value):
        raise TypeError("RNA value is not a supported literal")
    return value


def slot_is_occupied(slot) -> bool:
    return bool(
        getattr(slot, "enabled", False)
        and getattr(slot, "slot_type", "SEPARATOR") != "SEPARATOR"
        and getattr(slot, "command", "")
    )


def find_context_pointer_path(context, target, *, max_depth: int = 3) -> str:
    """Find a stable context path to an RNA owner using pointer properties only.

    Collection indexes are deliberately not traversed because paths through areas,
    objects, or other collections are not stable enough for a reusable pie action.
    """

    if context is None or target is None:
        return ""

    roots = []
    seen_names = set()
    for name in CONTEXT_ROOT_PRIORITY:
        _append_context_root(roots, seen_names, context, name)

    copy_context = getattr(context, "copy", None)
    if callable(copy_context):
        try:
            context_values = copy_context()
        except (AttributeError, RuntimeError, TypeError, ValueError):
            context_values = {}
        if isinstance(context_values, dict):
            for name in sorted(context_values):
                if _is_identifier(name) and not name.startswith("button_"):
                    _append_context_root(
                        roots,
                        seen_names,
                        context,
                        name,
                        fallback=context_values[name],
                    )

    visited = set()
    queue = deque((value, f"context.{name}", 0) for name, value in roots)
    while queue:
        value, path, depth = queue.popleft()
        pointer_key = _pointer_key(value)
        if pointer_key in visited:
            continue
        visited.add(pointer_key)
        if _same_rna_pointer(value, target):
            return path
        if depth >= max_depth:
            continue

        rna = getattr(value, "bl_rna", None)
        for descriptor in getattr(rna, "properties", ()):
            identifier = getattr(descriptor, "identifier", "")
            if (
                not _is_identifier(identifier)
                or identifier == "rna_type"
                or getattr(descriptor, "type", "") != "POINTER"
                or bool(getattr(descriptor, "is_array", False))
            ):
                continue
            try:
                child = getattr(value, identifier)
            except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
                continue
            if child is None or getattr(child, "bl_rna", None) is None:
                continue
            queue.append((child, f"{path}.{identifier}", depth + 1))
    return ""


def supported_property_owner_path(context, target) -> str:
    """Return a reusable owner path from the explicit cross-version allow-list."""

    tool_settings = _context_member(context, "tool_settings")
    scene = _context_member(context, "scene")
    if tool_settings is None and scene is not None:
        tool_settings = _context_member(scene, "tool_settings")
    if tool_settings is not None and _same_rna_pointer(tool_settings, target):
        return "context.scene.tool_settings"

    orientation_slots = _context_member(scene, "transform_orientation_slots")
    try:
        orientation_slot = orientation_slots[0]
    except (AttributeError, IndexError, ReferenceError, TypeError):
        orientation_slot = None
    if (
        orientation_slot is not None
        and _rna_identifier(orientation_slot) == "TransformOrientationSlot"
        and _same_rna_pointer(orientation_slot, target)
    ):
        return "context.scene.transform_orientation_slots[0]"

    space_data = _context_member(context, "space_data")
    space_type = getattr(space_data, "type", "") if space_data is not None else ""
    expected_rna = SPACE_RNA_TYPES.get(space_type)
    if expected_rna is None or _rna_identifier(space_data) != expected_rna:
        return ""
    if _same_rna_pointer(space_data, target):
        return "context.space_data"

    for property_id, owner_rna in NESTED_SPACE_PROPERTY_OWNERS.get(space_type, {}).items():
        owner = _context_member(space_data, property_id)
        if (
            owner is not None
            and _rna_identifier(owner) == owner_rna
            and _same_rna_pointer(owner, target)
        ):
            return f"context.space_data.{property_id}"
    return ""


def context_space_type(context) -> str:
    """Return an editor type only when it has a stable supported keymap."""

    space_data = _context_member(context, "space_data")
    space_type = getattr(space_data, "type", "") if space_data is not None else ""
    expected_rna = SPACE_RNA_TYPES.get(space_type)
    if expected_rna is None or _rna_identifier(space_data) != expected_rna:
        return ""
    return space_type


def keymap_settings_for_space_type(space_type: str):
    """Return menu keymap fields for an editor, or None when unsupported."""

    return SPACE_KEYMAP_SETTINGS.get(space_type)


def format_property_command(path: str, value=...):
    """Build the existing safe property command syntax."""

    if value is ...:
        return path
    return f"{path} = {_format_literal(value)}"


def _is_scalar(value) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _append_context_root(roots, seen_names, context, name, *, fallback=None):
    if name in seen_names:
        return
    try:
        value = getattr(context, name)
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        value = fallback
    if value is None or getattr(value, "bl_rna", None) is None:
        return
    roots.append((name, value))
    seen_names.add(name)


def _same_rna_pointer(left, right) -> bool:
    if left is right:
        return True
    try:
        return (
            int(left.as_pointer()) == int(right.as_pointer())
            and _rna_identifier(left) == _rna_identifier(right)
        )
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        return False


def _pointer_key(value):
    try:
        return ("RNA", int(value.as_pointer()), _rna_identifier(value))
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        return ("PY", id(value))


def _rna_identifier(value) -> str:
    return getattr(getattr(value, "bl_rna", None), "identifier", "")


def _is_identifier(value) -> bool:
    return isinstance(value, str) and value.isidentifier()


def _context_member(owner, name):
    try:
        return getattr(owner, name)
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        return None


def _format_literal(value) -> str:
    if isinstance(value, set):
        if not value:
            return "set()"
        return "{" + ", ".join(sorted(repr(item) for item in value)) + "}"
    return repr(value)
