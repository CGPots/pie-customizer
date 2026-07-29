"""End-to-end release smoke test. Run with Blender --factory-startup --python."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy


class OperatorResult:
    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)


class Layout:
    def __init__(self):
        self.operator_ids = []

    def operator(self, operator_id, *args, **kwargs):
        self.operator_ids.append(operator_id)
        return OperatorResult()

    def __getattr__(self, name):
        return lambda *args, **kwargs: self


class PreferencesProxy:
    def __init__(self, addon_preferences):
        self._preferences = addon_preferences
        self.layout = Layout()

    def __getattr__(self, name):
        return getattr(self._preferences, name)


def main() -> None:
    extra_path = None
    if "--" in sys.argv:
        extra_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, extra_path)

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import localization, operator_parameters, operators, preferences, runtime
    from pie_customizer.action_parser import parse_operator_command
    from pie_customizer.command_catalog import VIEWPORT_TOGGLE_ACTIONS

    property_rna_roots = {
        "context.space_data.overlay.": bpy.types.View3DOverlay,
        "context.space_data.shading.": bpy.types.View3DShading,
        "context.space_data.": bpy.types.SpaceView3D,
        "context.scene.tool_settings.": bpy.types.ToolSettings,
    }
    for action in VIEWPORT_TOGGLE_ACTIONS:
        matching_prefix = next(
            (prefix for prefix in property_rna_roots if action.command.startswith(prefix)),
            None,
        )
        assert matching_prefix is not None, action.command
        property_name = action.command.removeprefix(matching_prefix)
        rna_property = property_rna_roots[matching_prefix].bl_rna.properties.get(property_name)
        assert rna_property is not None, action.command
        assert rna_property.type == "BOOLEAN", action.command

    convert_target = bpy.ops.object.convert.get_rna_type().properties["target"]
    convert_values = {
        item.identifier for item in convert_target.enum_items_static if item.identifier
    }
    if "GREASEPENCIL" in convert_values and "GPENCIL" not in convert_values:
        normalized = runtime.normalize_operator_command(
            "object.convert(target='GPENCIL')"
        )
        assert parse_operator_command(normalized).kwargs["target"] == "GREASEPENCIL"
    elif "GPENCIL" in convert_values and "GREASEPENCIL" not in convert_values:
        normalized = runtime.normalize_operator_command(
            "object.convert(target='GREASEPENCIL')"
        )
        assert parse_operator_command(normalized).kwargs["target"] == "GPENCIL"

    try:
        runtime.normalize_operator_command(
            "object.convert(target='PIE_CUSTOMIZER_INVALID_TARGET')"
        )
    except ValueError as exc:
        assert "object.convert.target" in str(exc)
        assert bpy.app.version_string in str(exc)
    else:
        raise AssertionError("An invalid cross-version enum was accepted")

    technical_slot = SimpleNamespace(
        command=(
            "wm.context_set_enum("
            "data_path='space_data.shading.type', value='SOLID')"
        )
    )
    assert not preferences._slot_has_operator_parameters(technical_slot)

    searchable_actions = preferences._searchable_browser_actions(None)
    searchable_ids = {action.item_id for action in searchable_actions}
    assert "overlay_objects_relationships" in searchable_ids
    assert "viewport_gizmo_move" in searchable_ids
    assert "object_visibility_mesh" in searchable_ids
    assert "snap_option_enabled" in searchable_ids
    assert "mode_texture_paint" in searchable_ids
    assert "paint_flip_colors" in searchable_ids
    assert "PAINT" in preferences.BROAD_CATEGORY_MAP
    assert "NODES" in preferences.BROAD_CATEGORY_MAP

    try:
        runtime.run_operator_command(
            "object.set_proportional_falloff()",
            "EXEC_DEFAULT",
        )
    except ValueError as exc:
        assert "Falloff" in str(exc) or "Спад" in str(exc)
    else:
        raise AssertionError("Unsafe proportional falloff wrapper was executed")

    try:
        runtime.run_operator_command(
            "object.origin_set_any_mode()",
            "EXEC_DEFAULT",
        )
    except ValueError as exc:
        assert "Origin" in str(exc)
    else:
        raise AssertionError("Unsafe origin wrapper was executed")

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    assert len(prefs.pie_menus) == 0
    assert not hasattr(prefs, "ui_language")

    view = bpy.context.preferences.view
    original_language = view.language
    original_translate_interface = view.use_translate_interface
    original_translate_tooltips = view.use_translate_tooltips
    view.language = "en_US"
    view.use_translate_interface = True
    view.use_translate_tooltips = True
    assert localization.effective_language(bpy.context) == "EN"
    assert bpy.app.translations.pgettext_iface("Catalog") == "Catalog"
    assert (
        bpy.app.translations.pgettext_tip("Position of the slot inside the pie menu")
        == "Position of the slot inside the pie menu"
    )
    view.language = "ru_RU"
    assert localization.effective_language(bpy.context) == "RU"
    assert bpy.app.translations.pgettext_iface("Catalog") == "Каталог"
    assert (
        bpy.app.translations.pgettext_tip("Position of the slot inside the pie menu")
        == "Позиция слота внутри pie menu"
    )
    view.use_translate_interface = False
    assert localization.effective_language(bpy.context) == "EN"
    view.language = original_language
    view.use_translate_interface = original_translate_interface
    view.use_translate_tooltips = original_translate_tooltips

    empty_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(empty_preferences, bpy.context)
    assert all(
        item[3] == "NONE"
        for items in preferences.CATALOG_BROWSE_MODE_ITEMS.values()
        for item in items
    )
    assert "pie_customizer.rebuild" not in empty_preferences.layout.operator_ids
    assert "pie_customizer.import_preset" in empty_preferences.layout.operator_ids
    assert "pie_customizer.export_preset" in empty_preferences.layout.operator_ids

    assert bpy.ops.pie_customizer.add_menu() == {"FINISHED"}
    first = prefs.pie_menus[0]
    first.name = "Main"
    first.key = "F6"
    assert len(first.slots) == 8
    assert all(not slot.enabled and slot.slot_type == "SEPARATOR" for slot in first.slots)

    populated_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(populated_preferences, bpy.context)
    assert "pie_customizer.rebuild" in populated_preferences.layout.operator_ids

    first.active_slot_position = "0"
    first.slots[0].slot_type = "OPERATOR"
    first.slots[0].enabled = True
    first.slots[0].command = "mesh.select_mode(type='FACE', action='ENABLE')"
    assert not operator_parameters.operator_has_editable_parameters("mesh.select_mode")
    assert not operator_parameters.operator_has_editable_parameters("transform.select_orientation")
    fixed_action_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(fixed_action_preferences, bpy.context)
    assert "pie_customizer.configure_operator" not in fixed_action_preferences.layout.operator_ids

    first.slots[0].command = "transform.select_orientation(orientation='LOCAL')"
    orientation_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(orientation_preferences, bpy.context)
    assert "pie_customizer.configure_operator" not in orientation_preferences.layout.operator_ids

    assert bpy.ops.pie_customizer.select_operator_group(group="mesh") == {"FINISHED"}
    assert prefs.operator_group == "mesh"
    assert bpy.ops.pie_customizer.select_operator_group(group="ALL") == {"FINISHED"}
    assert prefs.operator_group == "ALL"

    class SearchPopupWindowManager:
        def __init__(self):
            self.operator = None

        def invoke_search_popup(self, operator):
            self.operator = operator

    search_window_manager = SearchPopupWindowManager()
    search_context = type(
        "SearchContext",
        (),
        {"window_manager": search_window_manager},
    )()
    search_operator = object()
    assert (
        operators.PC_OT_SelectOperatorGroup.invoke(
            search_operator,
            search_context,
            None,
        )
        == {"RUNNING_MODAL"}
    )
    assert search_window_manager.operator is search_operator

    first.slots[0].command = "mesh.primitive_cube_add(size=1)"
    assert operator_parameters.operator_has_editable_parameters("mesh.primitive_cube_add")
    configurable_action_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(configurable_action_preferences, bpy.context)
    assert "pie_customizer.configure_operator" in configurable_action_preferences.layout.operator_ids

    first.slots[0].slot_type = "PROPERTY"
    first.slots[0].command = "context.space_data.overlay.show_relationship_lines"
    property_action_preferences = PreferencesProxy(prefs)
    preferences.PC_AddonPreferences.draw(property_action_preferences, bpy.context)
    assert "pie_customizer.configure_operator" not in property_action_preferences.layout.operator_ids

    assert bpy.ops.pie_customizer.assign_browser_action(
        item_id="object.select_all",
        label="Select All",
        command="object.select_all(action='SELECT')",
        icon="RESTRICT_SELECT_OFF",
        slot_type="OPERATOR",
        operator_context="EXEC_DEFAULT",
    ) == {"FINISHED"}

    assert bpy.ops.pie_customizer.add_menu() == {"FINISHED"}
    second = prefs.pie_menus[1]
    second.name = "Nested"
    second.key = "F7"
    assert bpy.ops.pie_customizer.assign_browser_action(
        item_id="mesh.primitive_cube_add",
        label="Cube",
        command="mesh.primitive_cube_add(size=1)",
        icon="MESH_CUBE",
        slot_type="OPERATOR",
        operator_context="INVOKE_DEFAULT",
    ) == {"FINISHED"}

    prefs.active_menu_index = 0
    first.active_slot_position = "1"
    assert bpy.ops.pie_customizer.assign_browser_action(
        item_id=second.uid,
        label=second.name,
        command=runtime.menu_id_for(second),
        icon="MENU_PANEL",
        slot_type="MENU",
        operator_context="INVOKE_DEFAULT",
    ) == {"FINISHED"}

    assert bpy.ops.pie_customizer.rebuild() == {"FINISHED"}
    assert hasattr(bpy.types, runtime.menu_id_for(first))
    assert hasattr(bpy.types, runtime.menu_id_for(second))

    prefs.active_menu_index = 0
    assert bpy.ops.pie_customizer.duplicate_menu() == {"FINISHED"}
    assert len(prefs.pie_menus) == 3
    assert bpy.ops.pie_customizer.remove_menu() == {"FINISHED"}
    assert len(prefs.pie_menus) == 2

    exported = runtime.serialize_menus(prefs)
    runtime.load_menus(prefs, exported, replace=True)
    assert len(prefs.pie_menus) == 2
    runtime.load_menus(prefs, exported, replace=False)
    assert len(prefs.pie_menus) == 4
    menu_ids = [runtime.menu_id_for(menu) for menu in prefs.pie_menus]
    assert len(menu_ids) == len(set(menu_ids))
    assert prefs.pie_menus[2].slots[1].command == runtime.menu_id_for(prefs.pie_menus[3])

    before_invalid_import = runtime.serialize_menus(prefs)
    try:
        runtime.load_menus(prefs, [{"keymap_context": "INVALID"}], replace=True)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid preset was accepted")
    assert runtime.serialize_menus(prefs) == before_invalid_import

    incompatible_operator_preset = [
        {
            "name": "Incompatible",
            "slots": [
                {
                    "slot_type": "OPERATOR",
                    "command": (
                        "object.convert("
                        "target='PIE_CUSTOMIZER_INVALID_TARGET')"
                    ),
                }
            ],
        }
    ]
    try:
        runtime.load_menus(
            prefs,
            incompatible_operator_preset,
            replace=True,
        )
    except ValueError as exc:
        assert "object.convert.target" in str(exc)
    else:
        raise AssertionError("Cross-version operator preset was accepted")
    assert runtime.serialize_menus(prefs) == before_invalid_import

    incompatible_type_preset = [
        {
            "name": "Incompatible type",
            "slots": [
                {
                    "slot_type": "OPERATOR",
                    "command": "object.convert(target=42)",
                }
            ],
        }
    ]
    try:
        runtime.load_menus(
            prefs,
            incompatible_type_preset,
            replace=True,
        )
    except ValueError as exc:
        assert "object.convert.target" in str(exc)
        assert bpy.app.version_string in str(exc)
    else:
        raise AssertionError("Invalid operator argument type was accepted")
    assert runtime.serialize_menus(prefs) == before_invalid_import

    with tempfile.TemporaryDirectory() as directory:
        preset_path = Path(directory) / "menus.json"
        assert bpy.ops.pie_customizer.export_preset(filepath=str(preset_path)) == {"FINISHED"}
        payload = json.loads(preset_path.read_text(encoding="utf-8"))
        assert payload["version"] == 1
        assert len(payload["pie_menus"]) == 4

        invalid_path = Path(directory) / "invalid.json"
        invalid_path.write_text('{"pie_menus": [{"slots": "invalid"}]}', encoding="utf-8")
        try:
            result = bpy.ops.pie_customizer.import_preset(
                filepath=str(invalid_path),
                merge_mode="REPLACE",
            )
        except RuntimeError as exc:
            assert "slots must be a list" in str(exc)
        else:
            assert result == {"CANCELLED"}
        assert runtime.serialize_menus(prefs) == before_invalid_import

    original_snap = bpy.context.scene.tool_settings.use_snap
    assert runtime.run_property_command(
        "context.scene.tool_settings.use_snap",
        bpy.context,
    ) == {"FINISHED"}
    assert bpy.context.scene.tool_settings.use_snap is not original_snap
    bpy.context.scene.tool_settings.use_snap = original_snap

    preferences.PC_AddonPreferences.draw(PreferencesProxy(prefs), bpy.context)

    runtime.unregister_dynamic_menus()
    assert not hasattr(bpy.types, menu_ids[0])
    addon_utils.disable("pie_customizer", default_set=True)
    if extra_path is not None:
        sys.path.remove(extra_path)
    print("PIE_CUSTOMIZER_RELEASE_SMOKE_OK")


if __name__ == "__main__":
    main()
