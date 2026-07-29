"""Validate Blender 4.2 legacy brush activation in a real 3D View context."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import addon_utils
import bpy


def _run() -> None:
    failed = False
    source_path = None
    try:
        if "--" in sys.argv:
            source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
            sys.path.insert(0, source_path)

        module = addon_utils.enable(
            "pie_customizer",
            default_set=False,
            persistent=False,
        )
        assert module is not None

        from pie_customizer import runtime

        window = bpy.context.window_manager.windows[0]
        area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
        region = next(region for region in area.regions if region.type == "WINDOW")
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
            bpy.ops.object.mode_set(mode="SCULPT")
            result = runtime.run_operator_command(
                "wm.tool_set_by_id(name='builtin_brush.Clay Strips')",
                "EXEC_DEFAULT",
            )
            tool = bpy.context.workspace.tools.from_space_view3d_mode(
                "SCULPT",
                create=False,
            )
            assert result == {"FINISHED"}, result
            assert tool is not None
            assert tool.idname == "builtin_brush.Clay Strips", tool.idname
            print("PIE_CUSTOMIZER_LEGACY_BRUSH_UI_SMOKE_OK")
    except Exception:
        failed = True
        traceback.print_exc()
        print("PIE_CUSTOMIZER_LEGACY_BRUSH_UI_SMOKE_FAILED")
    finally:
        if source_path is not None and source_path in sys.path:
            sys.path.remove(source_path)
        bpy.app.driver_namespace["pie_customizer_smoke_failed"] = failed
        bpy.ops.wm.quit_blender()


if bpy.app.version < (4, 3, 0):
    bpy.app.timers.register(_run, first_interval=0.25)
else:
    print("PIE_CUSTOMIZER_LEGACY_BRUSH_UI_SMOKE_SKIPPED")
    bpy.app.timers.register(bpy.ops.wm.quit_blender, first_interval=0.1)
