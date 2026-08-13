"""Open Pie Customizer preferences with a nested-menu tree for visual QA."""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


SOURCE_ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
SCREENSHOT_PATH = Path(sys.argv[sys.argv.index("--") + 2]).resolve()
sys.path.insert(0, str(SOURCE_ROOT))


class PIE_CUSTOMIZER_PT_menu_hierarchy_preview(bpy.types.Panel):
    bl_idname = "PIE_CUSTOMIZER_PT_menu_hierarchy_preview"
    bl_label = "Pie Menus"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_ui_units_x = 60

    def draw(self, context):
        from pie_customizer import preferences, runtime

        prefs = runtime.get_preferences(context)
        preferences._draw_menus_content(self.layout, prefs)


def show_preferences():
    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()

    main_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(main_menu)
    main_menu.name = "Меню"
    main_menu.key = "NUMPAD_1"
    main_menu.alt = True

    directions = prefs.pie_menus.add()
    runtime.initialize_empty_menu(directions)
    directions.name = "Направления"

    centers = prefs.pie_menus.add()
    runtime.initialize_empty_menu(centers)
    centers.name = "Центры"

    second_parent = prefs.pie_menus.add()
    runtime.initialize_empty_menu(second_parent)
    second_parent.name = "Второе меню"

    runtime.assign_slot_action(
        main_menu.slots[0],
        label=directions.name,
        icon="MENU_PANEL",
        slot_type="MENU",
        command=runtime.menu_id_for(directions),
    )
    runtime.assign_slot_action(
        main_menu.slots[1],
        label=centers.name,
        icon="MENU_PANEL",
        slot_type="MENU",
        command=runtime.menu_id_for(centers),
    )
    runtime.assign_slot_action(
        second_parent.slots[0],
        label=centers.name,
        icon="MENU_PANEL",
        slot_type="MENU",
        command=runtime.menu_id_for(centers),
    )
    prefs.active_menu_index = 0

    bpy.utils.register_class(PIE_CUSTOMIZER_PT_menu_hierarchy_preview)
    result = bpy.ops.wm.call_panel(
        "INVOKE_DEFAULT",
        name=PIE_CUSTOMIZER_PT_menu_hierarchy_preview.bl_idname,
        keep_open=True,
    )
    print("PIE_CUSTOMIZER_MENU_HIERARCHY_PANEL", result)
    return None


def capture_preferences():
    bpy.ops.screen.screenshot(filepath=str(SCREENSHOT_PATH))
    print("PIE_CUSTOMIZER_MENU_HIERARCHY_SCREENSHOT", SCREENSHOT_PATH)
    return None


def finish():
    bpy.ops.wm.quit_blender()
    return None


bpy.app.timers.register(show_preferences, first_interval=1.5)
bpy.app.timers.register(capture_preferences, first_interval=3.5)
bpy.app.timers.register(finish, first_interval=4.5)
