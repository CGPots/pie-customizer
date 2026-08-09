import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "pie_customizer" / "quick_add_data.py"
SPEC = importlib.util.spec_from_file_location("quick_add_data", MODULE_PATH)
quick_add_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(quick_add_data)


class Slot:
    def __init__(self, enabled=False, slot_type="SEPARATOR", command=""):
        self.enabled = enabled
        self.slot_type = slot_type
        self.command = command


class Descriptor:
    def __init__(self, identifier, property_type="POINTER", is_array=False):
        self.identifier = identifier
        self.type = property_type
        self.is_array = is_array


class Pointer:
    _next_pointer = 1

    def __init__(self, rna_identifier="Pointer", pointer=None, **children):
        if pointer is None:
            pointer = Pointer._next_pointer
            Pointer._next_pointer += 1
        self._pointer = pointer
        descriptors = [Descriptor("rna_type")]
        for name, child in children.items():
            setattr(self, name, child)
            descriptors.append(Descriptor(name))
        self.bl_rna = type(
            "RNA",
            (),
            {"identifier": rna_identifier, "properties": descriptors},
        )()

    def as_pointer(self):
        return self._pointer


class Context:
    def __init__(self, **values):
        self._values = values
        for name, value in values.items():
            setattr(self, name, value)

    def copy(self):
        return dict(self._values)


