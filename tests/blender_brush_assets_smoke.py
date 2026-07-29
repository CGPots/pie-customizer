"""Validate version-appropriate brush discovery and activation."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import addon_utils
import bpy


def _action(actions, label: str, group: str):
    matches = [
        action
        for action in actions
        if action.label == label and action.group == group
    ]
    assert len(matches) == 1, (label, group, len(matches))
    return matches[0]


def _activate_sculpt_brush(command: str, expected_name: str) -> None:
    from pie_customizer import runtime

    result = runtime.run_operator_command(command, "EXEC_DEFAULT")
    assert result == {"FINISHED"}, (expected_name, result)
    brush = bpy.context.tool_settings.sculpt.brush
    assert brush is not None
    assert brush.name.strip() == expected_name


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer import preferences
    from pie_customizer.discovery import (
        broad_category_for_action,
        discover_brush_asset_actions,
        filter_actions,
    )

    actions = discover_brush_asset_actions()
    print(
        "PIE_CUSTOMIZER_BRUSH_COUNTS="
        f"{len(actions)}:{dict(sorted(Counter(action.group for action in actions).items()))}"
    )
    if bpy.app.version < (4, 2, 0):
        assert actions == ()
        print("PIE_CUSTOMIZER_BRUSH_CATALOG_UNAVAILABLE")
    elif bpy.app.version < (4, 3, 0):
        assert len(actions) >= 70, len(actions)
        assert {broad_category_for_action(action) for action in actions} == {
            "PAINT",
            "SCULPT",
        }
        clay_strips = _action(
            actions,
            "Clay Strips",
            "sculpt_brushes_general",
        )
        _action(actions, "Paint", "sculpt_brushes_paint")
        _action(actions, "Cloth", "sculpt_brushes_simulation")
        _action(actions, "Comb", "sculpt_brushes_curves")
        _action(actions, "Draw", "paint_brushes_texture")
        assert clay_strips.command == (
            "wm.tool_set_by_id(name='builtin_brush.Clay Strips')"
        )
        assert filter_actions(actions, "clay strips", rank_matches=True)[0] == clay_strips
        assert filter_actions(actions, "кисть симуляция")
        assert not preferences._slot_has_operator_parameters(
            SimpleNamespace(command=clay_strips.command)
        )
    else:
        assert len(actions) >= 100, len(actions)
        assert {broad_category_for_action(action) for action in actions} == {
            "PAINT",
            "SCULPT",
        }

        clay_strips = _action(
            actions,
            "Clay Strips",
            "sculpt_brushes_general",
        )
        paint_hard = _action(
            actions,
            "Paint Hard",
            "sculpt_brushes_paint",
        )
        grab_cloth = _action(
            actions,
            "Grab Cloth",
            "sculpt_brushes_simulation",
        )
        _action(actions, "Comb", "sculpt_brushes_curves")
        _action(actions, "Paint Hard", "paint_brushes_texture")

        assert filter_actions(actions, "clay strips", rank_matches=True)[0] == clay_strips
        assert filter_actions(actions, "кисть симуляция")
        assert not preferences._slot_has_operator_parameters(
            SimpleNamespace(command=clay_strips.command)
        )

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
        bpy.ops.object.mode_set(mode="SCULPT")
        for action in (clay_strips, paint_hard, grab_cloth):
            _activate_sculpt_brush(action.command, action.label)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.delete()

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_BRUSH_ASSETS_SMOKE_OK")


if __name__ == "__main__":
    main()
