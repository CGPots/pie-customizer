"""Context-mode availability for custom pie menus."""

from __future__ import annotations


MODE_FILTER_DEFINITIONS = (
    ("OBJECT", "Object Mode", "Режим объекта", ("OBJECT",)),
    ("EDIT_ANY", "Any Edit Mode", "Любой режим редактирования", ()),
    ("POSE", "Pose Mode", "Режим позы", ("POSE",)),
    ("EDIT_MESH", "Mesh Edit", "Редактирование сетки", ("EDIT_MESH",)),
    (
        "EDIT_CURVE_SURFACE",
        "Curve / Surface Edit",
        "Редактирование кривых и поверхностей",
        ("EDIT_CURVE", "EDIT_SURFACE"),
    ),
    ("EDIT_CURVES", "Curves Edit", "Редактирование Curves", ("EDIT_CURVES",)),
    (
        "EDIT_POINT_CLOUD",
        "Point Cloud Edit",
        "Редактирование облака точек",
        ("EDIT_POINT_CLOUD", "EDIT_POINTCLOUD"),
    ),
    ("EDIT_ARMATURE", "Armature Edit", "Редактирование арматуры", ("EDIT_ARMATURE",)),
    ("EDIT_LATTICE", "Lattice Edit", "Редактирование решётки", ("EDIT_LATTICE",)),
    ("EDIT_TEXT", "Text Edit", "Редактирование текста", ("EDIT_TEXT",)),
    ("EDIT_METABALL", "Metaball Edit", "Редактирование метасфер", ("EDIT_METABALL",)),
    ("SCULPT", "Sculpt Mode", "Скульптинг", ("SCULPT",)),
    ("SCULPT_CURVES", "Curves Sculpt", "Скульптинг Curves", ("SCULPT_CURVES",)),
    ("PAINT_TEXTURE", "Texture Paint", "Рисование текстур", ("PAINT_TEXTURE",)),
    ("PAINT_VERTEX", "Vertex Paint", "Рисование вершин", ("PAINT_VERTEX",)),
    ("PAINT_WEIGHT", "Weight Paint", "Рисование весов", ("PAINT_WEIGHT",)),
    ("PARTICLE", "Particle Edit", "Редактирование частиц", ("PARTICLE",)),
    (
        "GP_DRAW",
        "Grease Pencil Draw",
        "Рисование Grease Pencil",
        ("PAINT_GPENCIL", "PAINT_GREASE_PENCIL"),
    ),
    (
        "GP_EDIT",
        "Grease Pencil Edit",
        "Редактирование Grease Pencil",
        ("EDIT_GPENCIL", "EDIT_GREASE_PENCIL"),
    ),
    (
        "GP_SCULPT",
        "Grease Pencil Sculpt",
        "Скульптинг Grease Pencil",
        ("SCULPT_GPENCIL", "SCULPT_GREASE_PENCIL"),
    ),
    (
        "GP_VERTEX",
        "Grease Pencil Vertex Paint",
        "Рисование вершин Grease Pencil",
        ("VERTEX_GPENCIL", "VERTEX_GREASE_PENCIL"),
    ),
    (
        "GP_WEIGHT",
        "Grease Pencil Weight Paint",
        "Рисование весов Grease Pencil",
        ("WEIGHT_GPENCIL", "WEIGHT_GREASE_PENCIL"),
    ),
)

MODE_FILTER_ITEMS = tuple(
    (identifier, label_en, "", "NONE", 1 << index)
    for index, (identifier, label_en, _label_ru, _context_modes) in enumerate(
        MODE_FILTER_DEFINITIONS
    )
)
MODE_FILTER_IDS = frozenset(item[0] for item in MODE_FILTER_DEFINITIONS)
MODE_FILTER_TARGETS = {
    identifier: frozenset(context_modes)
    for identifier, _label_en, _label_ru, context_modes in MODE_FILTER_DEFINITIONS
}
MODE_FILTER_LABELS = {
    identifier: {"EN": label_en, "RU": label_ru}
    for identifier, label_en, label_ru, _context_modes in MODE_FILTER_DEFINITIONS
}

