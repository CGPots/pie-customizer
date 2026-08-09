"""Exercise shortcut trigger events, presets, and keymap cleanup in Blender."""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

import addon_utils
import bpy


EVENT_CASES = (
    ("PRESS", "F6", False),
    ("RELEASE", "F7", False),
    ("CLICK", "BUTTON4MOUSE", False),
    ("DOUBLE_CLICK", "BUTTON5MOUSE", False),
    ("CLICK_DRAG", "LEFTMOUSE", True),
)


def _shortcut_snapshot(keymap, keymap_item):
    return (
        keymap.name,
        keymap_item.idname,
        keymap_item.type,
        keymap_item.value,
        keymap_item.ctrl,
        keymap_item.shift,
        keymap_item.alt,
        keymap_item.oskey,
        keymap_item.properties.name,
    )


def _add_event_menus(prefs, runtime):
    prefs.pie_menus.clear()
    for event_value, key, ctrl in EVENT_CASES:
        menu = prefs.pie_menus.add()
        runtime.initialize_empty_menu(menu)
        menu.uid = uuid.uuid4().hex
        menu.name = event_value
        menu.keymap_context = "WINDOW"
        menu.key = key
        menu.event_value = event_value
        menu.ctrl = ctrl


def main():
    source_root = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    sys.path.insert(0, str(source_root))

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    foreign_keymap = keyconfig.keymaps.get("Window")
    if foreign_keymap is None:
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
    foreign_before = _shortcut_snapshot(foreign_keymap, foreign_item)

    _add_event_menus(prefs, runtime)
    errors = runtime.rebuild_dynamic_menus(bpy.context)
    assert not errors, errors
    assert len(runtime._dynamic_keymaps) == len(EVENT_CASES)

    registered = {
        (item.value, item.type, bool(item.ctrl))
        for _keymap, item in runtime._dynamic_keymaps
    }
    assert registered == set(EVENT_CASES), registered
    assert _shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before

    first_menu = prefs.pie_menus[0]
    configure_result = bpy.ops.pie_customizer.configure_shortcut(
        "EXEC_DEFAULT",
        menu_uid=first_menu.uid,
        event_value="PRESS",
    )
    assert configure_result == {"FINISHED"}, configure_result
    assert hasattr(bpy.ops.pie_customizer, "capture_shortcut")

    with tempfile.TemporaryDirectory(prefix="pie-customizer-events-") as temp_dir:
        export_path = Path(temp_dir) / "shortcut-events.json"
        export_result = bpy.ops.pie_customizer.export_preset(
            "EXEC_DEFAULT",
            filepath=str(export_path),
        )
        assert export_result == {"FINISHED"}, export_result

        payload = json.loads(export_path.read_text(encoding="utf-8"))
        exported_values = [item["event_value"] for item in payload["pie_menus"]]
        assert exported_values == [case[0] for case in EVENT_CASES], exported_values

        prefs.pie_menus.clear()
        import_result = bpy.ops.pie_customizer.import_preset(
            "EXEC_DEFAULT",
            filepath=str(export_path),
            merge_mode="REPLACE",
        )
        assert import_result == {"FINISHED"}, import_result
        imported_values = [menu.event_value for menu in prefs.pie_menus]
        assert imported_values == exported_values, imported_values
        assert not runtime.rebuild_dynamic_menus(bpy.context)

        legacy_path = Path(temp_dir) / "legacy-shortcut.json"
        legacy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "addon": "pie_customizer",
                    "pie_menus": [
                        {
                            "uid": "legacy-shortcut",
                            "name": "Legacy Shortcut",
                            "key": "F9",
                            "slots": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        legacy_result = bpy.ops.pie_customizer.import_preset(
            "EXEC_DEFAULT",
            filepath=str(legacy_path),
            merge_mode="REPLACE",
        )
        assert legacy_result == {"FINISHED"}, legacy_result
        assert len(prefs.pie_menus) == 1
        assert prefs.pie_menus[0].event_value == "PRESS"

    assert _shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before
    addon_utils.disable("pie_customizer", default_set=True)
    assert not runtime._dynamic_keymaps
    assert not runtime._dynamic_menu_classes
    assert _shortcut_snapshot(foreign_keymap, foreign_item) == foreign_before

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None
    addon_utils.disable("pie_customizer", default_set=True)
    assert not runtime._dynamic_keymaps
    assert not runtime._dynamic_menu_classes

    foreign_keymap.keymap_items.remove(foreign_item)
    print("PIE_CUSTOMIZER_SHORTCUT_EVENTS_OK", bpy.app.version_string)


if __name__ == "__main__":
    main()
