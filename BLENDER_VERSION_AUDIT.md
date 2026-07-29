# Pie Customizer: Blender Version Audit

Audit date: 2026-07-26

## Scope

The catalog, imported presets, operator parameters, property paths, enum values,
dynamic discovery, and legacy menu compatibility were checked separately for:

- Blender 4.2.21 LTS
- Blender 4.5.11 LTS
- Blender 5.2.0 LTS

Each version was reviewed by an independent agent against its bundled Blender UI
scripts and versioned official API documentation. The repository test suite,
full RNA audit, release workflow, and safe curated actions were then run in the
actual installed Blender binaries.

## Version Matrix

| Version | Curated catalog | Discovered operators | Poll errors | Parameter errors | Safe executions |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4.2.21 LTS | 121/121 | 2328 | 0 | 0 | 77, 0 errors |
| 4.5.11 LTS | 122/122 | 2315 | 0 | 0 | 78, 0 errors |
| 5.2.0 LTS | 122/122 | 2421 | 0 | 0 | 78, 0 errors |

No curated operator available only in Blender 5.x is shown by the 4.2 catalog.
The catalog builds version-dependent `object.convert` variants from the active
Blender RNA:

- Blender 4.2 uses `GPENCIL` and does not expose Point Cloud conversion.
- Newer versions can use `GREASEPENCIL` and expose only the targets reported by
  their own RNA.

References:

- Blender 4.2 Object operators:
  https://docs.blender.org/api/4.2/bpy.ops.object.html#bpy.ops.object.convert
- Blender 4.5 Python API:
  https://docs.blender.org/api/4.5/
- Blender Mesh mirror properties:
  https://docs.blender.org/api/5.0/bpy.types.Mesh.html#bpy.types.Mesh.use_mirror_x

## Issues Found And Fixed

### Cross-version presets

Imported operator commands were previously accepted as strings. A 5.x preset
could therefore carry `object.convert(target='GREASEPENCIL')` or
`object.convert(target='POINTCLOUD')` into Blender 4.2.

The importer and runtime now:

- validate operator ids and arguments against the active Blender RNA;
- validate scalar argument types and enum flags;
- migrate `GPENCIL` and `GREASEPENCIL` when the current version uses the other
  identifier;
- reject unsupported enum values before changing the user's existing menus;
- include the active Blender version in the error.

### Enum defaults

The Parameters editor previously selected the first enum item instead of the
operator's RNA default. For example, Blender 4.2 defaults
`object.convert.target` to `MESH`, while its first enum item is `CURVE`.

The editor now preserves `prop.default` and uses the first enum item only as a
fallback when Blender exposes no usable default.

### Sculpt Mirror X

Blender's Sculpt Mirror X control uses:

```text
context.object.data.use_mirror_x
```

The catalog now uses this Mesh property. The previous saved command
`context.scene.tool_settings.sculpt.use_symmetry_x` remains supported through a
runtime compatibility mapping.

### Dynamic operator cache

Dynamic discovery is now keyed by the enabled add-on set. Enabling or disabling
an add-on refreshes its available operators without requiring a Blender restart.

### Technical Parameters button

Curated `wm.context_set_enum` actions no longer show a Parameters button. Their
`data_path` and `value` fields are implementation details rather than useful
user-facing settings.

### Version-aware brush catalog

Blender 4.2 predates the Essentials brush asset layout used by newer versions.
Pie Customizer therefore reads the legacy brush enums from that version's own
RNA and generates native `wm.tool_set_by_id` commands. It finds 79 available
brush tools in Blender 4.2.21, including Sculpt Paint, Cloth, Curve Sculpt,
Texture Paint, Vertex Paint, Weight Paint, and Grease Pencil tools.

Starting with Blender 4.3, the built-in Essentials brush asset libraries are
indexed by their real asset names without loading brush datablocks into the
scene. The tested catalogs contain 129 assets in Blender 4.5.11 and 133 assets
in Blender 5.2.0. Both systems use the same human-facing groups:

- Sculpt: General, Paint, Simulation, Curve Sculpt, and Grease Pencil Sculpt.
- Paint: Texture, Vertex, Weight, Grease Pencil Draw, Grease Pencil Vertex,
  and Grease Pencil Weight.

The generated `brush.asset_activate` commands were executed in Blender 4.5 and
5.2 for General, Paint, and Simulation sculpt brushes. The generated Blender
4.2 command was executed in a real 3D View and verified to activate
`builtin_brush.Clay Strips`.

## Automated Evidence

- Python unit tests: 77 PASS.
- Full operator RNA audit: PASS in Blender 4.2, 4.5, and 5.2.
- Release workflow smoke: PASS in Blender 4.2, 4.5, and 5.2.
- Safe curated execution smoke: PASS in Blender 4.2, 4.5, and 5.2.
- Sculpt catalog smoke: PASS.
- Brush discovery smoke: PASS in Blender 4.2, 4.5, and 5.2.
- Blender 4.2 legacy brush activation in a real 3D View: PASS.
- Essentials brush asset activation: PASS in Blender 4.5 and 5.2.
- Extension installation smoke: PASS in Blender 4.2, 4.5, and 5.2.
- Boolean property actions checked against their active RNA paths: 131/131.
- Dynamic operators inspected across the three versions: 7064.
- Dynamic operator poll exceptions: 0.
- Parameter editor serialization errors: 0.

Some modal or editor-context actions cannot be fully executed in Blender
without a matching area and user event. Their API schema is checked
automatically, while final interactive behavior remains in the release
checklist:

- transform orientation selection;
- Loop Cut and Slide;
- modal move, rotate, scale, and mirror;
- editor-specific and add-on operators.

The current installed Blender 4.2.21, 4.5.11, and 5.2.0 builds all complete the
background catalog smoke. Blender 4.2 additionally completes the foreground UI
test required by its context-dependent workspace tool operator.
