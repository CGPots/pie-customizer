"""Exercise the Mirror X seam-cleanup operator inside Blender."""

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


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

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

    result = bpy.ops.pie_customizer.add_mirror_x_clean_seam()
    assert result == {"FINISHED"}
    assert bpy.context.mode == "EDIT_MESH"

    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(active_object.data.polygons) == original_face_count - 1
    assert len(active_object.data.edges) == original_edge_count
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
    assert mirror_object.users_collection[0] in active_object.users_collection
    for row in range(4):
        for column in range(4):
            assert abs(
                mirror_object.matrix_world[row][column] - cursor_matrix[row][column]
            ) < 1e-6

    # Object Mode has no selected mesh faces, so the cap facing the mirror
    # plane must be found and deleted automatically.
    _clear_scene()
    bpy.ops.mesh.primitive_cube_add()
    active_object = bpy.context.active_object
    original_edge_count = len(active_object.data.edges)
    bpy.context.scene.cursor.location = (3.0, 0.0, 0.0)
    bpy.context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)

    result = bpy.ops.pie_customizer.add_mirror_x_clean_seam()
    assert result == {"FINISHED"}
    assert len(active_object.data.polygons) == 5
    assert len(active_object.data.edges) == original_edge_count
    assert not any(
        all(
            abs(active_object.data.vertices[index].co.x - 1.0) < 1e-6
            for index in polygon.vertices
        )
        for polygon in active_object.data.polygons
    )
    modifier = active_object.modifiers[0]
    assert modifier.mirror_object is not None
    assert modifier.mirror_object.name == "mrr"
    assert tuple(modifier.mirror_object.location) == (3.0, 0.0, 0.0)

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_MIRROR_X_CLEAN_SEAM_SMOKE_OK")


if __name__ == "__main__":
    main()
