"""Smoke-test the v1.1 quick-add prototype inside Blender."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy


class FakeProperties:
    def __init__(self, identifier, name, descriptors, values, explicitly_set):
        self.bl_rna = SimpleNamespace(
            identifier=identifier,
            name=name,
            properties=descriptors,
        )
        self._explicitly_set = set(explicitly_set)
        for key, value in values.items():
            setattr(self, key, value)

    def is_property_set(self, identifier):
        return identifier in self._explicitly_set


class RecordingLayout:
    def __init__(self):
        self.entries = []

    def separator(self):
        self.entries.append(("SEPARATOR", None))

    def operator(self, operator_id, text, icon):
        properties = SimpleNamespace()
        self.entries.append((operator_id, properties, text, icon))
        return properties


def descriptor(identifier, property_type, is_array=False):
    return SimpleNamespace(identifier=identifier, type=property_type, is_array=is_array)


def shortcut_snapshot(keymap, keymap_item):
    return (
        keymap.name,
        keymap_item.idname,
        keymap_item.type,
        keymap_item.value,
        keymap_item.ctrl,
        keymap_item.shift,
        keymap_item.alt,
        keymap_item.oskey,
    )


def main():
    source_root = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    sys.path.insert(0, str(source_root))

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None
    assert tuple(module.ADDON_VERSION) == (1, 1, 3)

    from pie_customizer import availability, command_catalog, quick_add, runtime

    native_operator_layout = RecordingLayout()
    runtime._draw_slot(
        native_operator_layout,
        SimpleNamespace(
            enabled=True,
            slot_type="OPERATOR",
            icon="NONE",
            label="Merge by Distance",
            command="mesh.remove_doubles(use_unselected=True, threshold=0.001)",
            operator_context="EXEC_DEFAULT",
        ),
        bpy.context,
    )
    native_entry = native_operator_layout.entries[-1]
    assert native_entry[0] == "mesh.remove_doubles", native_entry
    assert native_entry[1].use_unselected is True
    assert native_entry[1].threshold == 0.001
    assert native_operator_layout.operator_context == "EXEC_DEFAULT"
    assert all(entry[0] != "pie_customizer.run_action" for entry in native_operator_layout.entries)

    wrapped_catalog_actions = []
    for action in command_catalog.SEARCH_ACTIONS:
        if action.slot_type != "OPERATOR":
            continue
        action_layout = RecordingLayout()
        runtime._draw_slot(
            action_layout,
            SimpleNamespace(
                enabled=True,
                slot_type=action.slot_type,
                icon=action.icon,
                label=action.label_en,
                command=action.command,
                operator_context=action.operator_context,
            ),
            bpy.context,
        )
        if action_layout.entries[-1][0] == "pie_customizer.run_action":
            wrapped_catalog_actions.append((action.action_id, action.command))
    assert not wrapped_catalog_actions, wrapped_catalog_actions

    assert quick_add._context_menu_registered
    assert quick_add._view3d_context_menu_types
    assert bpy.types.VIEW3D_MT_object_context_menu in quick_add._view3d_context_menu_types
    assert hasattr(bpy.ops.pie_customizer, "open_preferences")

    view3d_context_layout = RecordingLayout()
    quick_add.draw_view3d_context_menu(
        SimpleNamespace(layout=view3d_context_layout),
        bpy.context,
    )
    assert view3d_context_layout.entries[0][0] == "SEPARATOR"
    assert view3d_context_layout.entries[1][0] == "pie_customizer.open_preferences"

    captured = quick_add.capture_button_operator(
        SimpleNamespace(
            button_operator=FakeProperties(
                "MESH_OT_primitive_cube_add",
                "Add Cube",
                (
                    descriptor("rna_type", "POINTER"),
                    descriptor("size", "FLOAT"),
                    descriptor("align", "ENUM"),
                ),
                {"size": 2.5, "align": "WORLD"},
                {"size", "align"},
            )
        )
    )
    assert captured == {
        "operator_id": "mesh.primitive_cube_add",
        "label": "Add Cube",
        "command": "mesh.primitive_cube_add(size=2.5, align='WORLD')",
        "space_type": "",
    }

    class BMAX_OT_import(bpy.types.Operator):
        bl_idname = "bmax.import"
        bl_label = "Import from 3dsmax"

        def execute(self, context):
            context.scene["_pie_customizer_keyword_operator_ran"] = True
            return {"FINISHED"}

    bpy.utils.register_class(BMAX_OT_import)
    try:
        captured_keyword_operator = quick_add.capture_button_operator(
            SimpleNamespace(
                button_operator=FakeProperties(
                    "BMAX_OT_import",
                    "Import from 3dsmax",
                    (descriptor("rna_type", "POINTER"),),
                    {},
                    set(),
                )
            )
        )
        assert captured_keyword_operator == {
            "operator_id": "bmax.import",
            "label": "Import from 3dsmax",
            "command": "bmax.import()",
            "space_type": "",
        }
        assert runtime.normalize_operator_command("bmax.import()") == "bmax.import()"

        keyword_layout = RecordingLayout()
        runtime._draw_slot(
            keyword_layout,
            SimpleNamespace(
                enabled=True,
                slot_type="OPERATOR",
                icon="IMPORT",
                label="Get from 3dsmax",
                command="bmax.import()",
                operator_context="EXEC_DEFAULT",
            ),
            bpy.context,
        )
        assert keyword_layout.entries[-1][0] == "bmax.import"
        assert runtime.run_operator_command("bmax.import()", "EXEC_DEFAULT") == {"FINISHED"}
        assert bpy.context.scene.pop("_pie_customizer_keyword_operator_ran") is True
    finally:
        bpy.utils.unregister_class(BMAX_OT_import)

    unsupported = quick_add.capture_button_operator(
        SimpleNamespace(
            button_operator=FakeProperties(
                "OBJECT_OT_test_pointer",
                "Pointer Test",
                (descriptor("target", "POINTER"),),
                {"target": object()},
                {"target"},
            )
        )
    )
    assert unsupported is None
    assert quick_add.capture_button_operator(SimpleNamespace(button_operator=None)) is None

    tool_settings = bpy.context.scene.tool_settings
    use_snap_descriptor = tool_settings.bl_rna.properties["use_snap"]
    property_context = SimpleNamespace(
        button_operator=None,
        button_pointer=tool_settings,
        button_prop=use_snap_descriptor,
        scene=bpy.context.scene,
        tool_settings=tool_settings,
    )
    captured_property = quick_add.capture_button_property(property_context)
    assert captured_property["path"] == "context.scene.tool_settings.use_snap"
    assert captured_property["property_type"] == "BOOLEAN"
    assert captured_property["label"]

    snap_target_descriptor = tool_settings.bl_rna.properties["snap_target"]
    enum_context = SimpleNamespace(
        button_operator=None,
        button_pointer=tool_settings,
        button_prop=snap_target_descriptor,
        scene=bpy.context.scene,
        tool_settings=tool_settings,
    )
    captured_enum = quick_add.capture_button_property(enum_context)
    assert captured_enum["path"] == "context.scene.tool_settings.snap_target"
    assert captured_enum["property_type"] == "ENUM"
    assert "CENTER" in captured_enum["enum_items_json"]

    orientation_slot = bpy.context.scene.transform_orientation_slots[0]
    orientation_descriptor = orientation_slot.bl_rna.properties["type"]
    captured_orientation = quick_add.capture_button_property(
        SimpleNamespace(
            button_operator=None,
            button_pointer=orientation_slot,
            button_prop=orientation_descriptor,
            scene=bpy.context.scene,
            tool_settings=tool_settings,
        )
    )
    assert captured_orientation["path"] == (
        "context.scene.transform_orientation_slots[0].type"
    )
    assert "LOCAL" in captured_orientation["enum_items_json"]
    assert quick_add._enum_value_icon(
        captured_orientation["enum_items_json"],
        "LOCAL",
    ) == "ORIENTATION_LOCAL"
    assert quick_add._CATALOG_ICON_BY_COMMAND[
        "transform.select_orientation(orientation='LOCAL')"
    ] == "ORIENTATION_LOCAL"
    icon_probe = SimpleNamespace(
        suggested_icon="ORIENTATION_GLOBAL",
        slot_icon="ORIENTATION_GLOBAL",
        source_property_items_json=captured_orientation["enum_items_json"],
        property_enum_value="LOCAL",
    )
    quick_add._quick_add_property_value_updated(icon_probe, None)
    assert icon_probe.suggested_icon == "ORIENTATION_LOCAL"
    assert icon_probe.slot_icon == "ORIENTATION_LOCAL"
    icon_probe.slot_icon = "MESH_CUBE"
    icon_probe.property_enum_value = "NORMAL"
    quick_add._quick_add_property_value_updated(icon_probe, None)
    assert icon_probe.suggested_icon == "ORIENTATION_NORMAL"
    assert icon_probe.slot_icon == "MESH_CUBE"

    captured_pivot = quick_add.capture_button_operator(
        SimpleNamespace(
            button_operator=SimpleNamespace(
                data_path="scene.tool_settings.transform_pivot_point",
                value="CURSOR",
            )
        )
    )
    assert captured_pivot["operator_id"] == "wm.context_set_enum"
    assert captured_pivot["label"] == "Pivot: 3D Cursor"
    assert captured_pivot["command"] == (
        "wm.context_set_enum("
        "data_path='scene.tool_settings.transform_pivot_point', value='CURSOR')"
    )

    mesh_select_mode_descriptor = tool_settings.bl_rna.properties["mesh_select_mode"]
    assert quick_add.capture_button_property(
        SimpleNamespace(
            button_pointer=tool_settings,
            button_prop=mesh_select_mode_descriptor,
            scene=bpy.context.scene,
            tool_settings=tool_settings,
        )
    ) is None

    snap_elements_descriptor = tool_settings.bl_rna.properties["snap_elements_base"]
    captured_snap_elements = quick_add.capture_button_property(
        SimpleNamespace(
            button_pointer=tool_settings,
            button_prop=snap_elements_descriptor,
            scene=bpy.context.scene,
            tool_settings=tool_settings,
        )
    )
    assert captured_snap_elements["path"] == (
        "context.scene.tool_settings.snap_elements_base"
    )
    assert captured_snap_elements["is_enum_flag"]
    assert "VERTEX" in captured_snap_elements["enum_items_json"]

    view3d_space = next(
        area.spaces.active
        for screen in bpy.data.screens
        for area in screen.areas
        if area.type == "VIEW_3D"
    )
    show_stats_descriptor = view3d_space.overlay.bl_rna.properties["show_stats"]
    captured_overlay = quick_add.capture_button_property(
        SimpleNamespace(
            button_pointer=view3d_space.overlay,
            button_prop=show_stats_descriptor,
            scene=bpy.context.scene,
            space_data=view3d_space,
            tool_settings=tool_settings,
        )
    )
    assert captured_overlay, "Overlay property was not captured"
    assert captured_overlay["path"] == "context.space_data.overlay.show_stats", captured_overlay
    assert captured_overlay["property_type"] == "BOOLEAN"

    property_context.preferences = bpy.context.preferences
    property_menu = SimpleNamespace(layout=RecordingLayout())
    quick_add.draw_button_context_menu(property_menu, property_context)
    menu_entry = property_menu.layout.entries[-1]
    assert menu_entry[0] == "pie_customizer.quick_add_operator"
    assert menu_entry[1].source_action_type == "PROPERTY"
    assert menu_entry[1].source_property_path == "context.scene.tool_settings.use_snap"

    window = bpy.context.window_manager.windows[0]
    view3d_area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
    view3d_region = next(region for region in view3d_area.regions if region.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=view3d_area, region=view3d_region):
        show_stats_before = bpy.context.space_data.overlay.show_stats
        runtime.run_property_command(
            "context.space_data.overlay.show_stats",
            bpy.context,
        )
        assert bpy.context.space_data.overlay.show_stats is not show_stats_before
        bpy.context.space_data.overlay.show_stats = show_stats_before

        try:
            runtime.run_property_command(
                "context.space_data.overlay.show_stats",
                bpy.context,
                "NODE_EDITOR",
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Property action ran in an incompatible editor")

    editor_properties = {
        "IMAGE_EDITOR": "show_repeat",
        "NODE_EDITOR": "show_annotation",
        "SEQUENCE_EDITOR": "show_overlays",
        "CLIP_EDITOR": "show_names",
        "DOPESHEET_EDITOR": "show_seconds",
        "GRAPH_EDITOR": "show_handles",
        "NLA_EDITOR": "show_strip_curves",
        "TEXT_EDITOR": "show_word_wrap",
        "CONSOLE": "font_size",
        "INFO": "show_report_info",
        "OUTLINER": "use_sort_alpha",
        "PROPERTIES": "use_pin_id",
        "FILE_BROWSER": "show_region_toolbar",
        "SPREADSHEET": "use_filter",
    }
    try:
        for area_type, property_id in editor_properties.items():
            view3d_area.type = area_type
            space = view3d_area.spaces.active
            property_descriptor = space.bl_rna.properties[property_id]
            captured_editor_property = quick_add.capture_button_property(
                SimpleNamespace(
                    button_pointer=space,
                    button_prop=property_descriptor,
                    scene=bpy.context.scene,
                    space_data=space,
                    tool_settings=tool_settings,
                )
            )
            assert captured_editor_property, (area_type, property_id)
            assert captured_editor_property["space_type"] == area_type
            assert captured_editor_property["path"] == f"context.space_data.{property_id}"
    finally:
        view3d_area.type = "VIEW_3D"

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()

    keyconfig = bpy.context.window_manager.keyconfigs.addon
    foreign_keymap = keyconfig.keymaps.new(
        name="Window",
        space_type="EMPTY",
        region_type="WINDOW",
    )
    foreign_item = foreign_keymap.keymap_items.new(
        "wm.call_menu",
        type="F12",
        value="PRESS",
        shift=True,
    )
    foreign_item.properties.name = "VIEW3D_MT_view"
    foreign_before = shortcut_snapshot(foreign_keymap, foreign_item)

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.delete",
        source_label="Delete",
        source_command="object.delete()",
        source_space_type="VIEW_3D",
        menu_uid=quick_add.NEW_MENU_ID,
        new_menu_name="Quick Add Test",
        slot_position="0",
        slot_icon="MESH_CUBE",
        shortcut_key="F9",
        shortcut_ctrl=True,
        shortcut_shift=True,
    )
    assert result == {"FINISHED"}
    assert len(prefs.pie_menus) == 1
    menu = prefs.pie_menus[0]
    assert menu.name == "Quick Add Test"
    assert menu.key == "F9"
    assert menu.ctrl
    assert menu.shift
    assert not menu.alt
    assert not menu.oskey
    assert menu.slots[0].command == "object.delete()"
    assert menu.slots[0].label == "Delete"
    assert menu.slots[0].icon == "MESH_CUBE"
    assert menu.slots[0].enabled
    assert menu.keymap_context == "VIEW_3D"
    assert not menu.mode_filter_enabled
    assert not menu.allowed_modes
    assert shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before
    occupied_text, occupied_icon = quick_add._direction_button_content(prefs, menu, "0")
    empty_text, empty_icon = quick_add._direction_button_content(prefs, menu, "1")
    assert occupied_text == "Delete"
    assert occupied_icon == "MESH_CUBE"
    assert empty_text in {"Empty", "Пусто"}
    assert empty_icon == "NONE"
    menu.slots[0].enabled = False
    disabled_text, disabled_icon = quick_add._direction_button_content(prefs, menu, "0")
    assert disabled_text == "Delete"
    assert disabled_icon == "MESH_CUBE"
    assert quick_add._position_is_occupied(menu, "0")
    menu.slots[0].enabled = True

    menu.mode_filter_enabled = True
    menu.allowed_modes = {"OBJECT"}
    assert availability.menu_matches_context(menu, bpy.context)
    object_only_poll = runtime._make_menu_poll(menu.uid)
    assert object_only_poll(None, bpy.context)
    edit_context = SimpleNamespace(
        preferences=bpy.context.preferences,
        mode="EDIT_MESH",
    )
    assert not object_only_poll(None, edit_context)
    menu.mode_filter_enabled = False
    menu.allowed_modes = set()

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.select_all",
        source_label="Select All",
        source_command="object.select_all(action='SELECT')",
        menu_uid=menu.uid,
        slot_position="1",
        shortcut_edit_enabled=True,
        shortcut_key="F8",
        shortcut_event_value="PRESS",
        shortcut_alt=True,
    )
    assert result == {"FINISHED"}
    assert menu.key == "F8"
    assert menu.event_value == "PRESS"
    assert menu.alt
    assert not menu.ctrl
    assert not menu.shift
    assert not menu.oskey
    runtime.clear_slot(menu.slots[1])

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.select_all",
        source_label="Select All",
        source_command="object.select_all(action='SELECT')",
        menu_uid=menu.uid,
        slot_position="1",
    )
    assert result == {"FINISHED"}
    assert menu.slots[1].command == "object.select_all(action='SELECT')"
    # Adding another action must not replace an existing shortcut.
    assert menu.key == "F8"
    assert menu.alt
    runtime.clear_slot(menu.slots[1])

    no_key_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(no_key_menu)
    no_key_menu.uid = "quick-add-no-key"
    no_key_menu.name = "No Key"
    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.select_all",
        source_label="Select All",
        source_command="object.select_all(action='SELECT')",
        menu_uid=no_key_menu.uid,
        slot_position="0",
    )
    assert result == {"FINISHED"}
    # Background mode exercises the automatic capture path without an input event.
    assert not no_key_menu.key
    prefs.pie_menus.remove(len(prefs.pie_menus) - 1)
    prefs.active_menu_index = 0

    context_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(context_menu)
    quick_add._configure_menu_keymap(context_menu, "SEQUENCE_EDITOR")
    assert context_menu.keymap_context == "CUSTOM"
    assert context_menu.custom_keymap_name == "Sequencer"
    assert context_menu.custom_space_type == "SEQUENCE_EDITOR"
    prefs.pie_menus.remove(len(prefs.pie_menus) - 1)
    prefs.active_menu_index = 0

    use_snap_before = tool_settings.use_snap
    result = bpy.ops.pie_customizer.quick_add_operator(
        source_action_type="PROPERTY",
        source_label=captured_property["label"],
        source_property_path=captured_property["path"],
        source_property_type=captured_property["property_type"],
        source_property_value_json=captured_property["value_json"],
        source_space_type="VIEW_3D",
        menu_uid=menu.uid,
        slot_position="1",
        property_bool_mode="TOGGLE",
    )
    assert result == {"FINISHED"}
    assert menu.slots[1].slot_type == "PROPERTY"
    assert menu.slots[1].command == "context.scene.tool_settings.use_snap"
    assert menu.slots[1].context_space_type == "VIEW_3D"
    assert menu.key == "F8"
    assert menu.alt
    runtime.run_property_command(menu.slots[1].command, bpy.context)
    assert tool_settings.use_snap is not use_snap_before
    tool_settings.use_snap = use_snap_before
    runtime.clear_slot(menu.slots[1])

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_action_type="PROPERTY",
        source_label=captured_enum["label"],
        source_property_path=captured_enum["path"],
        source_property_type=captured_enum["property_type"],
        source_property_value_json=captured_enum["value_json"],
        source_property_items_json=captured_enum["enum_items_json"],
        menu_uid=menu.uid,
        slot_position="1",
        property_enum_value="CENTER",
    )
    assert result == {"FINISHED"}
    assert menu.slots[1].command == "context.scene.tool_settings.snap_target = 'CENTER'"
    runtime.clear_slot(menu.slots[1])

    snap_elements_before = set(tool_settings.snap_elements_base)
    result = bpy.ops.pie_customizer.quick_add_operator(
        source_action_type="PROPERTY",
        source_label=captured_snap_elements["label"],
        source_property_path=captured_snap_elements["path"],
        source_property_type=captured_snap_elements["property_type"],
        source_property_value_json=captured_snap_elements["value_json"],
        source_property_items_json=captured_snap_elements["enum_items_json"],
        source_property_is_enum_flag=True,
        source_space_type="VIEW_3D",
        menu_uid=menu.uid,
        slot_position="1",
        property_enum_value="VERTEX",
    )
    assert result == {"FINISHED"}
    assert menu.slots[1].slot_type == "PROPERTY"
    assert menu.slots[1].command == (
        "context.scene.tool_settings.snap_elements_base = {'VERTEX'}"
    )
    runtime.run_property_command(menu.slots[1].command, bpy.context)
    assert set(tool_settings.snap_elements_base) == {"VERTEX"}
    tool_settings.snap_elements_base = snap_elements_before
    runtime.clear_slot(menu.slots[1])

    orientation_before = orientation_slot.type
    result = bpy.ops.pie_customizer.quick_add_operator(
        source_action_type="PROPERTY",
        source_label=captured_orientation["label"],
        source_property_path=captured_orientation["path"],
        source_property_type=captured_orientation["property_type"],
        source_property_value_json=captured_orientation["value_json"],
        source_property_items_json=captured_orientation["enum_items_json"],
        source_space_type="VIEW_3D",
        menu_uid=menu.uid,
        slot_position="1",
        property_enum_value="LOCAL",
    )
    assert result == {"FINISHED"}
    assert menu.slots[1].slot_type == "OPERATOR"
    assert menu.slots[1].operator_context == "EXEC_DEFAULT"
    assert menu.slots[1].command == "transform.select_orientation(orientation='LOCAL')"
    with bpy.context.temp_override(window=window, area=view3d_area, region=view3d_region):
        runtime.run_operator_command(menu.slots[1].command, menu.slots[1].operator_context)
    assert orientation_slot.type == "LOCAL"
    orientation_slot.type = orientation_before
    runtime.clear_slot(menu.slots[1])

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.duplicate",
        source_label="Duplicate",
        source_command="object.duplicate()",
        menu_uid=menu.uid,
        slot_position="0",
    )
    assert result == {"CANCELLED"}
    assert menu.slots[0].command == "object.delete()"

    result = bpy.ops.pie_customizer.quick_add_operator(
        source_operator_id="object.duplicate",
        source_label="Duplicate",
        source_command="object.duplicate()",
        menu_uid=menu.uid,
        slot_position="0",
        replace_existing=True,
        slot_icon="DUPLICATE",
    )
    assert result == {"FINISHED"}
    assert menu.slots[0].command == "object.duplicate()"
    assert menu.slots[0].icon == "DUPLICATE"
    assert sum(slot.enabled for slot in menu.slots) == 1
    assert shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before

    for position in range(1, 8):
        before = [slot.command for slot in menu.slots]
        result = bpy.ops.pie_customizer.quick_add_operator(
            source_operator_id="object.delete",
            source_label=f"Direction {position}",
            source_command="object.delete(use_global=False)",
            menu_uid=menu.uid,
            slot_position=str(position),
        )
        assert result == {"FINISHED"}
        after = [slot.command for slot in menu.slots]
        changed = [index for index, values in enumerate(zip(before, after)) if values[0] != values[1]]
        assert changed == [position], (position, changed)
        assert shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before

    assert sum(slot.enabled for slot in menu.slots) == 8

    serialized = runtime.serialize_menus(prefs)
    assert serialized[0]["slots"][0]["command"] == "object.duplicate()"
    assert "context_space_type" in serialized[0]["slots"][0]
    assert len(serialized[0]["slots"]) == 8
    assert serialized[0]["mode_filter_enabled"] is False
    assert serialized[0]["allowed_modes"] == []

    addon_utils.disable("pie_customizer", default_set=True)
    assert not quick_add._context_menu_registered
    assert shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None
    from pie_customizer import quick_add as reloaded_quick_add
    assert reloaded_quick_add._context_menu_registered
    addon_utils.disable("pie_customizer", default_set=True)

    foreign_keymap.keymap_items.remove(foreign_item)
    keyconfig.keymaps.remove(foreign_keymap)
    print("PIE_CUSTOMIZER_QUICK_ADD_SMOKE_OK", bpy.app.version_string)


if __name__ == "__main__":
    main()
