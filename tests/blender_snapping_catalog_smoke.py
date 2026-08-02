"""Validate curated snapping actions against the active Blender RNA."""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def _enum_identifiers(prop) -> set[str]:
    return {item.identifier for item in prop.enum_items_static if item.identifier}


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer.action_parser import parse_property_command
    from pie_customizer.command_catalog import SEARCH_ACTIONS, catalog_action_group
    from pie_customizer.runtime import run_property_command

    actions = tuple(
        action
        for action in SEARCH_ACTIONS
        if catalog_action_group(action) == "transform_snapping"
    )
    assert len(actions) >= 29

    properties = bpy.types.ToolSettings.bl_rna.properties
    tool_settings = bpy.context.scene.tool_settings
    valid_icons = {
        item.identifier
        for item in bpy.types.UILayout.bl_rna.functions["prop"]
        .parameters["icon"]
        .enum_items
        if item.identifier
    }
    for action in actions:
        assert action.icon in valid_icons, (action.action_id, action.icon)
        parsed = parse_property_command(action.command)
        property_name = parsed.path.rsplit(".", 1)[-1]
        prop = properties.get(property_name)
        assert prop is not None, action.command

        if not parsed.has_value:
            assert prop.type == "BOOLEAN", action.command
            continue

        if prop.type == "ENUM":
            identifiers = _enum_identifiers(prop)
            requested = set(parsed.value) if prop.is_enum_flag else {parsed.value}
            assert requested.issubset(identifiers), action.command
        elif prop.type == "FLOAT":
            assert isinstance(parsed.value, float), action.command
        else:
            raise AssertionError(
                f"Unexpected assigned property type {prop.type}: {action.command}"
            )

    expected_face_center = "FACE_MIDPOINT" in _enum_identifiers(
        properties["snap_elements_base"]
    )
    action_ids = {action.action_id for action in actions}
    assert ("snap_target_face_center" in action_ids) is expected_face_center

    representative_ids = {
        "snap_base_center",
        "snap_target_vertex",
        "snap_individual_face_project",
        "snap_option_align_rotation",
        "snap_rotation_increment_standard",
    }
    for action in actions:
        if action.action_id not in representative_ids:
            continue
        parsed = parse_property_command(action.command)
        property_name = parsed.path.rsplit(".", 1)[-1]
        original = getattr(tool_settings, property_name)
        try:
            assert run_property_command(action.command, bpy.context) == {"FINISHED"}
        finally:
            setattr(tool_settings, property_name, original)

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print(
        "PIE_CUSTOMIZER_SNAPPING_CATALOG_OK "
        f"Blender={bpy.app.version_string} actions={len(actions)} "
        f"face_center={expected_face_center}"
    )


if __name__ == "__main__":
    main()
