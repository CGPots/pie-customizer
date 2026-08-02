"""Validate dynamically discovered modifier actions in a real Blender runtime."""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer.action_parser import parse_operator_command
    from pie_customizer.discovery import PHYSICS_MODIFIER_IDS, discover_operator_actions
    from pie_customizer.runtime import normalize_operator_command, run_operator_command

    enum_items = tuple(
        item
        for item in bpy.ops.object.modifier_add.get_rna_type()
        .properties["type"]
        .enum_items_static
        if item.identifier
    )
    expected_ids = {item.identifier for item in enum_items}
    actions = tuple(
        action
        for action in discover_operator_actions()
        if action.token.startswith("OPERATOR_VARIANT:object.modifier_add:")
    )
    discovered_ids = {
        parse_operator_command(action.command).kwargs["type"] for action in actions
    }

    assert discovered_ids == expected_ids
    assert len(actions) == len(expected_ids)
    assert not any(action.command == "object.modifier_add()" for action in actions)

    for action in actions:
        parsed = parse_operator_command(action.command)
        modifier_id = parsed.kwargs["type"]
        assert parsed.operator_id == "object.modifier_add"
        assert normalize_operator_command(action.command) == action.command
        if modifier_id.startswith("GREASE_PENCIL_") or modifier_id == "LINEART":
            assert action.group == "grease_pencil_modifiers"
            assert action.label.startswith("Grease Pencil:")
        elif modifier_id in PHYSICS_MODIFIER_IDS:
            assert action.group == "physics_modifiers"
        else:
            assert action.group == "object_modifiers"

    bpy.ops.object.select_all(action="SELECT")
    active_object = bpy.context.active_object
    assert active_object is not None and active_object.type == "MESH"
    for modifier_id in ("ARRAY", "BEVEL", "SUBSURF", "CLOTH"):
        if modifier_id not in expected_ids:
            continue
        before = len(active_object.modifiers)
        result = run_operator_command(
            f"object.modifier_add(type='{modifier_id}')",
            "EXEC_DEFAULT",
        )
        assert result == {"FINISHED"}
        assert len(active_object.modifiers) == before + 1
        assert active_object.modifiers[-1].type == modifier_id

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print(
        "PIE_CUSTOMIZER_MODIFIER_CATALOG_OK "
        f"Blender={bpy.app.version_string} modifiers={len(actions)}"
    )


if __name__ == "__main__":
    main()
