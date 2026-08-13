import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pie_customizer.action_parser import parse_operator_command
from pie_customizer.command_catalog import SEARCH_ACTIONS, catalog_action_group
from pie_customizer.discovery import (
    BrowserAction,
    _modifier_actions_from_enum_items,
    broad_category_for_action,
    brush_asset_catalog_supported,
    brush_asset_group,
    canonical_operator_group,
    discover_operator_actions,
    filter_actions,
    filter_broad_category,
    format_operator_command,
    group_icon,
    group_label,
    legacy_brush_catalog_supported,
    legacy_brush_group,
    legacy_brush_tool_id,
    operator_identifier_to_id,
    operator_group_items,
    operator_is_catalog_safe,
)


class DiscoveryTest(unittest.TestCase):
    def test_operator_discovery_uses_enabled_addons_as_cache_key(self):
        with (
            patch(
                "pie_customizer.discovery._enabled_addon_signature",
                side_effect=[("first",), ("second",)],
            ),
            patch(
                "pie_customizer.discovery._discover_operator_actions",
                side_effect=[("first-result",), ("second-result",)],
            ) as discover,
        ):
            self.assertEqual(discover_operator_actions(), ("first-result",))
            self.assertEqual(discover_operator_actions(), ("second-result",))

        self.assertEqual(
            discover.call_args_list[0].args,
            (("first",),),
        )
        self.assertEqual(
            discover.call_args_list[1].args,
            (("second",),),
        )

    def test_internal_wrapper_without_defaults_is_not_searchable(self):
        self.assertFalse(operator_is_catalog_safe("object.set_proportional_falloff"))
        self.assertFalse(operator_is_catalog_safe("object.origin_set_any_mode"))
        self.assertFalse(operator_is_catalog_safe("pie_customizer.rebuild"))
        self.assertTrue(operator_is_catalog_safe("object.delete"))

    def test_operator_identifier_conversion(self):
        self.assertEqual(operator_identifier_to_id("MESH_OT_bevel"), "mesh.bevel")
        self.assertEqual(operator_identifier_to_id("object.delete"), "object.delete")

    def test_command_formatting(self):
        self.assertEqual(
            format_operator_command("mesh.merge", {"type": "CENTER", "uvs": True}),
            "mesh.merge(type='CENTER', uvs=True)",
        )

    def test_command_formatting_supports_python_keyword_name(self):
        command = format_operator_command("bmax.import")
        self.assertEqual(command, "bmax.import()")
        self.assertEqual(parse_operator_command(command).operator_id, "bmax.import")

    def test_modifier_enum_items_become_assignable_actions(self):
        enum_items = (
            SimpleNamespace(identifier="", name="Generate", description=""),
            SimpleNamespace(identifier="ARRAY", name="Array", description="Repeat geometry"),
            SimpleNamespace(
                identifier="GREASE_PENCIL_MIRROR",
                name="Mirror",
                description="Mirror Grease Pencil strokes",
            ),
            SimpleNamespace(identifier="CLOTH", name="Cloth", description="Cloth simulation"),
        )

        actions = _modifier_actions_from_enum_items(enum_items)

        self.assertEqual(len(actions), 3)
        self.assertEqual(actions[0].label, "Array")
        self.assertEqual(actions[0].group, "object_modifiers")
        self.assertEqual(
            actions[0].command,
            "object.modifier_add(type='ARRAY')",
        )
        self.assertEqual(actions[0].operator_context, "EXEC_DEFAULT")
        self.assertEqual(actions[1].label, "Grease Pencil: Mirror")
        self.assertEqual(actions[1].group, "grease_pencil_modifiers")
        self.assertEqual(actions[2].group, "physics_modifiers")
        self.assertEqual(len({action.token for action in actions}), len(actions))

    def test_modifier_actions_are_searchable_in_russian(self):
        actions = _modifier_actions_from_enum_items(
            (SimpleNamespace(identifier="BEVEL", name="Bevel", description="Chamfer edges"),)
        )

        self.assertEqual(filter_actions(actions, "модификатор"), actions)
        self.assertEqual(filter_actions(actions, "bevel"), actions)
        self.assertEqual(broad_category_for_action(actions[0]), "OBJECT")

    def test_brush_catalog_uses_version_appropriate_source(self):
        self.assertTrue(legacy_brush_catalog_supported((4, 2, 21)))
        self.assertFalse(legacy_brush_catalog_supported((4, 3, 0)))
        self.assertFalse(brush_asset_catalog_supported((4, 2, 21)))
        self.assertTrue(brush_asset_catalog_supported((4, 3, 0)))
        self.assertTrue(brush_asset_catalog_supported((4, 5, 3)))
        self.assertTrue(brush_asset_catalog_supported((5, 0, 0)))
        self.assertTrue(brush_asset_catalog_supported((5, 2, 0)))

    def test_legacy_brushes_use_matching_catalog_groups(self):
        cases = {
            ("sculpt_tool", "CLAY_STRIPS"): "sculpt_brushes_general",
            ("sculpt_tool", "PAINT"): "sculpt_brushes_paint",
            ("sculpt_tool", "SMEAR"): "sculpt_brushes_paint",
            ("sculpt_tool", "CLOTH"): "sculpt_brushes_simulation",
            ("curves_sculpt_tool", "COMB"): "sculpt_brushes_curves",
            ("image_tool", "DRAW"): "paint_brushes_texture",
            ("gpencil_tool", "DRAW"): "paint_brushes_grease_pencil",
        }
        for (enum_property, identifier), expected in cases.items():
            with self.subTest(enum_property=enum_property, identifier=identifier):
                self.assertEqual(
                    legacy_brush_group(enum_property, identifier),
                    expected,
                )
        self.assertEqual(
            legacy_brush_tool_id("Clay Strips"),
            "builtin_brush.Clay Strips",
        )

    def test_mesh_sculpt_brushes_use_shelf_groups(self):
        library = "essentials_brushes-mesh_sculpt.blend"
        cases = {
            "Clay Strips": "sculpt_brushes_general",
            "Paint Hard": "sculpt_brushes_paint",
            "Grab Planar Cloth ": "sculpt_brushes_simulation",
            "Future Cloth Brush": "sculpt_brushes_simulation",
        }
        for brush_name, expected in cases.items():
            with self.subTest(brush_name=brush_name):
                self.assertEqual(brush_asset_group(library, brush_name), expected)

    def test_brush_asset_libraries_use_correct_domains(self):
        cases = {
            "essentials_brushes-curve_sculpt.blend": (
                "sculpt_brushes_curves",
                "SCULPT",
            ),
            "essentials_brushes-gp_sculpt.blend": (
                "sculpt_brushes_grease_pencil",
                "SCULPT",
            ),
            "essentials_brushes-mesh_texture.blend": (
                "paint_brushes_texture",
                "PAINT",
            ),
            "essentials_brushes-mesh_vertex.blend": (
                "paint_brushes_vertex",
                "PAINT",
            ),
            "essentials_brushes-mesh_weight.blend": (
                "paint_brushes_weight",
                "PAINT",
            ),
            "essentials_brushes-gp_draw.blend": (
                "paint_brushes_grease_pencil",
                "PAINT",
            ),
        }
        for library, (group, expected_category) in cases.items():
            action = BrowserAction(
                library,
                "BRUSH_ASSET",
                f"brush_asset:{library}:Example",
                brush_asset_group(library, "Example"),
                "Example",
                "",
                "brush.asset_activate()",
                "BRUSH_DATA",
                "OPERATOR",
            )
            with self.subTest(library=library):
                self.assertEqual(action.group, group)
                self.assertEqual(
                    broad_category_for_action(action),
                    expected_category,
                )

    def test_enum_flag_formatting_is_stable(self):
        self.assertEqual(
            format_operator_command("wm.example", {"flags": {"BETA", "ALPHA"}}),
            "wm.example(flags={'ALPHA', 'BETA'})",
        )

    def test_filter_uses_label_id_description_and_group(self):
        actions = (
            BrowserAction("1", "OPERATOR", "mesh.bevel", "mesh", "Bevel", "Chamfer edges", "mesh.bevel()", "NONE", "OPERATOR"),
            BrowserAction("2", "OPERATOR", "object.delete", "object", "Delete", "Remove objects", "object.delete()", "NONE", "OPERATOR"),
        )
        self.assertEqual(filter_actions(actions, "chamfer"), (actions[0],))
        self.assertEqual(filter_actions(actions, "delete", "object"), (actions[1],))

    def test_filter_uses_enum_search_terms(self):
        action = BrowserAction(
            "1",
            "OPERATOR",
            "object.example",
            "object",
            "Example",
            "",
            "object.example()",
            "NONE",
            "OPERATOR",
            search_terms="LOCAL Local orientation",
        )
        self.assertEqual(filter_actions((action,), "local"), (action,))

    def test_blenderkit_operator_aliases_share_one_source(self):
        actions = (
            BrowserAction("1", "OPERATOR", "bk.search", "bk", "Search", "", "bk.search()", "NONE", "OPERATOR"),
            BrowserAction(
                "2",
                "OPERATOR",
                "blenderkit.download",
                "blenderkit",
                "Download",
                "",
                "blenderkit.download()",
                "NONE",
                "OPERATOR",
            ),
        )

        self.assertEqual(canonical_operator_group("bk"), "blenderkit")
        self.assertEqual(filter_actions(actions, group="blenderkit"), actions)

    def test_operator_source_items_collapse_blenderkit_aliases(self):
        actions = (
            BrowserAction("1", "OPERATOR", "bk.search", "bk", "Search", "", "bk.search()", "NONE", "OPERATOR"),
            BrowserAction(
                "2",
                "OPERATOR",
                "blenderkit.download",
                "blenderkit",
                "Download",
                "",
                "blenderkit.download()",
                "NONE",
                "OPERATOR",
            ),
        )

        with patch("pie_customizer.discovery.discover_operator_actions", return_value=actions):
            items = operator_group_items("EN")

        self.assertEqual(items[0][1], "All Sources")
        self.assertEqual([item[1] for item in items].count("BlenderKit"), 1)

    def test_ranked_search_prefers_exact_and_label_matches(self):
        actions = (
            BrowserAction("1", "OPERATOR", "mesh.delete_edgeloop", "mesh", "Delete Edge Loop", "", "mesh.delete_edgeloop()", "NONE", "OPERATOR"),
            BrowserAction("2", "OPERATOR", "object.delete", "object", "Delete", "", "object.delete()", "NONE", "OPERATOR"),
            BrowserAction("3", "OPERATOR", "outliner.id_delete", "outliner", "Delete ID", "", "outliner.id_delete()", "NONE", "OPERATOR"),
        )
        self.assertEqual(
            filter_actions(actions, "delete", rank_matches=True),
            (actions[1], actions[0], actions[2]),
        )

    def test_visible_label_prefix_beats_hidden_operator_prefix(self):
        actions = (
            BrowserAction("1", "OPERATOR", "mesh.faces_shade_flat", "mesh", "Shade Flat", "Display faces flat", "mesh.faces_shade_flat()", "NONE", "OPERATOR"),
            BrowserAction("2", "OPERATOR", "view3d.face_extract", "view3d", "Face Extract", "", "view3d.face_extract()", "NONE", "OPERATOR"),
        )
        self.assertEqual(
            filter_actions(actions, "face", rank_matches=True),
            (actions[1], actions[0]),
        )

    def test_current_mode_breaks_equal_search_ties(self):
        actions = (
            BrowserAction("1", "OPERATOR", "object.face_tool", "object", "Face Object Tool", "", "object.face_tool()", "NONE", "OPERATOR"),
            BrowserAction("2", "OPERATOR", "mesh.face_tool", "mesh", "Face Mesh Tool", "", "mesh.face_tool()", "NONE", "OPERATOR"),
        )
        self.assertEqual(
            filter_actions(
                actions,
                "face",
                rank_matches=True,
                context_mode="EDIT_MESH",
            ),
            (actions[1], actions[0]),
        )

    def test_favorites_and_recent_actions_break_equal_search_ties(self):
        actions = (
            BrowserAction("normal", "OPERATOR", "object.face_a", "object", "Face Alpha", "", "object.face_a()", "NONE", "OPERATOR"),
            BrowserAction("recent", "OPERATOR", "object.face_b", "object", "Face Bravo", "", "object.face_b()", "NONE", "OPERATOR"),
            BrowserAction("favorite", "OPERATOR", "object.face_c", "object", "Face Charlie", "", "object.face_c()", "NONE", "OPERATOR"),
        )
        self.assertEqual(
            filter_actions(
                actions,
                "face",
                rank_matches=True,
                favorite_tokens={"favorite"},
                recent_item_ids={"object.face_b"},
            ),
            (actions[2], actions[1], actions[0]),
        )

    def test_fuzzy_fallback_supports_command_palette_initials(self):
        action = BrowserAction(
            "1",
            "OPERATOR",
            "preferences.keymap_show",
            "preferences",
            "Open Default Keyboard Shortcuts",
            "",
            "preferences.keymap_show()",
            "NONE",
            "OPERATOR",
        )
        self.assertEqual(
            filter_actions(
                (action,),
                "odks",
                rank_matches=True,
                fuzzy_fallback=True,
            ),
            (action,),
        )

    def test_fuzzy_fallback_does_not_expand_a_full_direct_page(self):
        direct = tuple(
            BrowserAction(
                str(index),
                "OPERATOR",
                f"object.face_{index}",
                "object",
                f"Face {index}",
                "",
                f"object.face_{index}()",
                "NONE",
                "OPERATOR",
            )
            for index in range(12)
        )
        fuzzy = BrowserAction(
            "fuzzy",
            "OPERATOR",
            "object.foo_bar",
            "object",
            "Find Another Clever Example",
            "",
            "object.foo_bar()",
            "NONE",
            "OPERATOR",
        )
        self.assertEqual(
            filter_actions(
                direct + (fuzzy,),
                "face",
                rank_matches=True,
                fuzzy_fallback=True,
            ),
            direct,
        )

    def test_broad_categories_use_operator_meaning(self):
        cases = {
            "mesh.primitive_cube_add": "ADD",
            "object.select_all": "SELECT",
            "transform.rotate": "TRANSFORM",
            "view3d.view_axis": "VIEW",
            "anim.keyframe_insert": "ANIMATION",
            "mesh.bevel": "MESH",
            "sculpt.trim_box_gesture": "SCULPT",
            "sculpt_curves.brush_stroke": "SCULPT",
            "paint.mask_flood_fill": "SCULPT",
            "paint.hide_show": "SCULPT",
            "paint.visibility_invert": "SCULPT",
            "object.voxel_remesh": "SCULPT",
            "object.voxel_size_edit": "SCULPT",
            "paint.image_paint": "PAINT",
            "brush.asset_activate": "PAINT",
            "palette.color_add": "PAINT",
            "grease_pencil.brush_stroke": "PAINT",
            "graph.select_all": "ANIMATION",
            "node.add_search": "NODES",
            "object.delete": "OBJECT",
            "wm.save_as_mainfile": "OTHER",
        }
        for operator_id, expected in cases.items():
            action = BrowserAction(
                operator_id,
                "OPERATOR",
                operator_id,
                operator_id.split(".", 1)[0],
                operator_id,
                "",
                f"{operator_id}()",
                "NONE",
                "OPERATOR",
            )
            with self.subTest(operator_id=operator_id):
                self.assertEqual(broad_category_for_action(action), expected)

    def test_general_paint_and_brush_actions_use_paint_category(self):
        for operator_id in ("paint.image_paint", "brush.asset_activate"):
            group = operator_id.split(".", 1)[0]
            action = BrowserAction(
                operator_id,
                "OPERATOR",
                operator_id,
                group,
                operator_id,
                "",
                f"{operator_id}()",
                "NONE",
                "OPERATOR",
            )
            with self.subTest(operator_id=operator_id):
                self.assertEqual(broad_category_for_action(action), "PAINT")

    def test_broad_category_filter(self):
        actions = (
            BrowserAction("1", "OPERATOR", "object.delete", "object", "Delete", "", "object.delete()", "NONE", "OPERATOR"),
            BrowserAction("2", "OPERATOR", "mesh.bevel", "mesh", "Bevel", "", "mesh.bevel()", "NONE", "OPERATOR"),
            BrowserAction("3", "OPERATOR", "paint.mask_flood_fill", "paint", "Mask Flood Fill", "", "paint.mask_flood_fill()", "NONE", "OPERATOR"),
        )
        self.assertEqual(filter_broad_category(actions, "MESH"), (actions[1],))
        self.assertEqual(filter_broad_category(actions, "SCULPT"), (actions[2],))

    def test_domain_categories_win_over_generic_action_names(self):
        cases = {
            "grease_pencil.select_all": "PAINT",
            "grease_pencil.layer_add": "PAINT",
            "graph.select_all": "ANIMATION",
            "nla.add_actionclip": "ANIMATION",
            "node.select_all": "NODES",
            "node.add_search": "NODES",
        }
        for operator_id, expected in cases.items():
            group = operator_id.split(".", 1)[0]
            action = BrowserAction(
                operator_id,
                "OPERATOR",
                operator_id,
                group,
                operator_id,
                "",
                f"{operator_id}()",
                "NONE",
                "OPERATOR",
            )
            with self.subTest(operator_id=operator_id):
                self.assertEqual(broad_category_for_action(action), expected)

    def test_curated_sculpt_actions_keep_sculpt_category(self):
        for action_id in (
            "mode_sculpt",
            "sculpt_voxel_remesh",
            "sculpt_mask_fill",
            "sculpt_mirror_x",
            "sculpt_overlay_mask",
        ):
            catalog_action = next(
                action for action in SEARCH_ACTIONS if action.action_id == action_id
            )
            action = BrowserAction(
                f"CURATED:{action_id}",
                "CURATED",
                action_id,
                catalog_action_group(catalog_action),
                action_id,
                "",
                catalog_action.command,
                catalog_action.icon,
                catalog_action.slot_type,
            )
            with self.subTest(action_id=action_id):
                self.assertEqual(broad_category_for_action(action), "SCULPT")

    def test_curated_variant_keeps_its_human_category(self):
        action = BrowserAction(
            "CURATED:orientation_local",
            "CURATED",
            "orientation_local",
            "transform",
            "Ориентация: Локальная",
            "",
            "transform.select_orientation(orientation='LOCAL')",
            "ORIENTATION_LOCAL",
            "OPERATOR",
        )
        self.assertEqual(broad_category_for_action(action), "TRANSFORM")

    def test_curated_paint_actions_keep_paint_category(self):
        for action_id in (
            "mode_vertex_paint",
            "mode_weight_paint",
            "mode_texture_paint",
            "paint_flip_colors",
            "paint_sample_color",
        ):
            catalog_action = next(
                action for action in SEARCH_ACTIONS if action.action_id == action_id
            )
            action = BrowserAction(
                f"CURATED:{action_id}",
                "CURATED",
                action_id,
                catalog_action_group(catalog_action),
                action_id,
                "",
                catalog_action.command,
                catalog_action.icon,
                catalog_action.slot_type,
            )
            with self.subTest(action_id=action_id):
                self.assertEqual(broad_category_for_action(action), "PAINT")

    def test_technical_and_addon_groups_have_readable_names(self):
        self.assertEqual(group_label("action", "RU"), "Редактор действий и ключевые кадры")
        self.assertEqual(group_label("anim", "RU"), "Инструменты анимации")
        self.assertEqual(group_label("asset", "RU"), "Ассеты и библиотеки")
        self.assertEqual(group_label("ed", "RU"), "Системные операции редактирования")
        self.assertEqual(group_label("geometry", "RU"), "Атрибуты геометрии")
        self.assertEqual(group_label("info", "RU"), "Отчёты и история операций")
        self.assertEqual(group_label("pie_customizer", "RU"), "Pie Customizer")
        self.assertEqual(group_label("preferences", "RU"), "Настройки Blender")
        self.assertEqual(group_label("wm", "RU"), "Общие команды")
        self.assertEqual(group_label("object", "RU"), "Действия с объектами")
        self.assertEqual(group_label("object_modifiers", "RU"), "Модификаторы")
        self.assertEqual(group_label("object_modifiers", "EN"), "Modifiers")
        self.assertEqual(
            group_label("grease_pencil_modifiers", "RU"),
            "Модификаторы Grease Pencil",
        )
        self.assertEqual(group_label("physics_modifiers", "EN"), "Physics Modifiers")
        self.assertEqual(group_label("mesh", "RU"), "Операции с сеткой")
        self.assertEqual(group_label("transform", "RU"), "Инструменты трансформации")
        self.assertEqual(group_label("rigidbody", "RU"), "Физика твёрдых тел")
        self.assertEqual(group_label("rigidbody", "EN"), "Rigid Body Physics")
        self.assertEqual(group_label("sculpt_brushes_general", "RU"), "Кисти: Основные")
        self.assertEqual(group_label("sculpt_brushes_paint", "EN"), "Paint Brushes")
        self.assertEqual(
            group_label("sculpt_brushes_simulation", "RU"),
            "Кисти: Симуляция",
        )
        self.assertEqual(
            group_label("paint_brushes_texture", "EN"),
            "Texture Paint Brushes",
        )
        self.assertEqual(group_label("text", "RU"), "Текстовый редактор")
        self.assertEqual(group_label("text_editor", "RU"), "Настройки текстового редактора")
        self.assertEqual(group_label("ui", "RU"), "Элементы интерфейса")
        self.assertEqual(group_label("world", "RU"), "Мир сцены")
        self.assertEqual(group_label("bc", "RU"), "BoxCutter")
        self.assertEqual(group_label("bk", "RU"), "BlenderKit")
        self.assertEqual(group_label("bpm", "RU"), "Better Pie Menus")
        self.assertEqual(group_label("cbl", "RU"), "Cablerator")
        self.assertEqual(group_label("hops", "RU"), "Hard Ops")
        self.assertEqual(group_label("mball", "RU"), "Метасферы")
        self.assertEqual(group_label("nla", "RU"), "Нелинейная анимация")

    def test_unknown_groups_use_plugin_icon(self):
        self.assertEqual(group_icon("future_addon_namespace"), "PLUGIN")
        self.assertNotEqual(group_icon("asset"), "DOT")


if __name__ == "__main__":
    unittest.main()
