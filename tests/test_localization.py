import ast
import re
import unittest
from pathlib import Path

from pie_customizer.localization import BLENDER_TRANSLATIONS, STRINGS, resolve_language, tr


ROOT = Path(__file__).resolve().parents[1]
CYRILLIC = re.compile(r"[А-Яа-яЁё]")


class LocalizationTest(unittest.TestCase):
    def test_languages_have_matching_nonempty_keys(self):
        self.assertEqual(set(STRINGS["RU"]), set(STRINGS["EN"]))
        for language, strings in STRINGS.items():
            with self.subTest(language=language):
                self.assertTrue(all(value.strip() for value in strings.values()))

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(tr("UNKNOWN", "apply"), STRINGS["EN"]["apply"])

    def test_automatic_language_uses_russian_only_for_russian_blender(self):
        self.assertEqual(resolve_language("ru_RU"), "RU")
        self.assertEqual(resolve_language("en_US"), "EN")
        self.assertEqual(resolve_language("de_DE"), "EN")

    def test_disabled_blender_translation_uses_english(self):
        self.assertEqual(resolve_language("ru_RU", False), "EN")

    def test_native_russian_translations_cover_reported_metadata(self):
        translations = BLENDER_TRANSLATIONS["ru_RU"]
        self.assertEqual(translations[("*", "Catalog")], "Каталог")
        self.assertEqual(
            translations[("*", "Position of the slot inside the pie menu")],
            "Позиция слота внутри pie menu",
        )

    def test_static_rna_metadata_uses_english_source_strings(self):
        for filename in ("model.py", "operators.py", "preferences.py"):
            tree = ast.parse((ROOT / "pie_customizer" / filename).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    target_names = {
                        target.id
                        for target in node.targets
                        if isinstance(target, ast.Name)
                    }
                    if target_names & {"bl_label", "bl_description"}:
                        self.assertNotRegex(node.value.value, CYRILLIC)
                if isinstance(node, ast.Call):
                    for keyword in node.keywords:
                        if keyword.arg in {"name", "description"} and isinstance(
                            keyword.value,
                            ast.Constant,
                        ) and isinstance(keyword.value.value, str):
                            self.assertNotRegex(keyword.value.value, CYRILLIC)


if __name__ == "__main__":
    unittest.main()
