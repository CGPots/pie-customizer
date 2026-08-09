import unittest

from pie_customizer.preset import normalize_preset_items


class PresetShortcutEventTests(unittest.TestCase):
    def test_legacy_preset_defaults_to_press(self):
        menus = normalize_preset_items([{"name": "Legacy", "slots": []}])
        self.assertEqual(menus[0]["event_value"], "PRESS")

    def test_all_shortcut_event_types_round_trip_through_validation(self):
        event_values = ("PRESS", "RELEASE", "CLICK", "DOUBLE_CLICK", "CLICK_DRAG")
        menus = normalize_preset_items(
            [
                {"name": event_value, "event_value": event_value, "slots": []}
                for event_value in event_values
            ]
        )
        self.assertEqual(
            [menu["event_value"] for menu in menus],
            list(event_values),
        )

    def test_drag_label_is_imported_as_blender_click_drag_value(self):
        menus = normalize_preset_items(
            [{"name": "Drag", "event_value": "DRAG", "slots": []}]
        )
        self.assertEqual(menus[0]["event_value"], "CLICK_DRAG")

    def test_unknown_shortcut_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "event_value"):
            normalize_preset_items(
                [{"name": "Invalid", "event_value": "HOLD", "slots": []}]
            )


if __name__ == "__main__":
    unittest.main()
