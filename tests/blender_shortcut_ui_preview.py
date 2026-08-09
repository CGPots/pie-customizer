"""Open and capture the compact shortcut settings dialog for visual QA."""

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
    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()
    menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(menu)
    menu.uid = uuid.uuid4().hex
    menu.name = "Context Tools"
    menu.key = "F8"
    menu.ctrl = True
    menu.event_value = "DOUBLE_CLICK"
    prefs.active_menu_index = 0

    result = bpy.ops.pie_customizer.configure_shortcut(
        "INVOKE_DEFAULT",
        menu_uid=menu.uid,
    )
    print("PIE_CUSTOMIZER_SHORTCUT_DIALOG", result)
    return None


def capture_dialog():
    bpy.ops.screen.screenshot(filepath=str(SCREENSHOT_PATH))
    print("PIE_CUSTOMIZER_SHORTCUT_SCREENSHOT", SCREENSHOT_PATH)
    return None


def finish():
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(open_dialog, first_interval=0.5)
bpy.app.timers.register(capture_dialog, first_interval=1.5)
bpy.app.timers.register(finish, first_interval=2.5)
