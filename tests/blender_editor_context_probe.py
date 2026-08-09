"""Report stable direct Space properties for Blender editor types.

Run with Blender in factory-startup/background mode. This is a development
probe and is intentionally kept outside the extension package.
"""

from __future__ import annotations

import json
import sys

import bpy


SUPPORTED_TYPES = {"BOOLEAN", "INT", "FLOAT", "ENUM"}


def property_summary(space):
    values = []
    for descriptor in space.bl_rna.properties:
        identifier = descriptor.identifier
        if (
            identifier == "rna_type"
            or descriptor.type not in SUPPORTED_TYPES
            or bool(getattr(descriptor, "is_array", False))
            or bool(getattr(descriptor, "is_readonly", False))
            or (
                descriptor.type == "ENUM"
                and bool(getattr(descriptor, "is_enum_flag", False))
            )
        ):
            continue
        try:
            if space.is_property_readonly(identifier):
                continue
            getattr(space, identifier)
        except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
            continue
        values.append({"id": identifier, "type": descriptor.type})
    return values


def main():
    keymaps_only = "--keymaps-only" in sys.argv
    window = bpy.context.window_manager.windows[0]
    area = next(area for area in window.screen.areas if area.type == "VIEW_3D")
    original_type = area.type
    reports = []
    try:
        if keymaps_only:
            reports = []
        else:
            area_types = bpy.types.Area.bl_rna.properties["type"].enum_items
            for item in area_types:
                area_type = item.identifier
                if area_type in {"EMPTY", "TOPBAR", "STATUSBAR"}:
                    continue
                try:
                    area.type = area_type
                    region = next(
                        (region for region in area.regions if region.type == "WINDOW"),
                        None,
                    )
                    if region is None:
                        continue
                    with bpy.context.temp_override(window=window, area=area, region=region):
                        space = bpy.context.space_data
                        reports.append(
                            {
                                "area_type": area_type,
                                "space_rna": space.bl_rna.identifier,
                                "properties": property_summary(space),
                            }
                        )
                except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
                    reports.append({"area_type": area_type, "error": str(exc)})
    finally:
        area.type = original_type

    if not keymaps_only:
        print("PIE_CUSTOMIZER_EDITOR_CONTEXTS=" + json.dumps(reports, sort_keys=True))
    keymaps = []
    keyconfig = bpy.context.window_manager.keyconfigs.default
    if keyconfig is not None:
        for keymap in keyconfig.keymaps:
            if keymap.space_type == "EMPTY":
                continue
            keymaps.append(
                {
                    "name": keymap.name,
                    "space_type": keymap.space_type,
                    "region_type": keymap.region_type,
                }
            )
    print("PIE_CUSTOMIZER_EDITOR_KEYMAPS=" + json.dumps(keymaps, sort_keys=True))


if __name__ == "__main__":
    main()
