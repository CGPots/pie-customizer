# Pie Customizer 1.0.1

## Tagline

Build custom pie menus with any buttons you choose

## Description

Pie Customizer lets you create multiple pie menus, fill their eight directions
with Blender commands, and assign a shortcut to each menu without writing code.

Choose actions from a searchable catalog of registered Blender operators,
configure common operator parameters, save favorites, and connect one custom
menu to another when eight directions are not enough. Advanced users can also
enter operators, properties, or Blender menus manually.

The interface follows Blender's language automatically and includes English
and Russian translations. Presets can be imported and exported as JSON.

## Platform Testing

Pie Customizer is designed to work on Windows, macOS, and Linux through
Blender's cross-platform Python API. This release has currently been tested on
macOS. If you use Windows or Linux, testing feedback and reports of any
platform-specific issues are very welcome.

## Highlights

- Create and manage multiple custom pie menus.
- Capture single-key and modifier shortcuts directly from the keyboard.
- Search Blender operators by name, description, category, or operator ID.
- Browse dedicated Sculpting, Painting, Nodes, and Animation sections.
- Find the built-in brushes provided by the active Blender version. Blender 4.2
  uses its native brush tools; Blender 4.3 and newer use Essentials brush
  assets. Results are organized into dedicated Sculpt, Sculpt Paint, Sculpt
  Simulation, Texture Paint, Vertex Paint, Weight Paint, Curve Sculpt, and
  Grease Pencil groups.
- Find 125 ready-to-use 3D View toggles for overlays, gizmos, regions, shading, object visibility, transforms, and snapping.
- Browse curated popular actions, recent operators, and favorites.
- Configure supported operator parameters from the interface.
- Open nested custom menus as compact lists while keeping the original pie open.
- Import and export menu presets.
- Automatic English and Russian interface localization.

## Compatibility

Blender 4.2 LTS and newer. Tested with Blender 4.2.21 LTS, 4.5.11 LTS,
5.1, and 5.2.0 LTS on macOS.

## Release Notes

### 1.0.1

- Updated module loading to follow Blender's documented reload pattern.
- Added a public issue tracker for support and bug reports.
- Removed dynamic Python execution and development-only diagnostics.
- Limited shortcut handling to registering and unregistering the add-on's own keymap items.
- Rebuilt the package with Blender's official extension command-line tool.

### 1.0.0

- Initial public release.
- Custom menu editor with eight native pie directions.
- Searchable catalog of Blender and enabled add-on operators.
- Shortcut capture, favorites, recent commands, and nested menus.
- Operator parameter editor and manual command entry.
- JSON preset import and export.
- English and Russian localization.

## Support

Report bugs and request features in the public
[GitHub issue tracker](https://github.com/CGPots/pie-customizer/issues).

## Suggested Tags

User Interface, Development
