import unittest

from pie_customizer.action_parser import parse_operator_command, parse_property_command


class ActionParserTest(unittest.TestCase):
    def test_operator_id_without_call(self):
        parsed = parse_operator_command("object.delete")
        self.assertEqual(parsed.operator_id, "object.delete")
        self.assertEqual(parsed.kwargs, {})

    def test_operator_call_with_kwargs(self):
        parsed = parse_operator_command("bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False)")
        self.assertEqual(parsed.operator_id, "mesh.primitive_cube_add")
        self.assertEqual(parsed.kwargs, {"size": 2, "enter_editmode": False})

    def test_operator_call_supports_python_keyword_name(self):
        parsed = parse_operator_command("bmax.import()")
        self.assertEqual(parsed.operator_id, "bmax.import")
        self.assertEqual(parsed.kwargs, {})

    def test_keyword_named_operator_keeps_literal_only_kwargs(self):
        parsed = parse_operator_command(
            "bpy.ops.bmax.import(filepath='/tmp/example.fbx', enabled=True)"
        )
        self.assertEqual(parsed.operator_id, "bmax.import")
        self.assertEqual(
            parsed.kwargs,
            {"filepath": "/tmp/example.fbx", "enabled": True},
        )

    def test_operator_rejects_positional_args(self):
        with self.assertRaises(ValueError):
            parse_operator_command("object.select_all('SELECT')")

    def test_operator_rejects_executable_argument(self):
        with self.assertRaises(ValueError):
            parse_operator_command("object.delete(confirm=print('unsafe'))")

        with self.assertRaises(ValueError):
            parse_operator_command("bmax.import(filepath=print('unsafe'))")

    def test_operator_rejects_expression_after_keyword_named_call(self):
        with self.assertRaises(ValueError):
            parse_operator_command("bmax.import().__class__")

    def test_operator_supports_literal_collections_and_signed_numbers(self):
        parsed = parse_operator_command(
            "object.example(offset=(-1, +2.5), names=['A', 'B'], flags={'X'})"
        )
        self.assertEqual(parsed.kwargs["offset"], (-1, 2.5))
        self.assertEqual(parsed.kwargs["names"], ["A", "B"])
        self.assertEqual(parsed.kwargs["flags"], {"X"})

    def test_property_toggle(self):
        parsed = parse_property_command("bpy.context.space_data.overlay.show_overlays")
        self.assertEqual(parsed.path, "context.space_data.overlay.show_overlays")
        self.assertFalse(parsed.has_value)

    def test_property_assignment(self):
        parsed = parse_property_command("context.scene.tool_settings.use_snap = True")
        self.assertEqual(parsed.path, "context.scene.tool_settings.use_snap")
        self.assertTrue(parsed.has_value)
        self.assertTrue(parsed.value)


if __name__ == "__main__":
    unittest.main()
