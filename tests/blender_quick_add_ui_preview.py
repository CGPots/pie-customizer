"""Open and capture the Quick Add direction grid for visual QA."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy


SOURCE_ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
SCREENSHOT_PATH = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
sys.path.insert(0, str(SOURCE_ROOT))


def open_dialog():
    for addon_id in ("pie_customizer", "bl_ext.user_default.pie_customizer"):
        addon_utils.disable(addon_id, default_set=False)
    for module_name in tuple(sys.modules):
        if (
            module_name == "pie_customizer"
            or module_name.startswith("pie_customizer.")
            or module_name.endswith(".pie_customizer")
            or ".pie_customizer." in module_name
        ):
            sys.modules.pop(module_name, None)

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import quick_add, runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()
    menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(menu)
    menu.uid = uuid.uuid4().hex
    menu.name = "Modeling"
    runtime.assign_slot_action(
        menu.slots[0],
        label="Empty: Plain Axes",
        icon="EMPTY_AXIS",
        slot_type="OPERATOR",
        command="object.empty_add(type='PLAIN_AXES')",
    )
    prefs.active_menu_index = 0

    orientation_slot = bpy.context.scene.transform_orientation_slots[0]
    property_data = quick_add.capture_button_property(
        SimpleNamespace(
            button_operator=None,
            button_pointer=orientation_slot,
            button_prop=orientation_slot.bl_rna.properties["type"],
            scene=bpy.context.scene,
            tool_settings=bpy.context.scene.tool_settings,
        )
    )
    assert property_data is not None

    result = bpy.ops.pie_customizer.quick_add_operator(
        "INVOKE_DEFAULT",
        source_action_type="PROPERTY",
        source_label=property_data["label"],
        source_property_path=property_data["path"],
        source_property_type=property_data["property_type"],
        source_property_value_json=property_data["value_json"],
        source_property_items_json=property_data["enum_items_json"],
        source_property_is_enum_flag=property_data["is_enum_flag"],
        source_space_type=property_data["space_type"],
        menu_uid=menu.uid,
        slot_position="3",
    )
    print("PIE_CUSTOMIZER_QUICK_ADD_DIALOG", result)
    return None


def capture_dialog():
    bpy.ops.screen.screenshot(filepath=str(SCREENSHOT_PATH))
    print("PIE_CUSTOMIZER_QUICK_ADD_SCREENSHOT", SCREENSHOT_PATH)
    return None


def finish():
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(open_dialog, first_interval=1.5)
bpy.app.timers.register(capture_dialog, first_interval=3.0)
bpy.app.timers.register(finish, first_interval=4.0)
