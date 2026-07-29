import unittest

from pie_customizer.shortcuts import normalize_key_event, shortcut_display, update_modifier_state


class ShortcutTest(unittest.TestCase):
    def test_digit_keys_are_blender_event_ids(self):
        self.assertEqual(normalize_key_event("1"), "ONE")
        self.assertEqual(normalize_key_event("0"), "ZERO")

    def test_common_aliases(self):
        self.assertEqual(normalize_key_event("spacebar"), "SPACE")
        self.assertEqual(normalize_key_event("enter"), "RET")

    def test_display_keeps_user_friendly_digits(self):
        self.assertEqual(shortcut_display("1", alt=True), "Alt + 1")

    def test_modifier_state_tracks_press_and_release(self):
        state = {"ctrl": False, "shift": False, "alt": False, "oskey": False}
        update_modifier_state(state, "LEFT_ALT", "PRESS")
        self.assertTrue(state["alt"])
        update_modifier_state(state, "LEFT_ALT", "RELEASE")
        self.assertFalse(state["alt"])

    def test_modifier_state_keeps_multiple_modifiers(self):
        state = {"ctrl": False, "shift": False, "alt": False, "oskey": False}
        update_modifier_state(state, "LEFT_CTRL", "PRESS")
        update_modifier_state(state, "LEFT_SHIFT", "PRESS")
        self.assertTrue(state["ctrl"])
        self.assertTrue(state["shift"])


if __name__ == "__main__":
    unittest.main()
