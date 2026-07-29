"""Smoke-test the built extension under Blender's extension module namespace."""

from __future__ import annotations

import importlib
import sys
import tempfile
import zipfile
from pathlib import Path

import addon_utils
import bpy


MODULE_NAME = "bl_ext.user_default.pie_customizer"


def main() -> None:
    separator = sys.argv.index("--")
    archive = Path(sys.argv[separator + 1]).resolve()
    assert archive.is_file()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        package_dir = root / "bl_ext" / "user_default" / "pie_customizer"
        package_dir.mkdir(parents=True)
        (root / "bl_ext" / "__init__.py").write_text("", encoding="utf-8")
        (root / "bl_ext" / "user_default" / "__init__.py").write_text("", encoding="utf-8")
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(package_dir)

        saved_extension_modules = {
            name: module
            for name, module in tuple(sys.modules.items())
            if name == "bl_ext" or name.startswith("bl_ext.")
        }
        for name in saved_extension_modules:
            sys.modules.pop(name, None)

        sys.path.insert(0, str(root))
        try:
            importlib.invalidate_caches()
            module = addon_utils.enable(MODULE_NAME, default_set=True, persistent=False)
            assert module is not None
            assert module.ADDON_VERSION == (1, 0, 1)

            prefs = bpy.context.preferences.addons[MODULE_NAME].preferences
            assert len(prefs.pie_menus) == 0
            assert bpy.ops.pie_customizer.add_menu() == {"FINISHED"}
            menu = prefs.pie_menus[0]
            menu.name = "Extension Smoke"
            menu.key = "F8"
            assert bpy.ops.pie_customizer.rebuild() == {"FINISHED"}

            runtime = importlib.import_module(f"{MODULE_NAME}.runtime")
            assert hasattr(bpy.types, runtime.menu_id_for(menu))

            view = bpy.context.preferences.view
            original_language = view.language
            original_translate_interface = view.use_translate_interface
            original_translate_tooltips = view.use_translate_tooltips
            try:
                view.use_translate_interface = True
                view.use_translate_tooltips = True

                view.language = "en_US"
                assert bpy.app.translations.pgettext_iface("Catalog") == "Catalog"
                assert (
                    bpy.app.translations.pgettext_tip(
                        "Position of the slot inside the pie menu"
                    )
                    == "Position of the slot inside the pie menu"
                )

                view.language = "ru_RU"
                assert bpy.app.translations.pgettext_iface("Catalog") == "Каталог"
                assert (
                    bpy.app.translations.pgettext_tip(
                        "Position of the slot inside the pie menu"
                    )
                    == "Позиция слота внутри pie menu"
                )
            finally:
                view.language = original_language
                view.use_translate_interface = original_translate_interface
                view.use_translate_tooltips = original_translate_tooltips
        finally:
            addon_utils.disable(MODULE_NAME, default_set=True)
            sys.path.remove(str(root))
            for name in tuple(sys.modules):
                if name == "bl_ext" or name.startswith("bl_ext."):
                    sys.modules.pop(name, None)
            sys.modules.update(saved_extension_modules)

    print("PIE_CUSTOMIZER_EXTENSION_SMOKE_OK")


if __name__ == "__main__":
    main()