MODE_FILTER_GROUPS = (
    ("availability_general", ("OBJECT", "POSE")),
    (
        "availability_edit",
        (
            "EDIT_ANY",
            "EDIT_MESH",
            "EDIT_CURVE_SURFACE",
            "EDIT_CURVES",
            "EDIT_POINT_CLOUD",
            "EDIT_ARMATURE",
            "EDIT_LATTICE",
            "EDIT_TEXT",
            "EDIT_METABALL",
        ),
    ),
    (
        "availability_paint",
        (
            "SCULPT",
            "SCULPT_CURVES",
            "PAINT_TEXTURE",
            "PAINT_VERTEX",
            "PAINT_WEIGHT",
        ),
    ),
    (
        "availability_grease",
        ("GP_DRAW", "GP_EDIT", "GP_SCULPT", "GP_VERTEX", "GP_WEIGHT"),
    ),
    ("availability_other", ("PARTICLE",)),
)

SPECIFIC_EDIT_FILTER_IDS = frozenset(
    identifier
    for identifier in MODE_FILTER_IDS
    if identifier.startswith("EDIT_") and identifier != "EDIT_ANY"
)


def normalized_mode_selection(allowed_modes) -> set[str]:
    """Collapse redundant edit-mode choices into the broader EDIT_ANY option."""

    selected = set(allowed_modes or ())
    if "EDIT_ANY" in selected:
        selected.difference_update(SPECIFIC_EDIT_FILTER_IDS)
    return selected


def menu_matches_mode(mode_filter_enabled: bool, allowed_modes, context_mode: str) -> bool:
    """Return whether a menu is available for one public Context.mode value."""

    if not mode_filter_enabled:
        return True

    selected = normalized_mode_selection(allowed_modes)
    if not selected:
        return False
    if "EDIT_ANY" in selected and context_mode.startswith("EDIT_"):
        return True
    return any(
        context_mode in MODE_FILTER_TARGETS.get(identifier, ())
        for identifier in selected
    )


def menu_matches_context(menu_config, context) -> bool:
    return menu_matches_mode(
        bool(getattr(menu_config, "mode_filter_enabled", False)),
        getattr(menu_config, "allowed_modes", ()),
        str(getattr(context, "mode", "OBJECT")),
    )


def supported_filter_ids(context_mode_ids) -> frozenset[str]:
    available = set(context_mode_ids)
    supported = {
        identifier
        for identifier, targets in MODE_FILTER_TARGETS.items()
        if targets.intersection(available)
    }
    if any(mode.startswith("EDIT_") for mode in available):
        supported.add("EDIT_ANY")
    return frozenset(supported)


def blender_context_mode_ids() -> frozenset[str]:
    try:
        import bpy

        enum_items = bpy.types.Context.bl_rna.properties["mode"].enum_items
        return frozenset(item.identifier for item in enum_items if item.identifier)
    except (AttributeError, KeyError, ModuleNotFoundError, RuntimeError, TypeError):
        return frozenset(
            target
            for targets in MODE_FILTER_TARGETS.values()
            for target in targets
        )


def mode_label(identifier: str, language: str) -> str:
    labels = MODE_FILTER_LABELS.get(identifier)
    if labels is None:
        return identifier
    return labels.get(language, labels["EN"])


def preferred_filter_for_context_mode(context_mode: str) -> str:
    exact_order = (
        "OBJECT",
        "POSE",
        "EDIT_MESH",
        "EDIT_CURVE_SURFACE",
        "EDIT_CURVES",
        "EDIT_POINT_CLOUD",
        "EDIT_ARMATURE",
        "EDIT_LATTICE",
        "EDIT_TEXT",
        "EDIT_METABALL",
        "SCULPT",
        "SCULPT_CURVES",
        "PAINT_TEXTURE",
        "PAINT_VERTEX",
        "PAINT_WEIGHT",
        "PARTICLE",
        "GP_DRAW",
        "GP_EDIT",
        "GP_SCULPT",
        "GP_VERTEX",
        "GP_WEIGHT",
    )
    for identifier in exact_order:
        if context_mode in MODE_FILTER_TARGETS[identifier]:
            return identifier
    return "EDIT_ANY" if context_mode.startswith("EDIT_") else "OBJECT"
