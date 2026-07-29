"""Validate curated sculpt actions against Blender and the command browser.

Run with Blender in background mode:
  blender --background --factory-startup \
    --python tests/blender_sculpt_catalog_smoke.py -- /path/to/project

Blender's sculpt undo stack is unavailable in background mode, so commands
that push sculpt undo are schema-checked there instead of being executed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def _prepare_sculpt_object() -> None:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
    obj = bpy.context.active_object
    assert obj is not None
    obj.data.remesh_voxel_size = 0.25
    bpy.ops.object.mode_set(mode="SCULPT")
    assert bpy.context.mode == "SCULPT"


def _operator(operator_id: str):
    namespace, name = operator_id.split(".", 1)
    return getattr(getattr(bpy.ops, namespace), name)


def _assert_operator_schema(operator_id: str, expected_arguments=()) -> None:
    operator = _operator(operator_id)
    properties = operator.get_rna_type().properties
    for argument in expected_arguments:
        assert properties.get(argument) is not None, f"{operator_id}.{argument}"


def _assert_sculpt_schemas() -> None:
    _assert_operator_schema("object.voxel_remesh")
    _assert_operator_schema("object.voxel_size_edit")
    _assert_operator_schema("sculpt.dynamic_topology_toggle")
    _assert_operator_schema("sculpt.symmetrize")
    _assert_operator_schema("paint.mask_flood_fill", ("mode", "value"))

    mode_property = bpy.ops.paint.mask_flood_fill.get_rna_type().properties["mode"]
    mask_modes = {item.identifier for item in mode_property.enum_items_static}
    assert {"VALUE", "INVERT"}.issubset(mask_modes)

    assert bpy.types.Mesh.bl_rna.properties.get("use_mirror_x") is not None


def _exercise_mirror_x_property() -> None:
    from pie_customizer import runtime

    _prepare_sculpt_object()
    mesh = bpy.context.active_object.data
    original_mirror_x = mesh.use_mirror_x

    assert runtime.run_property_command(
        "context.object.data.use_mirror_x",
        bpy.context,
    ) == {"FINISHED"}
    assert mesh.use_mirror_x is not original_mirror_x

    # Menus saved by earlier Pie Customizer builds keep working after update.
    assert runtime.run_property_command(
        "context.scene.tool_settings.sculpt.use_symmetry_x",
        bpy.context,
    ) == {"FINISHED"}
    assert mesh.use_mirror_x is original_mirror_x

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.delete()


def _exercise_sculpt_actions() -> None:
    _prepare_sculpt_object()

    assert bpy.ops.paint.mask_flood_fill.poll()
    assert bpy.ops.paint.mask_flood_fill(mode="VALUE", value=1.0) == {"FINISHED"}
    assert bpy.ops.paint.mask_flood_fill(mode="INVERT") == {"FINISHED"}
    assert bpy.ops.paint.mask_flood_fill(mode="VALUE", value=0.0) == {"FINISHED"}

    assert bpy.ops.object.voxel_remesh.poll()
    assert bpy.ops.object.voxel_remesh() == {"FINISHED"}

    assert bpy.ops.sculpt.symmetrize.poll()
    assert bpy.ops.sculpt.symmetrize() == {"FINISHED"}

    mesh = bpy.context.active_object.data
    original_mirror_x = mesh.use_mirror_x
    mesh.use_mirror_x = not original_mirror_x
    assert mesh.use_mirror_x is not original_mirror_x
    mesh.use_mirror_x = original_mirror_x

    assert bpy.ops.sculpt.dynamic_topology_toggle.poll()
    assert bpy.ops.sculpt.dynamic_topology_toggle() == {"FINISHED"}
    assert bpy.context.active_object.use_dynamic_topology_sculpting
    assert bpy.ops.sculpt.dynamic_topology_toggle() == {"FINISHED"}
    assert not bpy.context.active_object.use_dynamic_topology_sculpting


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer.command_catalog import action_by_id
    from pie_customizer.discovery import (
        BrowserAction,
        broad_category_for_action,
        discover_operator_actions,
    )

    _assert_sculpt_schemas()
    mirror_x = action_by_id("sculpt_mirror_x")
    assert mirror_x is not None
    assert mirror_x.command == "context.object.data.use_mirror_x"

    discovered = {action.item_id: action for action in discover_operator_actions()}
    expected_sculpt_ids = {
        "object.voxel_remesh",
        "object.voxel_size_edit",
        "paint.hide_show",
        "paint.mask_flood_fill",
        "paint.visibility_invert",
        "sculpt.brush_stroke",
        "sculpt_curves.brush_stroke",
    }
    for operator_id in expected_sculpt_ids:
        action = discovered.get(operator_id)
        assert action is not None, operator_id
        assert broad_category_for_action(action) == "SCULPT", operator_id

    for operator_id in ("brush.asset_select", "paint.brush_colors_flip"):
        action = discovered.get(operator_id)
        if action is None:
            action = BrowserAction(
                operator_id,
                "OPERATOR",
                operator_id,
                operator_id.split(".", 1)[0],
                operator_id,
                "",
                f"{operator_id}()",
                "NONE",
                "OPERATOR",
            )
        assert broad_category_for_action(action) != "SCULPT", operator_id

    _exercise_mirror_x_property()

    if bpy.app.background:
        print("SCULPT_EXECUTION_SKIPPED_BACKGROUND_UNDO")
    else:
        _exercise_sculpt_actions()

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_SCULPT_CATALOG_SMOKE_OK")


if __name__ == "__main__":
    main()
