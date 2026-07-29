# Pie Customizer 1.0.1

## Listing Fields

**Name**

Pie Customizer

**Tagline**

Build custom pie menus with any buttons you choose

**Type**

Add-on

**Compatibility**

Blender 4.2 LTS and newer

**Suggested tags**

User Interface, Development

**License**

GNU General Public License v3.0 or later

**Permissions**

Files: Import and export JSON presets.

**Network access**

Not required. Pie Customizer has no telemetry, updater, or online service.

## Description

Pie Customizer lets you create multiple pie menus, fill their eight directions
with Blender actions, and assign a shortcut to each menu without writing code.

Choose actions from a searchable catalog of registered Blender operators,
built-in brushes, and ready-to-use interface toggles. Search by name,
description, category, or operator ID; save favorites; configure supported
parameters; and connect one custom menu to another when eight directions are
not enough.

The catalog includes dedicated Sculpting, Painting, Nodes, and Animation
sections. Brush results adapt to the installed Blender version: Blender 4.2
uses its native brush tools, while Blender 4.3 and newer use Essentials brush
assets.

Advanced users can also enter operators, properties, or Blender menus
manually. Presets can be imported and exported as JSON.

The interface follows Blender's language automatically and includes English
and Russian translations.

## Platform Testing

Pie Customizer is designed to work on Windows, macOS, and Linux through
Blender's cross-platform Python API. This release has currently been tested on
macOS. If you use Windows or Linux, testing feedback and reports of any
platform-specific issues are very welcome.

## Highlights

- Create and manage multiple custom pie menus.
- Capture single-key and modifier shortcuts directly from the keyboard.
- Search Blender and enabled add-on operators.
- Browse version-aware Sculpt and Paint brushes.
- Use ready-made 3D View toggles for overlays, gizmos, shading, visibility,
  snapping, and other common settings.
- Configure supported operator parameters.
- Keep the original pie open while opening a nested menu as a compact list.
- Import and export JSON presets.
- Use automatic English and Russian localization.

## What's New

### 1.0.1

- Updated module loading to follow Blender's documented reload pattern.
- Added a public issue tracker for support and bug reports.
- Removed dynamic Python execution and development-only diagnostics.
- Limited shortcut handling to registering and unregistering the add-on's own
  keymap items.
- Rebuilt the release package with Blender's official extension command-line
  tool.

### 1.0.0

- Initial public release.
- Custom editor for multiple eight-direction pie menus.
- Searchable catalog of Blender actions and enabled add-on operators.
- Version-aware brush discovery for Blender 4.2 and newer.
- Shortcut capture, favorites, recent commands, and nested menus.
- Operator parameter editor and manual command entry.
- JSON preset import and export.
- English and Russian localization.

## Support Reply Template

Please include:

1. Your Blender version and operating system.
2. The action or shortcut that failed.
3. Exact steps needed to reproduce the issue.
4. A screenshot or the complete Blender error message, if available.

Public issue tracker:
https://github.com/CGPots/pie-customizer/issues