class QuickAddDataTests(unittest.TestCase):
    def test_normalizes_scalar_values(self):
        self.assertEqual(quick_add_data.normalize_rna_value("BOOLEAN", False, True), True)
        self.assertEqual(quick_add_data.normalize_rna_value("INT", False, 3), 3)
        self.assertEqual(quick_add_data.normalize_rna_value("FLOAT", False, 1.5), 1.5)
        self.assertEqual(quick_add_data.normalize_rna_value("STRING", False, "Cube"), "Cube")

    def test_normalizes_arrays_and_enum_flags(self):
        self.assertEqual(
            quick_add_data.normalize_rna_value("FLOAT", True, [1.0, 2.0, 3.0]),
            (1.0, 2.0, 3.0),
        )
        self.assertEqual(
            quick_add_data.normalize_rna_value("ENUM", False, {"A", "B"}),
            {"A", "B"},
        )

    def test_rejects_pointer_and_nested_values(self):
        with self.assertRaises(TypeError):
            quick_add_data.normalize_rna_value("POINTER", False, object())
        with self.assertRaises(TypeError):
            quick_add_data.normalize_rna_value("FLOAT", True, [1.0, object()])

    def test_occupied_slot_requires_enabled_command_action(self):
        self.assertFalse(quick_add_data.slot_is_occupied(None))
        self.assertFalse(quick_add_data.slot_is_occupied(Slot(True, "SEPARATOR", "")))
        self.assertFalse(quick_add_data.slot_is_occupied(Slot(False, "OPERATOR", "object.delete()")))
        self.assertTrue(quick_add_data.slot_is_occupied(Slot(True, "OPERATOR", "object.delete()")))

    def test_finds_direct_and_nested_context_pointer_paths(self):
        overlay = Pointer()
        space = Pointer(overlay=overlay)
        tool_settings = Pointer()
        context = Context(space_data=space, tool_settings=tool_settings)

        self.assertEqual(
            quick_add_data.find_context_pointer_path(context, tool_settings),
            "context.tool_settings",
        )
        self.assertEqual(
            quick_add_data.find_context_pointer_path(context, overlay),
            "context.space_data.overlay",
        )

    def test_distinguishes_embedded_rna_types_that_share_a_pointer(self):
        overlay = Pointer(rna_identifier="View3DOverlay", pointer=500)
        space = Pointer(rna_identifier="SpaceView3D", pointer=500, overlay=overlay)
        context = Context(space_data=space)

        self.assertEqual(
            quick_add_data.find_context_pointer_path(context, overlay),
            "context.space_data.overlay",
        )

    def test_accepts_only_whitelisted_reusable_property_owners(self):
        overlay = Pointer(rna_identifier="View3DOverlay")
        shading = Pointer(rna_identifier="View3DShading")
        space = Pointer(rna_identifier="SpaceView3D", overlay=overlay, shading=shading)
        space.type = "VIEW_3D"
        tool_settings = Pointer()
        scene = Pointer(tool_settings=tool_settings)
        context = Context(scene=scene, space_data=space, tool_settings=tool_settings)

        self.assertEqual(
            quick_add_data.supported_property_owner_path(context, tool_settings),
            "context.scene.tool_settings",
        )
        self.assertEqual(
            quick_add_data.supported_property_owner_path(context, overlay),
            "context.space_data.overlay",
        )
        self.assertEqual(
            quick_add_data.supported_property_owner_path(context, shading),
            "context.space_data.shading",
        )

        space.type = "PROPERTIES"
        self.assertEqual(quick_add_data.supported_property_owner_path(context, overlay), "")

    def test_accepts_main_transform_orientation_slot(self):
        orientation = Pointer(rna_identifier="TransformOrientationSlot")
        scene = Pointer()
        scene.transform_orientation_slots = [orientation]
        space = Pointer(rna_identifier="SpaceView3D")
        space.type = "VIEW_3D"
        context = Context(scene=scene, space_data=space)

        self.assertEqual(
            quick_add_data.supported_property_owner_path(context, orientation),
            "context.scene.transform_orientation_slots[0]",
        )

    def test_accepts_direct_and_nested_editor_property_owners(self):
        node_overlay = Pointer(rna_identifier="SpaceNodeOverlay")
        node_space = Pointer(rna_identifier="SpaceNodeEditor", overlay=node_overlay)
        node_space.type = "NODE_EDITOR"
        node_context = Context(space_data=node_space)
        self.assertEqual(
            quick_add_data.supported_property_owner_path(node_context, node_space),
            "context.space_data",
        )
        self.assertEqual(
            quick_add_data.supported_property_owner_path(node_context, node_overlay),
            "context.space_data.overlay",
        )

        uv_editor = Pointer(rna_identifier="SpaceUVEditor")
        image_space = Pointer(rna_identifier="SpaceImageEditor", uv_editor=uv_editor)
        image_space.type = "IMAGE_EDITOR"
        image_context = Context(space_data=image_space)
        self.assertEqual(
            quick_add_data.supported_property_owner_path(image_context, uv_editor),
            "context.space_data.uv_editor",
        )

    def test_rejects_mismatched_space_rna_and_returns_stable_keymaps(self):
        fake_node_space = Pointer(rna_identifier="SpaceView3D")
        fake_node_space.type = "NODE_EDITOR"
        context = Context(space_data=fake_node_space)
        self.assertEqual(
            quick_add_data.supported_property_owner_path(context, fake_node_space),
            "",
        )
        self.assertEqual(quick_add_data.context_space_type(context), "")
        real_node_space = Pointer(rna_identifier="SpaceNodeEditor")
        real_node_space.type = "NODE_EDITOR"
        self.assertEqual(
            quick_add_data.context_space_type(Context(space_data=real_node_space)),
            "NODE_EDITOR",
        )
        self.assertEqual(
            quick_add_data.keymap_settings_for_space_type("NODE_EDITOR"),
            ("NODE_EDITOR", "Node Editor", "NODE_EDITOR", "WINDOW"),
        )
        self.assertEqual(
            quick_add_data.keymap_settings_for_space_type("SEQUENCE_EDITOR"),
            ("CUSTOM", "Sequencer", "SEQUENCE_EDITOR", "WINDOW"),
        )
        self.assertIsNone(
            quick_add_data.keymap_settings_for_space_type("PREFERENCES")
        )

    def test_rejects_arbitrary_context_property_owners(self):
        target = Pointer()
        context = Context(object=target)
        self.assertEqual(quick_add_data.supported_property_owner_path(context, target), "")

    def test_ignores_unstable_collection_only_targets(self):
        target = Pointer()
        context = Context(selected_objects=[target])
        self.assertEqual(quick_add_data.find_context_pointer_path(context, target), "")

    def test_formats_toggle_assignments_and_enum_sets(self):
        path = "context.tool_settings.snap_target"
        self.assertEqual(quick_add_data.format_property_command(path), path)
        self.assertEqual(
            quick_add_data.format_property_command(path, "CENTER"),
            "context.tool_settings.snap_target = 'CENTER'",
        )
        self.assertEqual(
            quick_add_data.format_property_command(path, {"EDGE", "VERTEX"}),
            "context.tool_settings.snap_target = {'EDGE', 'VERTEX'}",
        )


if __name__ == "__main__":
    unittest.main()
