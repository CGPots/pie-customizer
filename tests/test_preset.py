import unittest

from pie_customizer.preset import MAX_PRESET_MENUS, normalize_preset_items


class PresetValidationTest(unittest.TestCase):
    def test_normalizes_valid_menu_and_slot(self):
        menus = normalize_preset_items(
            [
                {
                    "uid": "menu-a",
                    "name": "Tools",
                    "slots": [
                        {
                            "slot_type": "OPERATOR",
                            "command": "object.delete()",
                            "label": "Delete",
                        }
                    ],
                }
            ]
        )

        self.assertEqual(menus[0]["uid"], "menu-a")
        self.assertTrue(menus[0]["slots"][0]["enabled"])
        self.assertEqual(menus[0]["slots"][0]["operator_context"], "INVOKE_DEFAULT")

    def test_rejects_non_object_menu(self):
        with self.assertRaisesRegex(ValueError, r"pie_menus\[0\]"):
            normalize_preset_items(["invalid"])

    def test_rejects_unknown_enum_value(self):
        with self.assertRaisesRegex(ValueError, "keymap_context"):
            normalize_preset_items([{"keymap_context": "UNKNOWN"}])

    def test_rejects_non_boolean_value(self):
        with self.assertRaisesRegex(ValueError, "enabled"):
            normalize_preset_items([{"enabled": "yes"}])

    def test_limits_menu_count(self):
        with self.assertRaisesRegex(ValueError, str(MAX_PRESET_MENUS)):
            normalize_preset_items([{}] * (MAX_PRESET_MENUS + 1))


if __name__ == "__main__":
    unittest.main()
