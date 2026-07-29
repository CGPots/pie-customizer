"""Drive a short, deterministic Pie Customizer screen-recording demo."""

from __future__ import annotations

import sys
import os
from pathlib import Path

import addon_utils
import bpy


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEMO_WINDOW = None
DEMO_LOG = Path("/private/tmp/pie_customizer_demo_actions.log")


def _log(message: str) -> None:
    with DEMO_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{message}\n")


def _largest_area(area_type: str | None = None):
    areas = DEMO_WINDOW.screen.areas
    candidates = [area for area in areas if area_type is None or area.type == area_type]
    return max(candidates, key=lambda area: area.width * area.height)


def _window_region(area):
    return next(region for region in area.regions if region.type == "WINDOW")


def _redraw() -> None:
    for area in DEMO_WINDOW.screen.areas:
        area.tag_redraw()


def _slot(menu, position: int, label: str, icon: str, slot_type: str, command: str):
    slot = menu.slots[position]
    slot.enabled = True
    slot.label = label
    slot.icon = icon
    slot.slot_type = slot_type
    slot.command = command
    slot.operator_context = "EXEC_DEFAULT"


def _new_menu(prefs, runtime, name: str):
    menu = prefs.pie_menus.add()
    menu.name = name
    runtime.initialize_empty_menu(menu)
    return menu


def _prepare_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_cube_add(location=(-1.45, 0.0, 0.0), scale=(0.85, 0.85, 0.85))
    cube = bpy.context.object
    cube.name = "Product"
    bevel = cube.modifiers.new("Soft Edges", "BEVEL")
    bevel.width = 0.12
    bevel.segments = 4

    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(1.25, 0.0, 0.05), radius=0.9)
    sphere = bpy.context.object
    sphere.name = "Choice"
    sphere.scale.z = 1.15

    bpy.ops.mesh.primitive_plane_add(size=14, location=(0.0, 0.0, -1.05))
    floor = bpy.context.object
    floor.name = "Workspace"

    for obj in (cube, sphere):
        obj.select_set(True)
    floor.select_set(False)
    bpy.context.view_layer.objects.active = cube


def _prepare_addon():
    addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    from pie_customizer import runtime

    prefs = runtime.get_preferences()
    prefs.pie_menus.clear()
    prefs.favorite_actions.clear()
    prefs.active_menu_index = 0
    prefs.catalog_mode = "POPULAR"
    prefs.catalog_browse_mode = "SEARCH"
    prefs.command_search = ""

    nested = _new_menu(prefs, runtime, "View Controls")
    _slot(nested, 0, "Frame Selected", "VIEWZOOM", "OPERATOR", "view3d.view_selected()")
    _slot(nested, 1, "Camera View", "VIEW_CAMERA", "OPERATOR", "view3d.view_camera()")
    _slot(
        nested,
        2,
        "Toggle Overlays",
        "OVERLAY",
        "PROPERTY",
        "context.space_data.overlay.show_overlays",
    )
    _slot(nested, 3, "Wireframe", "SHADING_WIRE", "OPERATOR", "object.mode_set(mode='OBJECT')")

    main = _new_menu(prefs, runtime, "Quick Tools")
    _slot(main, 0, "Local", "ORIENTATION_LOCAL", "OPERATOR", "transform.select_orientation(orientation='LOCAL')")
    _slot(main, 1, "View Controls", "MENU_PANEL", "MENU", runtime.menu_id_for(nested))
    _slot(main, 2, "Delete", "TRASH", "OPERATOR", "object.delete()")
    _slot(main, 3, "Add Cube", "MESH_CUBE", "OPERATOR", "mesh.primitive_cube_add()")
    _slot(main, 4, "Global", "ORIENTATION_GLOBAL", "OPERATOR", "transform.select_orientation(orientation='GLOBAL')")
    _slot(main, 5, "Frame Selected", "VIEWZOOM", "OPERATOR", "view3d.view_selected()")
    _slot(main, 6, "Overlays", "OVERLAY", "PROPERTY", "context.space_data.overlay.show_overlays")
    _slot(main, 7, "Select All", "RESTRICT_SELECT_OFF", "OPERATOR", "object.select_all(action='SELECT')")
    main.key = "F6"

    prefs.active_menu_index = 1
    runtime.rebuild_dynamic_menus()
    return prefs, runtime, main, nested


