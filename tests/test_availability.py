import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "pie_customizer" / "availability.py"
SPEC = importlib.util.spec_from_file_location("pie_customizer_availability", MODULE_PATH)
availability = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(availability)


class AvailabilityTests(unittest.TestCase):
    def test_unrestricted_menu_matches_every_mode(self):
        self.assertTrue(availability.menu_matches_mode(False, set(), "OBJECT"))
        self.assertTrue(availability.menu_matches_mode(False, set(), "SCULPT"))

    def test_specific_modes_use_or_logic(self):
        selected = {"OBJECT", "SCULPT"}
        self.assertTrue(availability.menu_matches_mode(True, selected, "OBJECT"))
        self.assertTrue(availability.menu_matches_mode(True, selected, "SCULPT"))
        self.assertFalse(availability.menu_matches_mode(True, selected, "EDIT_MESH"))

    def test_any_edit_mode_matches_old_and_new_edit_identifiers(self):
        self.assertTrue(availability.menu_matches_mode(True, {"EDIT_ANY"}, "EDIT_MESH"))
        self.assertTrue(
            availability.menu_matches_mode(True, {"EDIT_ANY"}, "EDIT_GREASE_PENCIL")
        )
        self.assertFalse(availability.menu_matches_mode(True, {"EDIT_ANY"}, "OBJECT"))

    def test_version_aliases_are_supported(self):
        self.assertTrue(
            availability.menu_matches_mode(
                True, {"EDIT_POINT_CLOUD"}, "EDIT_POINT_CLOUD"
            )
        )
        self.assertTrue(
            availability.menu_matches_mode(True, {"EDIT_POINT_CLOUD"}, "EDIT_POINTCLOUD")
        )
        self.assertTrue(
            availability.menu_matches_mode(True, {"GP_DRAW"}, "PAINT_GPENCIL")
        )
        self.assertTrue(
            availability.menu_matches_mode(True, {"GP_DRAW"}, "PAINT_GREASE_PENCIL")
        )

    def test_empty_restricted_filter_is_unavailable(self):
        self.assertFalse(availability.menu_matches_mode(True, set(), "OBJECT"))

    def test_any_edit_mode_removes_redundant_specific_edit_modes(self):
        selected = availability.normalized_mode_selection(
            {"EDIT_ANY", "EDIT_MESH", "SCULPT"}
        )
        self.assertEqual(selected, {"EDIT_ANY", "SCULPT"})

    def test_supported_filter_ids_follow_blender_version(self):
        blender_42 = {"OBJECT", "EDIT_MESH", "EDIT_POINT_CLOUD", "PAINT_GPENCIL"}
        blender_52 = {
            "OBJECT",
            "EDIT_MESH",
            "EDIT_POINTCLOUD",
            "PAINT_GREASE_PENCIL",
        }
        for identifiers in (blender_42, blender_52):
            supported = availability.supported_filter_ids(identifiers)
            self.assertIn("OBJECT", supported)
            self.assertIn("EDIT_ANY", supported)
            self.assertIn("EDIT_POINT_CLOUD", supported)
            self.assertIn("GP_DRAW", supported)


if __name__ == "__main__":
    unittest.main()
