"""Exercise both geometry choices of the Mirror X operator inside Blender."""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def _clear_scene() -> None:
    if bpy.context.object is not None and bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _assert_mirror_setup(active_object, cursor_matrix) -> None:
    assert len(active_object.modifiers) == 1
    modifier = active_object.modifiers[0]
    assert modifier.type == "MIRROR"
    assert tuple(modifier.use_axis) == (True, False, False)
    assert modifier.use_clip
    assert modifier.use_mirror_merge
    assert abs(modifier.merge_threshold - 0.001) < 1e-8
    assert not modifier.use_bisect_axis[0]

    mirror_object = modifier.mirror_object
    assert mirror_object is not None
    assert mirror_object.type == "EMPTY"
    assert mirror_object.empty_display_type == "PLAIN_AXES"
    assert mirror_object.name == "mrr"
    for row in range(4):
        for column in range(4):
            assert abs(
                mirror_object.matrix_world[row][column] - cursor_matrix[row][column]
            ) < 1e-6


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    # Delete enabled: a selected face is removed while boundary edges remain.
    _clear_scene()
    bpy.ops.mesh.primitive_cube_add()
    active_object = bpy.context.active_object
    original_face_count = len(active_object.data.polygons)
    original_edge_count = len(active_object.data.edges)
    bpy.context.scene.cursor.location = (1.25, -2.5, 0.75)
    bpy.context.scene.cursor.rotation_euler = (0.1, 0.2, 0.3)
    cursor_matrix = bpy.context.scene.cursor.matrix.copy()

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    active_object.data.polygons[0].select = True
    bpy.ops.object.mode_set(mode="EDIT")

    result = bpy.ops.pie_customizer.add_mirror_x_clean_seam(
        delete_selected_faces=True,
    )
    assert result == {"FINISHED"}
    assert bpy.context.mode == "EDIT_MESH"

    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(active_object.data.polygons) == original_face_count - 1
    assert len(active_object.data.edges) == original_edge_count
    _assert_mirror_setup(active_object, cursor_matrix)

    # Delete disabled: the cube is untouched but the Empty and modifier are added.
    _clear_scene()
    bpy.ops.mesh.primitive_cube_add()
    active_object = bpy.context.active_object
    original_face_count = len(active_object.data.polygons)
    original_edge_count = len(active_object.data.edges)
    bpy.context.scene.cursor.location = (3.0, 0.0, 0.0)
    bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
    cursor_matrix = bpy.context.scene.cursor.matrix.copy()

    result = bpy.ops.pie_customizer.add_mirror_x_clean_seam(
        delete_selected_faces=False,
    )
    assert result == {"FINISHED"}
    assert len(active_object.data.polygons) == original_face_count
    assert len(active_object.data.edges) == original_edge_count
    _assert_mirror_setup(active_object, cursor_matrix)

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_MIRROR_X_CLEAN_SEAM_SMOKE_OK")


if __name__ == "__main__":
    main()