def _full_view() -> None:
    area = _largest_area("VIEW_3D")
    region = _window_region(area)
    with bpy.context.temp_override(window=DEMO_WINDOW, area=area, region=region):
        try:
            bpy.ops.screen.screen_full_area(use_hide_panels=True)
        except Exception:
            pass
    area = _largest_area("VIEW_3D")
    space = area.spaces.active
    space.region_3d.view_distance = 7.2
    region = _window_region(area)
    with bpy.context.temp_override(window=bpy.context.window, area=area, region=region):
        bpy.ops.view3d.view_selected(use_all_regions=False)
    DEMO_WINDOW.cursor_warp(area.x + area.width // 2, area.y + area.height // 2)


def _show_pie(runtime, menu) -> None:
    area = _largest_area("VIEW_3D")
    region = _window_region(area)
    DEMO_WINDOW.cursor_warp(area.x + area.width // 2, area.y + area.height // 2)
    with bpy.context.temp_override(window=DEMO_WINDOW, area=area, region=region):
        bpy.ops.wm.call_menu_pie(name=runtime.menu_id_for(menu))


def _show_preferences() -> None:
    area = _largest_area()
    area.type = "PREFERENCES"
    bpy.context.preferences.active_section = "ADDONS"
    region = _window_region(area)
    with bpy.context.temp_override(window=DEMO_WINDOW, area=area, region=region):
        bpy.ops.preferences.addon_show(module="pie_customizer")
    _log(f"preferences: {[item.type for item in DEMO_WINDOW.screen.areas]}")
    _redraw()


def _restore_view() -> None:
    area = _largest_area()
    area.type = "VIEW_3D"
    space = area.spaces.active
    space.region_3d.view_distance = 7.2
    DEMO_WINDOW.cursor_warp(area.x + area.width // 2, area.y + area.height // 2)
    _log(f"viewport: {[item.type for item in DEMO_WINDOW.screen.areas]}")
    _redraw()


def _schedule(delay: float, callback) -> None:
    def run_once():
        try:
            _log(f"run: {getattr(callback, '__name__', repr(callback))}")
            callback()
        except Exception:
            import traceback

            traceback.print_exc()
        return None

    bpy.app.timers.register(run_once, first_interval=delay)


def main() -> None:
    global DEMO_WINDOW
    DEMO_WINDOW = max(
        bpy.context.window_manager.windows,
        key=lambda window: sum(area.width * area.height for area in window.screen.areas),
    )
    DEMO_LOG.write_text("demo initialized\n", encoding="utf-8")
    _log(
        "windows: "
        + repr(
            [
                [(area.type, area.width, area.height) for area in window.screen.areas]
                for window in bpy.context.window_manager.windows
            ]
        )
    )
    view = bpy.context.preferences.view
    view.language = "en_US"
    view.use_translate_interface = True
    view.use_translate_tooltips = True

    _prepare_scene()
    bpy.ops.wm.save_as_mainfile(
        filepath="/private/tmp/Pie_Customizer_Demo.blend",
        check_existing=False,
    )
    prefs, runtime, main_menu, _nested_menu = _prepare_addon()
    _full_view()

    state = {"new_menu": None}

    def add_empty_menu():
        bpy.ops.pie_customizer.add_menu()
        menu = prefs.pie_menus[prefs.active_menu_index]
        menu.name = "Orientation"
        state["new_menu"] = menu
        _redraw()

    def search_local():
        menu = state["new_menu"]
        menu.active_slot_position = "0"
        prefs.catalog_mode = "ALL"
        prefs.catalog_browse_mode = "SEARCH"
        prefs.command_search = "local"
        _redraw()

    def assign_local():
        menu = state["new_menu"]
        slot = menu.slots[0]
        slot.enabled = True
        slot.label = "Orientation: Local"
        slot.icon = "ORIENTATION_LOCAL"
        slot.slot_type = "OPERATOR"
        slot.command = "transform.select_orientation(orientation='LOCAL')"
        slot.operator_context = "EXEC_DEFAULT"
        _redraw()

    def assign_shortcut():
        menu = state["new_menu"]
        menu.key = "ONE"
        menu.alt = True
        runtime.rebuild_dynamic_menus()
        _redraw()

    def apply_changes():
        bpy.ops.pie_customizer.rebuild()
        _redraw()

    def show_new_menu():
        _show_pie(runtime, state["new_menu"])

    def hover_nested():
        area = _largest_area("VIEW_3D")
        bpy.context.window.cursor_warp(
            area.x + area.width // 2 + 245,
            area.y + area.height // 2,
        )

    def wait_for_recording_trigger():
        trigger = Path("/private/tmp/pie_customizer_demo_go")
        if not trigger.exists():
            return 0.25

        trigger.unlink(missing_ok=True)
        start = 0.5
        _schedule(start + 1.0, lambda: _show_pie(runtime, main_menu))
        _schedule(start + 3.3, _show_preferences)
        _schedule(start + 5.0, add_empty_menu)
        _schedule(start + 7.0, search_local)
        _schedule(start + 9.2, assign_local)
        _schedule(start + 10.8, assign_shortcut)
        _schedule(start + 12.2, apply_changes)
        _schedule(start + 13.6, _restore_view)
        _schedule(start + 14.7, show_new_menu)
        _schedule(start + 16.8, lambda: _show_pie(runtime, main_menu))
        _schedule(start + 18.1, hover_nested)
        _schedule(start + 24.5, lambda: bpy.ops.wm.quit_blender())
        return None

    bpy.app.timers.register(wait_for_recording_trigger, first_interval=0.25)

    Path("/private/tmp/pie_customizer_demo_ready.txt").write_text(
        str(os.getpid()),
        encoding="utf-8",
    )
    print("PIE_CUSTOMIZER_DEMO_READY", flush=True)


if __name__ == "__main__":
    main()
