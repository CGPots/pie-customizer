import unittest
from types import SimpleNamespace

from pie_customizer.action_parser import parse_operator_command, parse_property_command
from pie_customizer.command_catalog import (
    ACTIONS,
    SEARCH_ACTIONS,
    VIEWPORT_TOGGLE_ACTIONS,
    action_by_id,
    apply_action,
    catalog_action_group,
)


class CommandCatalogTest(unittest.TestCase):
    def test_action_ids_are_unique(self):
        action_ids = [action.action_id for action in SEARCH_ACTIONS]
        self.assertEqual(len(action_ids), len(set(action_ids)))

    def test_commands_are_parseable(self):
        for action in SEARCH_ACTIONS:
            with self.subTest(action=action.action_id):
                if action.slot_type == "OPERATOR":
                    parse_operator_command(action.command)
                elif action.slot_type == "PROPERTY":
                    parse_property_command(action.command)

    def test_apply_action_populates_slot(self):
        action = action_by_id("add_cube")
        slot = SimpleNamespace()
        apply_action(slot, action, "RU")
        self.assertTrue(slot.enabled)
        self.assertEqual(slot.label, "Куб")
        self.assertEqual(slot.icon, "MESH_CUBE")
        self.assertEqual(slot.command, "mesh.primitive_cube_add()")

    def test_transform_orientations_are_available_as_individual_actions(self):
        expected = {
            "GLOBAL",
            "LOCAL",
            "NORMAL",
            "GIMBAL",
            "VIEW",
            "CURSOR",
            "PARENT",
        }
        commands = {
            action.command
            for action in ACTIONS
            if action.action_id.startswith("orientation_")
        }
        self.assertEqual(
            commands,
            {f"transform.select_orientation(orientation='{value}')" for value in expected},
        )

    def test_common_variant_families_are_present(self):
        action_ids = {action.action_id for action in ACTIONS}
        expected = {
            "add_empty_image",
            "pivot_active",
            "falloff_random",
            "origin_cursor",
            "convert_grease_pencil",
            "mode_texture_paint",
            "paint_flip_colors",
            "paint_sample_color",
            "mode_sculpt",
            "sculpt_voxel_remesh",
            "sculpt_dyntopo_toggle",
            "sculpt_mask_fill",
            "sculpt_mask_clear",
            "sculpt_mask_invert",
            "sculpt_mirror_x",
            "mesh_mirror_x_clean_seam",
            "mesh_merge_collapse",
            "mesh_delete_only_faces",
            "select_mode_face",
            "toggle_objects",
            "view_back",
            "shading_rendered",
        }
        self.assertTrue(expected.issubset(action_ids))
        self.assertTrue(
            {"mesh_merge_first", "mesh_merge_last"}.isdisjoint(action_ids)
        )

    def test_sculpt_mirror_x_targets_the_mesh_symmetry_property(self):
        action = action_by_id("sculpt_mirror_x")
        self.assertIsNotNone(action)
        self.assertEqual(action.command, "context.object.data.use_mirror_x")

    def test_mesh_mirror_x_clean_seam_uses_the_addon_operator(self):
        action = action_by_id("mesh_mirror_x_clean_seam")
        self.assertIsNotNone(action)
        self.assertEqual(
            action.command,
            "pie_customizer.add_mirror_x_clean_seam()",
        )
        self.assertEqual(action.operator_context, "INVOKE_DEFAULT")

    def test_viewport_toggles_are_search_only_property_actions(self):
        self.assertGreaterEqual(len(VIEWPORT_TOGGLE_ACTIONS), 120)
        self.assertTrue(all(action.slot_type == "PROPERTY" for action in VIEWPORT_TOGGLE_ACTIONS))
        self.assertFalse(set(VIEWPORT_TOGGLE_ACTIONS) & set(ACTIONS))
        self.assertIsNotNone(action_by_id("overlay_objects_relationships"))
        self.assertIsNotNone(action_by_id("viewport_gizmo_move"))
        self.assertIsNotNone(action_by_id("snap_option_enabled"))
        self.assertIsNotNone(action_by_id("object_visibility_mesh"))
        self.assertIsNotNone(action_by_id("object_selectability_mesh"))

    def test_complete_snapping_controls_are_available(self):
        expected_commands = {
            "snap_base_closest": "context.scene.tool_settings.snap_target = 'CLOSEST'",
            "snap_base_active": "context.scene.tool_settings.snap_target = 'ACTIVE'",
            "snap_target_vertex": "context.scene.tool_settings.snap_elements_base = {'VERTEX'}",
            "snap_target_face_center": "context.scene.tool_settings.snap_elements_base = {'FACE_MIDPOINT'}",
            "snap_individual_face_project": "context.scene.tool_settings.snap_elements_individual = {'FACE_PROJECT'}",
            "snap_individual_face_nearest": "context.scene.tool_settings.snap_elements_individual = {'FACE_NEAREST'}",
            "snap_option_align_rotation": "context.scene.tool_settings.use_snap_align_rotation",
            "snap_option_selectable": "context.scene.tool_settings.use_snap_selectable",
            "snap_rotation_increment_standard": "context.scene.tool_settings.snap_angle_increment_3d = 0.08726646259971647",
            "snap_rotation_increment_precision": "context.scene.tool_settings.snap_angle_increment_3d_precision = 0.017453292519943295",
        }
        for action_id, command in expected_commands.items():
            with self.subTest(action=action_id):
                action = action_by_id(action_id)
                self.assertIsNotNone(action)
                self.assertEqual(action.command, command)
                self.assertEqual(catalog_action_group(action), "transform_snapping")

    def test_curated_actions_use_semantic_groups(self):
        expected = {
            "add_cube": "add_primitives",
            "add_empty": "add_empties",
            "move": "transform_basic",
            "clear_location": "transform_reset",
            "orientation_local": "transform_orientations",
            "pivot_cursor": "transform_pivots",
            "falloff_smooth": "transform_falloff",
            "shade_smooth": "object_shading",
            "origin_cursor": "object_origin",
            "convert_mesh": "object_convert",
            "mode_edit": "object_modes",
            "mode_texture_paint": "paint_modes",
            "paint_flip_colors": "paint_actions",
            "mesh_merge_center": "mesh_merge",
            "mesh_delete_faces": "mesh_delete",
            "mesh_mirror_x_clean_seam": "mesh_modeling",
            "select_mode_face": "mesh_select_mode",
            "select_all_objects": "select_objects",
            "select_all_mesh": "select_mesh",
            "view_left": "view_axes",
            "shading_solid": "view_display",
            "search_menu": "view_interface",
            "view_selected": "view_navigation",
            "mode_sculpt": "sculpt_actions",
            "sculpt_voxel_remesh": "sculpt_remesh",
            "sculpt_mask_fill": "sculpt_masks",
            "sculpt_mirror_x": "sculpt_symmetry",
            "sculpt_overlay_mask": "sculpt_display",
        }
        for action_id, group in expected.items():
            with self.subTest(action=action_id):
                self.assertEqual(catalog_action_group(action_by_id(action_id)), group)


if __name__ == "__main__":
    unittest.main()
