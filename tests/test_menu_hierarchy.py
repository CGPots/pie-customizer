import unittest
from types import SimpleNamespace

from pie_customizer.menu_hierarchy import build_menu_hierarchy, hierarchy_new_order


def slot(command, *, enabled=True, slot_type="MENU"):
    return SimpleNamespace(
        enabled=enabled,
        slot_type=slot_type,
        command=command,
    )


def menu(*slots):
    return SimpleNamespace(slots=slots)


class MenuHierarchyTest(unittest.TestCase):
    def test_parent_and_two_children_use_indentation(self):
        menus = (
            menu(slot("menu-directions"), slot("menu-centers")),
            menu(),
            menu(),
        )

        rows = build_menu_hierarchy(
            menus,
            ("menu-main", "menu-directions", "menu-centers"),
        )

        self.assertEqual([row.index for row in rows], [0, 1, 2])
        self.assertEqual([row.prefix for row in rows], ["", "", ""])
        self.assertEqual([row.depth for row in rows], [0, 1, 1])
        self.assertTrue(rows[0].has_children)
        self.assertEqual(rows[1].parent_index, 0)
        self.assertEqual(rows[2].parent_index, 0)

    def test_deep_tree_uses_depth_without_connector_characters(self):
        menus = (
            menu(slot("menu-a"), slot("menu-b")),
            menu(slot("menu-a-child")),
            menu(),
            menu(),
        )

        rows = build_menu_hierarchy(
            menus,
            ("root", "menu-a", "menu-b", "menu-a-child"),
        )

        self.assertEqual([row.index for row in rows], [0, 1, 3, 2])
        self.assertEqual(
            [row.prefix for row in rows],
            ["", "", "", ""],
        )
        self.assertEqual([row.depth for row in rows], [0, 1, 2, 1])
        self.assertEqual(hierarchy_new_order(rows, 4), [0, 1, 3, 2])

    def test_disabled_and_non_menu_slots_do_not_create_links(self):
        menus = (
            menu(
                slot("child", enabled=False),
                slot("child", slot_type="OPERATOR"),
            ),
            menu(),
        )

        rows = build_menu_hierarchy(menus, ("root", "child"))

        self.assertEqual([row.index for row in rows], [0, 1])
        self.assertEqual([row.depth for row in rows], [0, 0])

    def test_cycle_is_rendered_once_without_recursion(self):
        menus = (
            menu(slot("second")),
            menu(slot("first")),
        )

        rows = build_menu_hierarchy(menus, ("first", "second"))

        self.assertEqual([row.index for row in rows], [0, 1])
        self.assertEqual([row.depth for row in rows], [0, 1])
        self.assertEqual(rows[1].prefix, "")

    def test_shared_child_is_shown_under_each_visual_parent(self):
        menus = (
            menu(slot("shared")),
            menu(slot("shared")),
            menu(),
        )

        rows = build_menu_hierarchy(menus, ("first", "second", "shared"))
        shared_rows = [row for row in rows if row.index == 2]

        self.assertEqual([row.index for row in rows], [0, 2, 1, 2])
        self.assertEqual([row.parent_index for row in shared_rows], [0, 1])
        self.assertEqual(
            [row.reference_count for row in shared_rows],
            [2, 2],
        )
        self.assertNotEqual(
            shared_rows[0].occurrence_key,
            shared_rows[1].occurrence_key,
        )
        self.assertEqual(hierarchy_new_order(rows, 3), [])


if __name__ == "__main__":
    unittest.main()
