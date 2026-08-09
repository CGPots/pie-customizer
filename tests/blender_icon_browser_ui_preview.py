"""Open and capture the icon browser dialog for visual QA."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

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

    from pie_customizer import runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()
    menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(menu)
    menu.uid = uuid.uuid4().hex
    menu.name = "Modeling"
    runtime.assign_slot_action(
        menu.slots[0],
        label="Add Cube",
        icon="MESH_CUBE",
        slot_type="OPERATOR",
        command="mesh.primitive_cube_add()",
    )
    prefs.active_menu_index = 0

    result = bpy.ops.pie_customizer.choose_slot_icon(
        "INVOKE_DEFAULT",
        menu_uid=menu.uid,
        slot_position="0",
    )
    print("PIE_CUSTOMIZER_ICON_DIALOG", result)
    return None


def capture_dialog():
    bpy.ops.screen.screenshot(filepath=str(SCREENSHOT_PATH))
    print("PIE_CUSTOMIZER_ICON_SCREENSHOT", SCREENSHOT_PATH)
    return None


def finish():
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(open_dialog, first_interval=1.5)
bpy.app.timers.register(capture_dialog, first_interval=3.0)
bpy.app.timers.register(finish, first_interval=4.0)
