import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "pie_customizer" / "shortcuts.py"
SPEC = importlib.util.spec_from_file_location("pie_customizer_shortcuts", MODULE_PATH)
shortcuts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shortcuts)


class ShortcutSafetyTests(unittest.TestCase):
    def test_plain_pointer_navigation_is_blocked(self):
        for event_type in shortcuts.PLAIN_POINTER_EVENT_IDS:
            with self.subTest(event_type=event_type):
                self.assertTrue(shortcuts.is_unsafe_plain_shortcut(event_type))

    def test_plain_essential_keyboard_input_is_blocked(self):
        for event_type in shortcuts.PLAIN_KEYBOARD_EVENT_IDS:
            with self.subTest(event_type=event_type):
                self.assertTrue(shortcuts.is_unsafe_plain_shortcut(event_type))

    def test_modified_reserved_input_is_allowed(self):
        for modifier in ("ctrl", "shift", "alt", "oskey"):
            with self.subTest(modifier=modifier):
                self.assertFalse(
                    shortcuts.is_unsafe_plain_shortcut(
                        "LEFTMOUSE",
                        **{modifier: True},
                    )
                )
                self.assertFalse(
                    shortcuts.is_unsafe_plain_shortcut(
                        "SPACE",
                        **{modifier: True},
                    )
                )

    def test_regular_keys_and_extra_mouse_buttons_are_allowed(self):
        for event_type in ("A", "ONE", "F1", "BUTTON4MOUSE", "BUTTON5MOUSE"):
            with self.subTest(event_type=event_type):
                self.assertFalse(shortcuts.is_unsafe_plain_shortcut(event_type))

    def test_all_supported_trigger_types_have_blender_ids(self):
        self.assertEqual(
            shortcuts.EVENT_VALUE_IDS,
            {"PRESS", "RELEASE", "CLICK", "DOUBLE_CLICK", "CLICK_DRAG"},
        )
        self.assertEqual(shortcuts.normalize_event_value("Drag"), "CLICK_DRAG")
        self.assertEqual(shortcuts.event_value_display("CLICK_DRAG"), "Drag")

    def test_shortcut_display_can_include_trigger_type(self):
        self.assertEqual(
            shortcuts.shortcut_display(
                "F8",
                ctrl=True,
                event_value="DOUBLE_CLICK",
            ),
            "Ctrl + F8 · Double Click",
        )


if __name__ == "__main__":
    unittest.main()
