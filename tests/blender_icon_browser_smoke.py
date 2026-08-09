"""Exercise the built-in icon browser and icon preset round trips in Blender."""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy


def main():
    source_root = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    sys.path.insert(0, str(source_root))

    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None

    from pie_customizer import operators, runtime

    prefs = bpy.context.preferences.addons["pie_customizer"].preferences
    prefs.pie_menus.clear()
    menu = prefs.pie_menus.add()
    runtime.initialize_empty_menu(menu)
    menu.uid = uuid.uuid4().hex
    menu.name = "Icon Browser"
    slot = menu.slots[0]
    runtime.assign_slot_action(
        slot,
        label="Cube",
        icon="OBJECT_DATA",
        slot_type="OPERATOR",
        command="mesh.primitive_cube_add()",
    )

    icon_names = runtime.builtin_icon_names()
    assert icon_names[0] == "NONE"
    assert "MESH_CUBE" in icon_names
    assert "OBJECT_DATA" in icon_names
    assert "BLANK1" not in icon_names
    assert not any("BLENDER" in name for name in icon_names)
    assert "COLORSET_01_VEC" in icon_names
    assert "COLOR_BLUE" in icon_names
    assert not {
        "COLORSET_17_VEC",
        "COLORSET_18_VEC",
        "COLORSET_19_VEC",
        "COLORSET_20_VEC",
    }.intersection(icon_names)
    assert len(icon_names) > 900, len(icon_names)
    assert runtime.safe_icon("mesh_cube") == "MESH_CUBE"
    assert runtime.safe_icon("NOT_A_REAL_ICON") == "NONE"

    mesh_matches = operators._matching_icon_names("mesh cube")
    assert "MESH_CUBE" in mesh_matches
    assert all("MESH" in name and "CUBE" in name for name in mesh_matches)

    page_probe = SimpleNamespace(icon_search="", icon_page="0")
    operators._step_icon_page(page_probe, 1)
    assert page_probe.icon_page == "1"
    operators._step_icon_page(page_probe, -1)
    assert page_probe.icon_page == "0"
    operators._step_icon_page(page_probe, -1)
    assert page_probe.icon_page == "0"

    before = runtime.serialize_menus(prefs)
    result = bpy.ops.pie_customizer.choose_slot_icon(
        "EXEC_DEFAULT",
        menu_uid=menu.uid,
        slot_position="0",
        icon="MESH_CUBE",
    )
    assert result == {"FINISHED"}, result
    assert slot.icon == "MESH_CUBE"
    after = runtime.serialize_menus(prefs)
    assert before[0]["slots"][0]["icon"] == "OBJECT_DATA"
    assert after[0]["slots"][0]["icon"] == "MESH_CUBE"
    assert before[0]["slots"][1:] == after[0]["slots"][1:]

    with tempfile.TemporaryDirectory(prefix="pie-customizer-icons-") as temp_dir:
        export_path = Path(temp_dir) / "icons.json"
        export_result = bpy.ops.pie_customizer.export_preset(
            "EXEC_DEFAULT",
            filepath=str(export_path),
        )
        assert export_result == {"FINISHED"}, export_result
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        assert payload["pie_menus"][0]["slots"][0]["icon"] == "MESH_CUBE"

        prefs.pie_menus.clear()
        import_result = bpy.ops.pie_customizer.import_preset(
            "EXEC_DEFAULT",
            filepath=str(export_path),
            merge_mode="REPLACE",
        )
        assert import_result == {"FINISHED"}, import_result
        assert prefs.pie_menus[0].slots[0].icon == "MESH_CUBE"

    no_icon_result = bpy.ops.pie_customizer.choose_slot_icon(
        "EXEC_DEFAULT",
        menu_uid=prefs.pie_menus[0].uid,
        slot_position="0",
        icon="NONE",
    )
    assert no_icon_result == {"FINISHED"}, no_icon_result
    assert prefs.pie_menus[0].slots[0].icon == "NONE"

    addon_utils.disable("pie_customizer", default_set=True)
    module = addon_utils.enable("pie_customizer", default_set=True, persistent=False)
    assert module is not None
    addon_utils.disable("pie_customizer", default_set=True)
    print("PIE_CUSTOMIZER_ICON_BROWSER_OK", bpy.app.version_string, len(icon_names))


if __name__ == "__main__":
    main()
