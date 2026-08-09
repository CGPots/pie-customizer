"""Exercise per-menu mode availability inside a real Blender process."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import addon_utils
import bpy


def main():
    source_root = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    sys.path.insert(0, str(source_root))

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import availability, runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()

    unsafe_keys = (
        "LEFTMOUSE",
        "RIGHTMOUSE",
        "MIDDLEMOUSE",
        "WHEELUPMOUSE",
        "SPACE",
        "TAB",
        "RET",
        "NUMPAD_ENTER",
        "BACK_SPACE",
        "DEL",
    )
    for unsafe_key in unsafe_keys:
        unsafe_menu = prefs.pie_menus.add()
        runtime.initialize_empty_menu(unsafe_menu)
        unsafe_menu.uid = uuid.uuid4().hex
        unsafe_menu.name = f"Unsafe {unsafe_key}"
        unsafe_menu.key = unsafe_key
        unsafe_errors = runtime.rebuild_dynamic_menus(bpy.context)
        assert unsafe_errors, f"Plain {unsafe_key} must be rejected"
        assert not any(
            item.type == unsafe_key for _keymap, item in runtime._dynamic_keymaps
        )
        prefs.pie_menus.clear()

    object_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(object_menu)
    object_menu.uid = uuid.uuid4().hex
    object_menu.name = "Object Tools"
    object_menu.key = "F10"
    prefs.active_menu_index = 0

    result = bpy.ops.pie_customizer.configure_menu_availability(
        menu_uid=object_menu.uid,
        mode_filter_enabled=True,
        allowed_modes={"OBJECT"},
    )
    assert result == {"FINISHED"}, result
    assert object_menu.mode_filter_enabled
    assert set(object_menu.allowed_modes) == {"OBJECT"}
    assert availability.menu_matches_context(object_menu, bpy.context)

    object_menu_id = runtime.menu_id_for(object_menu)
    object_menu_class = getattr(bpy.types, object_menu_id)
    assert object_menu_class.poll(bpy.context)

    object_menu.allowed_modes = {"SCULPT"}
    runtime.rebuild_dynamic_menus(bpy.context)
    object_menu_class = getattr(bpy.types, object_menu_id)
    assert not object_menu_class.poll(bpy.context)
    blocked_result = bpy.ops.wm.call_menu_pie("INVOKE_DEFAULT", name=object_menu_id)
    assert "CANCELLED" in blocked_result, blocked_result
    assert "PASS_THROUGH" in blocked_result, blocked_result

    object_menu.allowed_modes = {"OBJECT"}
    edit_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(edit_menu)
    edit_menu.uid = uuid.uuid4().hex
    edit_menu.name = "Edit Tools"
    edit_menu.key = "F10"
    result = bpy.ops.pie_customizer.configure_menu_availability(
        menu_uid=edit_menu.uid,
        mode_filter_enabled=True,
        allowed_modes={"EDIT_ANY", "EDIT_MESH"},
    )
    assert result == {"FINISHED"}, result
    assert set(edit_menu.allowed_modes) == {"EDIT_ANY"}

    object_menu_class = getattr(bpy.types, object_menu_id)
    edit_menu_class = getattr(bpy.types, runtime.menu_id_for(edit_menu))
    assert not edit_menu_class.poll(bpy.context)
    assert object_menu_class.poll(bpy.context)
    registered_f10 = [
        item
        for _keymap, item in runtime._dynamic_keymaps
        if item.type == "F10"
    ]
    assert len(registered_f10) == 2, len(registered_f10)

    edit_menu_id = runtime.menu_id_for(edit_menu)
    blocked_nested_result = bpy.ops.wm.call_menu_pie(
        "INVOKE_DEFAULT", name=edit_menu_id
    )
    assert "CANCELLED" in blocked_nested_result, blocked_nested_result
    assert "PASS_THROUGH" in blocked_nested_result, blocked_nested_result

    bpy.ops.object.mode_set(mode="EDIT")
    assert bpy.context.mode == "EDIT_MESH", bpy.context.mode
    assert not object_menu_class.poll(bpy.context)
    assert edit_menu_class.poll(bpy.context)
    blocked_object_result = bpy.ops.wm.call_menu_pie(
        "INVOKE_DEFAULT", name=object_menu_id
    )
    assert "CANCELLED" in blocked_object_result, blocked_object_result
    assert "PASS_THROUGH" in blocked_object_result, blocked_object_result
    bpy.ops.object.mode_set(mode="OBJECT")

    serialized = runtime.serialize_menus(prefs)
    assert serialized[0]["mode_filter_enabled"] is True
    assert serialized[0]["allowed_modes"] == ["OBJECT"]
    assert serialized[1]["allowed_modes"] == ["EDIT_ANY"]

    runtime.load_menus(
        prefs,
        [{"uid": "legacy-menu", "name": "Legacy", "slots": []}],
        replace=True,
    )
    legacy = prefs.pie_menus[0]
    assert not legacy.mode_filter_enabled
    assert not legacy.allowed_modes
    assert availability.menu_matches_context(legacy, bpy.context)

    runtime.load_menus(
        prefs,
        [
            {
                "uid": "empty-filter",
                "name": "Recovered Empty Filter",
                "mode_filter_enabled": True,
                "allowed_modes": [],
                "slots": [],
            }
        ],
        replace=True,
    )
    recovered = prefs.pie_menus[0]
    assert not recovered.mode_filter_enabled
    assert availability.menu_matches_context(recovered, bpy.context)

    addon_utils.disable("pie_customizer", default_set=True)
    assert not runtime._dynamic_keymaps
    assert not runtime._dynamic_menu_classes
    print("PIE_CUSTOMIZER_MODE_AVAILABILITY_OK", bpy.app.version_string)


if __name__ == "__main__":
    main()
