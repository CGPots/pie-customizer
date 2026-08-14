# Pie Customizer

Build custom pie menus with any Blender buttons you need.

Author: `cgPots`. License: `GPL-3.0-or-later`.

## Pie Customizer 1.1.3

Added a clear hierarchy view for pie menus with clean indentation. Shared
submenus are displayed under each parent menu and stay synchronized when
edited.

## Features

- Create and manage multiple custom pie menus.
- Assign a Blender shortcut to each menu through `wm.call_menu_pie`.
- Quickly add supported operators and properties from the
  `Add to Pie Customizer` entry in Blender's button context menu.
- Choose `Press`, `Release`, `Click`, `Double Click`, or `Drag` as the shortcut
  trigger and reassign the key combination from a compact dialog.
- Configure all eight standard pie directions.
- View nested custom menus as a clean, indented hierarchy. A shared submenu can
  appear under multiple parents while remaining one synchronized menu.
- Browse and search Blender's built-in icons with paged navigation and automatic
  icon suggestions in Quick Add.
- Use the automatic English interface or Russian translation based on Blender's
  interface language.
- Add operator, property, menu, or separator slots.
- Import and export menu presets as JSON.
- Discover registered operators from Blender and enabled add-ons automatically.
- Use 125 ready-made 3D View controls for overlays, gizmos, panels, shading,
  object visibility, transforms, and snapping.
- Search by name, description, or technical operator ID, with sections and
  paged results.
- Browse dedicated Popular, Recent, Favorites, Sculpting, Painting, and Nodes
  sections.
- Configure common operator parameters such as numbers, strings, toggles, and
  enum values.
- Use ready-made actions for transform orientation, pivot point, proportional
  editing falloff, object and selection modes, axis views, shading, Origin,
  Convert, Merge, Delete, and Empty types.
- Use the combined `Mirror X from Cursor + Clean Seam` action to create an
  `mrr` Plain Axes Empty at the 3D Cursor, use it as the Mirror Object, clean
  the center seam, and add an X Mirror modifier with Merge and Clipping.
- Search the brushes available in the current Blender version. Blender 4.2 uses
  its available built-in brush tools, while Blender 4.3 and newer use the
  bundled Essentials assets.
- Keep Shader Editor, Geometry Nodes, and Compositor actions in a dedicated
  Nodes section instead of mixing them with general view commands.

## Installation

Pie Customizer supports Blender 4.2 and newer. Version 1.1.3 was tested in
Blender 4.2 LTS, 4.5 LTS, and 5.2 LTS.

See [`BLENDER_VERSION_AUDIT.md`](BLENDER_VERSION_AUDIT.md) for the detailed
compatibility and test notes.

Install the published Blender Extension archive:

`pie_customizer-1.1.3.zip`

In Blender, open `Edit > Preferences > Add-ons`, choose `Install from Disk...`,
and select the ZIP without unpacking it.

The add-on follows Blender's interface language. Russian Blender uses the
Russian translation; all other languages use English.

After changing menus, click `Apply` in the add-on preferences to rebuild the
menu classes and shortcuts.

## Getting Started

1. In the `Pie Menus` section, click `New Menu`.
2. Each row is a separate pie menu. Click `New Menu` again to create another.
3. Click the shortcut shown to the right of the menu name, choose a trigger,
   and reassign the key combination if needed.
4. In `Buttons in Selected Menu`, select a direction and choose an action from
   the catalog.
5. Click `Apply`.

To add a supported Blender button faster, right-click it and choose
`Add to Pie Customizer`. Select the menu, value, icon, and direction, then
confirm. An occupied direction is replaced only after explicit confirmation.

The menu list is empty on first launch. Every new menu starts with eight empty
directions, so you can build your own layout without removing demo actions.

Use `Custom Command` to enter an operator, property, or menu manually. JSON
preset import and export are available in the `Advanced` section.

## Action Catalog

The catalog includes these modes:

- `Popular` — a short curated set of useful actions with ready-made settings.
- `Search` — operators from `bpy.ops`, enabled add-ons, and built-in Blender UI
  controls.
- `Recent` — operators recently used in the current Blender window.
- `Favorites` — actions marked with the heart button.
- `Nested Menu` — assign another custom pie menu to the selected direction.
- `Custom Command` — enter an operator, property, or menu manually.

When an operator has editable arguments, a `Parameters` button appears. Regular
parameters are enabled with a checkbox. Boolean arguments use one clear choice:
`Default`, `Enabled`, or `Disabled`. `Default` omits the argument and preserves
Blender's standard behavior. Ready-made property toggles run immediately and do
not need a parameters dialog.

Inside `Search`, switch to `Sections` to browse human-readable categories
without knowing the exact command name. Sculpt operators stay in `Sculpting`,
Paint and Grease Pencil actions stay in `Painting`, and node editor operations
stay in `Nodes`. Results show ten actions per page. The complete technical
`bpy.ops` module filter is available behind the filter icon.

Search covers operator names, Popular actions, English and Russian labels,
available enum values, and built-in brushes for the current Blender version.
It remains global: a Sculpting action can be found without opening the
Sculpting section first. Exact and visible-name matches appear first, followed
by results ranked by the current mode, favorites, and recent actions. Fuzzy
matching is used only when regular matches do not fill a page.

Some operators require a specific editor, mode, or selection. The catalog lists
registered actions, while Blender validates whether each action can run in the
current context.

Catalog assignment takes two clicks: select a pie direction, then select an
action. Blender's Preferences UI does not provide reliable drag-and-drop between
arbitrary controls, so click-based assignment is more predictable.

Blender's native pie layout has eight directions. To add more actions, create a
second menu and assign it through `Nested Menu`. Its populated buttons open in
a compact list near the selected direction while the original pie remains
visible. Nested levels can continue further.

Test shortcuts in the `3D View`. While the Preferences window is focused, the
3D View keymap may not receive the event. Press modifiers and the main key
together, for example `Alt+1`; Pie Customizer stores the complete combination.

## Implementation Notes

Pie Customizer uses Blender's native API. Dynamic `bpy.types.Menu` classes draw
their content through `layout.menu_pie()`, and shortcuts open them through
`wm.call_menu_pie`.

`Better Pie Menus v0.5.3` uses a similar foundation for its menu builder: menu
data is stored in add-on preferences, menu classes are generated dynamically,
and shortcuts are registered in `keyconfigs.addon`. Pie Customizer keeps this
architecture compact so the action editor can grow without unnecessary
complexity.

## Support

Report bugs or suggest improvements through
[GitHub Issues](https://github.com/CGPots/pie-customizer/issues). Include your
Blender version, operating system, reproduction steps, and a screenshot or
complete error message when available.
