import unittest

from pie_customizer.ui_style import (
    CATALOG_GRID_COLUMNS,
    CATALOG_MODE_HEIGHT,
    CATALOG_PAGE_SIZE,
    CATALOG_TOP_SPACING,
    DIVIDER_HEIGHT,
    PIE_DIRECTION_ARROWS,
    SECTION_BOTTOM_SPACING,
    SECTION_HEADER_HEIGHT,
    SECTION_SIDE_PADDING,
    SPACING_LARGE,
    SPACING_MEDIUM,
    SPACING_SECTION,
    SPACING_SMALL,
    SPACING_TIGHT,
    draw_section_header,
    draw_space,
    draw_subsection_divider,
    inset_layout,
)


class FakeLayout:
    def __init__(self):
        self.separators = []
        self.labels = []
        self.boxes = 0

    def separator(self, **kwargs):
        self.separators.append(kwargs)

    def row(self):
        return self

    def box(self):
        self.boxes += 1
        return self

    def column(self):
        return self

    def label(self, **kwargs):
        self.labels.append(kwargs)


class UIStyleTest(unittest.TestCase):
    def test_spacing_scale_is_ordered(self):
        self.assertLess(SPACING_TIGHT, SPACING_SMALL)
        self.assertLess(SPACING_SMALL, SPACING_MEDIUM)
        self.assertLess(SPACING_MEDIUM, SPACING_SECTION)
        self.assertLess(SPACING_SECTION, SPACING_LARGE)

    def test_catalog_mode_is_visually_emphasized(self):
        self.assertEqual(CATALOG_MODE_HEIGHT, 1.35)
        self.assertGreater(CATALOG_TOP_SPACING, SPACING_LARGE)

    def test_catalog_pages_fill_both_supported_grid_widths(self):
        self.assertEqual(CATALOG_GRID_COLUMNS, 3)
        self.assertEqual(CATALOG_PAGE_SIZE, 12)
        self.assertEqual(CATALOG_PAGE_SIZE % CATALOG_GRID_COLUMNS, 0)
        self.assertEqual(CATALOG_PAGE_SIZE % 2, 0)

    def test_section_headers_are_emphasized(self):
        self.assertEqual(SECTION_HEADER_HEIGHT, 1.2)
        self.assertEqual(SECTION_BOTTOM_SPACING, SPACING_MEDIUM)

    def test_section_header_uses_static_semantic_icon(self):
        layout = FakeLayout()
        self.assertIs(draw_section_header(layout, "Section", "MENU_PANEL"), layout)
        self.assertEqual(
            layout.labels,
            [{"text": "Section", "icon": "MENU_PANEL"}],
        )
        self.assertEqual(layout.boxes, 0)

    def test_section_content_has_symmetric_side_padding(self):
        layout = FakeLayout()
        self.assertIs(inset_layout(layout), layout)
        self.assertEqual(
            layout.separators,
            [
                {"factor": SECTION_SIDE_PADDING, "type": "SPACE"},
                {"factor": SECTION_SIDE_PADDING, "type": "SPACE"},
            ],
        )

    def test_pie_direction_arrows_cover_all_slots(self):
        self.assertEqual(
            PIE_DIRECTION_ARROWS,
            {
                "0": "←",
                "1": "→",
                "2": "↓",
                "3": "↑",
                "4": "↖",
                "5": "↗",
                "6": "↙",
                "7": "↘",
            },
        )

    def test_space_never_uses_auto_separator(self):
        layout = FakeLayout()
        draw_space(layout, SPACING_TIGHT)
        self.assertEqual(
            layout.separators,
            [{"factor": SPACING_TIGHT, "type": "SPACE"}],
        )

    def test_subsection_divider_is_symmetric(self):
        layout = FakeLayout()
        draw_subsection_divider(layout)
        self.assertEqual(
            layout.separators,
            [
                {"factor": SPACING_MEDIUM, "type": "SPACE"},
                {"factor": DIVIDER_HEIGHT, "type": "SPACE"},
                {"factor": SPACING_MEDIUM, "type": "SPACE"},
            ],
        )

if __name__ == "__main__":
    unittest.main()
