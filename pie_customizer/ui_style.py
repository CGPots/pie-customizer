"""Shared spacing and sizing rules for Pie Customizer UI."""

SPACING_TIGHT = 0.25
SPACING_SMALL = 0.45
SPACING_MEDIUM = 0.65
SPACING_SECTION = 0.75
SPACING_LARGE = 1.5
CATALOG_TOP_SPACING = 3.0
CATALOG_PAGE_SIZE = 12
CATALOG_GRID_COLUMNS = 3

DIVIDER_HEIGHT = 0.1
SECTION_HEADER_HEIGHT = 1.2
SECTION_SIDE_PADDING = 0.5
SECTION_BOTTOM_SPACING = 0.65
SECTION_BUTTON_HEIGHT = 1.25
PIE_BUTTON_HEIGHT = 1.4
CATALOG_MODE_HEIGHT = 1.35

PIE_DIRECTION_ARROWS = {
    "0": "←",
    "1": "→",
    "2": "↓",
    "3": "↑",
    "4": "↖",
    "5": "↗",
    "6": "↙",
    "7": "↘",
}


def draw_space(layout, factor: float) -> None:
    layout.separator(factor=factor, type="SPACE")


def inset_layout(layout):
    row = layout.row()
    row.separator(factor=SECTION_SIDE_PADDING, type="SPACE")
    content = row.column()
    row.separator(factor=SECTION_SIDE_PADDING, type="SPACE")
    return content


def draw_section_header(layout, text: str, icon: str):
    header = layout.row()
    header.scale_y = SECTION_HEADER_HEIGHT
    header.separator(factor=SECTION_SIDE_PADDING, type="SPACE")
    header.label(text=text, icon=icon)
    return header


def draw_subsection_divider(layout) -> None:
    draw_space(layout, SPACING_MEDIUM)
    draw_space(layout, DIVIDER_HEIGHT)
    draw_space(layout, SPACING_MEDIUM)
