"""Pie Customizer - custom pie menu builder for Blender."""

ADDON_VERSION = (1, 1, 1)

bl_info = {
    "name": "Pie Customizer",
    "description": "Build custom pie menus with any buttons you choose.",
    "author": "cgPots",
    "version": ADDON_VERSION,
    "blender": (4, 2, 0),
    "category": "Interface",
}

_needs_reload = "bpy" in locals()

try:
    import bpy
except ModuleNotFoundError:
    bpy = None

if bpy is not None:
    from . import (
        availability,
        command_catalog,
        discovery,
        localization,
        model,
        operator_parameters,
        operators,
        preset,
        preferences,
        quick_add,
        quick_add_data,
        runtime,
        shortcuts,
        ui_style,
    )

    if _needs_reload:
        import importlib

        for module in (
            availability,
            command_catalog,
            discovery,
            localization,
            shortcuts,
            model,
            operator_parameters,
            operators,
            preset,
            preferences,
            quick_add_data,
            quick_add,
            runtime,
            ui_style,
        ):
            importlib.reload(module)

    CLASSES = (
        *model.CLASSES,
        *preferences.CLASSES,
        *operators.CLASSES,
        *quick_add.CLASSES,
    )
else:
    CLASSES = ()


def register():
    if bpy is None:
        raise RuntimeError("Pie Customizer can only be registered inside Blender")

    registered_classes = []
    try:
        bpy.app.translations.register(__name__, localization.BLENDER_TRANSLATIONS)

        for cls in CLASSES:
            bpy.utils.register_class(cls)
            registered_classes.append(cls)

        quick_add.register_context_menu()
        runtime.ensure_initial_preferences()
        runtime.rebuild_dynamic_menus()
    except Exception:
        quick_add.unregister_context_menu()
        for cls in reversed(registered_classes):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
        try:
            bpy.app.translations.unregister(__name__)
        except (RuntimeError, ValueError):
            pass
        raise


def unregister():
    if bpy is None:
        return

    quick_add.unregister_context_menu()
    runtime.unregister_dynamic_menus()

    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    try:
        bpy.app.translations.unregister(__name__)
    except (RuntimeError, ValueError):
        pass
