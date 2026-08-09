import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "pie_customizer" / "command_catalog.py"
SPEC = importlib.util.spec_from_file_location("command_catalog", MODULE_PATH)
command_catalog = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = command_catalog
SPEC.loader.exec_module(command_catalog)


class MirrorXCatalogTests(unittest.TestCase):
    def test_mirror_x_action_opens_operator_options(self):
        action = command_catalog.action_by_id("mesh_mirror_x_clean_seam")

        self.assertIsNotNone(action)
        self.assertEqual(action.label_ru, "Зеркало X от курсора")
        self.assertEqual(action.label_en, "Mirror X from Cursor")
        self.assertEqual(action.operator_context, "INVOKE_DEFAULT")


if __name__ == "__main__":
    unittest.main()
