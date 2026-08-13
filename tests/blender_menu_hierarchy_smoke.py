"""Verify nested menu hierarchy presentation inside Blender."""

from __future__ import annotations

import sys
from pathlib import Path

import addon_utils
import bpy


def main() -> None:
    source_root = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    sys.path.insert(0, str(source_root))

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import preferences, runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()

    main_menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(main_menu)
    main_menu.name = "Menu"

    directions = prefs.pie_menus.add()
    runtime.initialize_empty_menu(directions)
    directions.name = "Directions"

    centers = prefs.pie_menus.add()
    runtime.initialize_empty_menu(centers)
    centers.name = "Centers"

    second_parent = prefs.pie_menus.add()
    runtime.initialize_empty_menu(second_parent)
    second_parent.name = "Second Parent"

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

    rows = preferences._menu_hierarchy_rows(prefs)
    assert [row.index for row in rows] == [0, 1, 2, 3, 2]
    assert [row.prefix for row in rows] == ["", "", "", "", ""]

    preferences._sync_menu_hierarchy_entries(prefs)
    entries = list(prefs.menu_hierarchy_entries)
    assert len(entries) == 5
    centers_entries = [entry for entry in entries if entry.menu_uid == centers.uid]
    assert len(centers_entries) == 2
    assert centers_entries[0].occurrence_key != centers_entries[1].occurrence_key

    prefs.active_hierarchy_index = 4
    assert prefs.active_menu_index == 2
    centers.name = "Shared Centers"
    assert prefs.pie_menus[2].name == "Shared Centers"

    print("PIE_CUSTOMIZER_MENU_HIERARCHY_OK", bpy.app.version_string)


if __name__ == "__main__":
    main()
