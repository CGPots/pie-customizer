import unittest
from unittest.mock import patch
from types import SimpleNamespace

from pie_customizer.operator_parameters import (
    _enum_default,
    _is_editable_property,
    operator_has_editable_parameters,
    parameters_to_kwargs,
)


class OperatorParametersTest(unittest.TestCase):
    def test_editable_property_filter_matches_parameter_editor(self):
        editable = SimpleNamespace(
            identifier="size",
            type="FLOAT",
            is_readonly=False,
            is_hidden=False,
            is_array=False,
        )
        hidden = SimpleNamespace(**{**editable.__dict__, "identifier": "type", "is_hidden": True})
        array = SimpleNamespace(**{**editable.__dict__, "identifier": "location", "is_array": True})
        unsupported = SimpleNamespace(**{**editable.__dict__, "identifier": "data", "type": "POINTER"})
        dynamic_enum = SimpleNamespace(
            **{
                **editable.__dict__,
                "identifier": "orientation",
                "type": "ENUM",
                "enum_items_static": (),
            }
        )

        self.assertTrue(_is_editable_property(editable))
        self.assertFalse(_is_editable_property(hidden))
        self.assertFalse(_is_editable_property(array))
        self.assertFalse(_is_editable_property(unsupported))
        self.assertFalse(_is_editable_property(dynamic_enum))

    def test_enabled_values_are_serialized_by_type(self):
        parameters = (
            SimpleNamespace(identifier="enabled", enabled=True, value_type="BOOLEAN", bool_value=True),
            SimpleNamespace(identifier="count", enabled=True, value_type="INT", int_value=3),
            SimpleNamespace(identifier="factor", enabled=True, value_type="FLOAT", float_value=0.25),
            SimpleNamespace(identifier="mode", enabled=True, value_type="ENUM", enum_value="CENTER"),
            SimpleNamespace(identifier="flags", enabled=True, value_type="ENUM_FLAG", string_value="A, B"),
            SimpleNamespace(identifier="name", enabled=True, value_type="STRING", string_value="Example"),
            SimpleNamespace(identifier="ignored", enabled=False, value_type="STRING", string_value="No"),
        )

        self.assertEqual(
            parameters_to_kwargs(parameters),
            {
                "enabled": True,
                "count": 3,
                "factor": 0.25,
                "mode": "CENTER",
                "flags": {"A", "B"},
                "name": "Example",
            },
        )

    def test_boolean_mode_combines_default_and_value(self):
        parameters = (
            SimpleNamespace(identifier="default", enabled=True, value_type="BOOLEAN", bool_mode="DEFAULT"),
            SimpleNamespace(identifier="on", enabled=False, value_type="BOOLEAN", bool_mode="TRUE"),
            SimpleNamespace(identifier="off", enabled=False, value_type="BOOLEAN", bool_mode="FALSE"),
        )

        self.assertEqual(parameters_to_kwargs(parameters), {"on": True, "off": False})

    def test_context_operator_without_rna_hides_parameter_button(self):
        operator = SimpleNamespace(
            get_rna_type=lambda: (_ for _ in ()).throw(KeyError("context RNA unavailable"))
        )
        bpy = SimpleNamespace(
            ops=SimpleNamespace(node=SimpleNamespace(add_search=operator))
        )
        with patch.dict("sys.modules", {"bpy": bpy}):
            self.assertFalse(operator_has_editable_parameters("node.add_search"))

    def test_enum_default_uses_rna_default_instead_of_first_item(self):
        items = (
            SimpleNamespace(identifier="CURVE"),
            SimpleNamespace(identifier="MESH"),
        )
        prop = SimpleNamespace(default="MESH")

        self.assertEqual(_enum_default(prop, items), "MESH")

    def test_enum_default_falls_back_when_rna_default_is_unavailable(self):
        items = (SimpleNamespace(identifier="CURVE"),)
        prop = SimpleNamespace(default="")

        self.assertEqual(_enum_default(prop, items), "CURVE")


if __name__ == "__main__":
    unittest.main()
