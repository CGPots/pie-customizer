"""Execute context-safe curated actions in a disposable Blender session."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import addon_utils
import bpy


CONTEXT_ONLY_ACTIONS = {
    "move",
    "rotate",
    "scale",
    "mirror",
    "duplicate_object",
    "sculpt_voxel_size",
    "mesh_extrude",
    "mesh_loop_cut",
    "paint_sample_color",
}

BACKGROUND_UNDO_ACTIONS = {
    "sculpt_voxel_remesh",
    "sculpt_dyntopo_toggle",
    "sculpt_symmetrize",
    "sculpt_mask_fill",
    "sculpt_mask_clear",
    "sculpt_mask_invert",
}


def _operator(operator_id: str):
    namespace, name = operator_id.split(".", 1)
    return getattr(getattr(bpy.ops, namespace), name)


def _object_mode() -> None:
    if bpy.context.object is not None and bpy.context.mode != "OBJECT":
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except RuntimeError:
            pass


def _clear_scene() -> None:
    _object_mode()
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _add_cube() -> None:
    _clear_scene()
    bpy.ops.mesh.primitive_cube_add()


def _prepare_action(action) -> None:
    if action.action_id == "mode_pose":
        _clear_scene()
        bpy.ops.object.armature_add()
        return

    if action.action_id == "join_objects":
        _clear_scene()
        bpy.ops.mesh.primitive_cube_add(location=(-1.0, 0.0, 0.0))
        first = bpy.context.object
        bpy.ops.mesh.primitive_cube_add(location=(1.0, 0.0, 0.0))
        first.select_set(True)
        return

    _add_cube()
    if action.category == "MESH" or (
        action.category == "SELECT" and not action.action_id.endswith("_objects")
    ):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer.action_parser import parse_operator_command
    from pie_customizer.command_catalog import ACTIONS

    report = {
        "executed": [],
        "poll_false": [],
        "context_only": [],
        "background_undo": [],
        "cancelled": [],
        "errors": [],
    }

    for action in ACTIONS:
        if action.slot_type != "OPERATOR" or action.category == "VIEW":
            continue
        if action.action_id in CONTEXT_ONLY_ACTIONS:
            report["context_only"].append(action.action_id)
            continue
        if action.action_id in BACKGROUND_UNDO_ACTIONS:
            report["background_undo"].append(action.action_id)
            continue

        try:
            _prepare_action(action)
            parsed = parse_operator_command(action.command)
            operator = _operator(parsed.operator_id)
            if not operator.poll():
                report["poll_false"].append(action.action_id)
                continue
            result = operator("EXEC_DEFAULT", **parsed.kwargs)
            if "CANCELLED" in result:
                report["cancelled"].append(action.action_id)
            else:
                report["executed"].append(action.action_id)
        except Exception as exc:
            report["errors"].append(
                f"{action.action_id}: {type(exc).__name__}: {exc}"
            )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert not report["errors"], "Curated action execution raised exceptions"

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_CURATED_EXECUTION_SMOKE_OK")


if __name__ == "__main__":
    main()
