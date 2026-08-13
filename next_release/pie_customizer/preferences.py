"""Add-on preferences UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty

from . import runtime
from .action_parser import parse_operator_command
from .availability import mode_label
from .command_catalog import (
    ACTIONS,
    SEARCH_ACTIONS,
    action_label,
    catalog_action_group,
)
from .discovery import (
    BrowserAction,
    broad_category_for_action,
    canonical_operator_group,
    discover_brush_asset_actions,
    discover_operator_actions,
    filter_actions,
    filter_broad_category,
    group_icon,
    group_label,
    operator_group_items,
    recent_operator_actions,
)
from .localization import effective_language, t
from .menu_hierarchy import build_menu_hierarchy
from .model import PC_FavoriteAction, PC_MenuHierarchyEntry, PC_PieMenu
from .operator_parameters import operator_has_editable_parameters
from .shortcuts import shortcut_display
from .ui_style import (
    CATALOG_GRID_COLUMNS,
    CATALOG_MODE_HEIGHT,
    CATALOG_PAGE_SIZE,
    CATALOG_TOP_SPACING,
    PIE_DIRECTION_ARROWS,
    PIE_BUTTON_HEIGHT,
    SECTION_BUTTON_HEIGHT,
    SECTION_BOTTOM_SPACING,
    SPACING_MEDIUM,
    SPACING_SECTION,
    SPACING_SMALL,
    SPACING_TIGHT,
    draw_section_header,
    draw_space,
    draw_subsection_divider,
    inset_layout,
)


POSITION_GRID = (
    ("4", "3", "5"),
    ("0", None, "1"),
    ("6", "2", "7"),
)

CATALOG_MODE_ITEMS = {
    "RU": (
        ("POPULAR", "Популярное", "Проверенные популярные команды", "SOLO_ON", 0),
        ("ALL", "Поиск", "Поиск по всем операторам Blender и включённых аддонов", "VIEWZOOM", 1),
        ("RECENT", "Недавние", "Недавно выполненные действия Blender", "RECOVER_LAST", 2),
        ("FAVORITES", "Избранное", "Сохранённые действия", "HEART", 3),
        ("NESTED", "Вложенное меню", "Открыть другое созданное круговое меню", "MENU_PANEL", 4),
        ("CUSTOM", "Своя команда", "Ручная настройка действия", "PREFERENCES", 5),
    ),
    "EN": (
        ("POPULAR", "Popular", "Curated popular commands", "SOLO_ON", 0),
        ("ALL", "Search", "Search all Blender and enabled add-on operators", "VIEWZOOM", 1),
        ("RECENT", "Recent", "Recently used Blender actions", "RECOVER_LAST", 2),
        ("FAVORITES", "Favorites", "Saved actions", "HEART", 3),
        ("NESTED", "Nested Menu", "Open another custom pie menu", "MENU_PANEL", 4),
        ("CUSTOM", "Custom Command", "Configure an action manually", "PREFERENCES", 5),
    ),
}

CATALOG_BROWSE_MODE_ITEMS = {
    "RU": (
        ("SEARCH", "Поиск", "Найти команду по названию или operator id", "NONE", 0),
        ("SECTIONS", "Разделы", "Просматривать команды по крупным разделам", "NONE", 1),
    ),
    "EN": (
        ("SEARCH", "Search", "Find a command by name or operator id", "NONE", 0),
        ("SECTIONS", "Sections", "Browse commands by broad section", "NONE", 1),
    ),
}

BROAD_CATEGORIES = (
    ("ADD", "Добавление", "Add", "ADD"),
    ("OBJECT", "Объект", "Object", "OBJECT_DATA"),
    ("MESH", "Сетка и моделирование", "Mesh & Modeling", "MESH_DATA"),
    ("SCULPT", "Скульптинг", "Sculpting", "SCULPTMODE_HLT"),
    ("PAINT", "Рисование", "Painting", "BRUSH_DATA"),
    ("NODES", "Ноды", "Nodes", "NODETREE"),
    ("TRANSFORM", "Трансформация", "Transform", "ORIENTATION_GLOBAL"),
    ("SELECT", "Выделение", "Selection", "RESTRICT_SELECT_OFF"),
    ("VIEW", "Редакторы и вид", "Editors & View", "VIEW3D"),
    ("ANIMATION", "Анимация", "Animation", "ACTION"),
    ("OTHER", "Другое и аддоны", "Other & Add-ons", "DOT"),
)

BROAD_CATEGORY_MAP = {item[0]: item for item in BROAD_CATEGORIES}
TECHNICAL_PARAMETER_OPERATOR_IDS = {
    "brush.asset_activate",
    "wm.context_set_enum",
    "wm.tool_set_by_id",
}


def _reset_catalog_page(self, context):
    self.catalog_page = 0


def _reset_catalog_navigation(self, context):
    self.catalog_page = 0
    self.catalog_section = ""
    self.catalog_group = ""
    self.command_search = ""


def _operator_group_enum_items(self, context):
    return operator_group_items(effective_language(context))


def _slot_has_operator_parameters(slot) -> bool:
    try:
        parsed = parse_operator_command(slot.command)
    except ValueError:
        return False
    if parsed.operator_id in TECHNICAL_PARAMETER_OPERATOR_IDS:
        return False
    return operator_has_editable_parameters(parsed.operator_id)


def _catalog_mode_enum_items(self, context):
    return CATALOG_MODE_ITEMS[effective_language(context)]


def _catalog_browse_mode_enum_items(self, context):
    return CATALOG_BROWSE_MODE_ITEMS[effective_language(context)]


def _broad_category_label(prefs, category: str) -> str:
    item = BROAD_CATEGORY_MAP.get(category)
    if item is None:
        return category
    return item[2] if effective_language() == "EN" else item[1]


def _catalog_browser_action(action, language: str) -> BrowserAction:
    return BrowserAction(
        token=f"CURATED:{action.action_id}",
        kind="CURATED",
        item_id=action.action_id,
        group=catalog_action_group(action),
        label=action_label(action, language),
        description=action.command,
        command=action.command,
        icon=action.icon,
        slot_type=action.slot_type,
        operator_context=action.operator_context,
        search_terms=f"{action.label_ru} {action.label_en} {action.action_id} {action.command}",
    )


def _searchable_browser_actions(prefs) -> tuple[BrowserAction, ...]:
    language = effective_language()
    discovered = discover_operator_actions()
    brush_assets = discover_brush_asset_actions()
    discovered_by_command = {action.command: action for action in discovered}
    curated = tuple(
        _catalog_browser_action(action, language)
        for action in SEARCH_ACTIONS
    )
    curated = tuple(
        replace(
            action,
            search_terms=(
                f"{action.search_terms} {discovered_by_command[action.command].search_terms}"
                if action.command in discovered_by_command
                else action.search_terms
            ),
        )
        for action in curated
    )
    curated_commands = {action.command for action in curated}
    unique_discovered = tuple(
        action
        for action in discovered
        if action.command not in curated_commands
    )
    return curated + brush_assets + unique_discovered


def _favorite_browser_actions(prefs) -> tuple[BrowserAction, ...]:
    return tuple(
        BrowserAction(
            token=favorite.token,
            kind=favorite.kind,
            item_id=favorite.item_id,
            group=favorite.group,
            label=favorite.label,
            description=favorite.description,
            command=favorite.command,
            icon=favorite.icon,
            slot_type=favorite.slot_type,
            operator_context=favorite.operator_context,
        )
        for favorite in prefs.favorite_actions
    )


def _set_browser_action_properties(operator, action: BrowserAction) -> None:
    operator.item_id = action.item_id
    operator.label = action.label
    operator.tooltip = action.description
    operator.command = action.command
    operator.icon = action.icon
    operator.slot_type = action.slot_type
    operator.operator_context = action.operator_context


def _set_favorite_properties(operator, action: BrowserAction) -> None:
    operator.token = action.token
    operator.kind = action.kind
    operator.item_id = action.item_id
    operator.group = action.group
    operator.label = action.label
    operator.tooltip = action.description
    operator.command = action.command
    operator.icon = action.icon
    operator.slot_type = action.slot_type
    operator.operator_context = action.operator_context


def _draw_action_grid(
    layout,
    prefs,
    actions: tuple[BrowserAction, ...],
    columns: int = 2,
    duplicate_labels: frozenset[str] = frozenset(),
    duplicate_sources: frozenset[tuple[str, str]] = frozenset(),
) -> None:
    favorite_tokens = {favorite.token for favorite in prefs.favorite_actions}
    grid = layout.grid_flow(
        row_major=True,
        columns=columns,
        even_columns=True,
        even_rows=True,
        align=False,
    )
    for action in actions:
        label_key = action.label.casefold()
        source_key = (label_key, canonical_operator_group(action.group))
        display_label = action.label
        if label_key in duplicate_labels:
            source = (
                action.item_id
                if source_key in duplicate_sources
                else group_label(
                    canonical_operator_group(action.group),
                    effective_language(),
                )
            )
            display_label = f"{action.label} | {source}"
        cell = grid.row(align=True)
        assign = cell.operator(
            "pie_customizer.assign_browser_action",
            text=display_label,
            icon=runtime.safe_icon(action.icon),
        )
        _set_browser_action_properties(assign, action)
        favorite = cell.operator(
            "pie_customizer.toggle_favorite",
            text="",
            icon="HEART",
            depress=action.token in favorite_tokens,
        )
        _set_favorite_properties(favorite, action)


def _draw_browser_actions(
    layout,
    prefs,
    actions: tuple[BrowserAction, ...],
    columns: int = 2,
) -> None:
    total = len(actions)
    if total == 0:
        layout.label(text=t(prefs, "catalog_empty"), icon="INFO")
        return

    page_count = max(1, (total + CATALOG_PAGE_SIZE - 1) // CATALOG_PAGE_SIZE)
    page = min(prefs.catalog_page, page_count - 1)
    start = page * CATALOG_PAGE_SIZE
    visible_actions = actions[start : start + CATALOG_PAGE_SIZE]
    label_counts = Counter(action.label.casefold() for action in actions)
    source_counts = Counter(
        (action.label.casefold(), canonical_operator_group(action.group))
        for action in actions
    )
    _draw_action_grid(
        layout,
        prefs,
        visible_actions,
        columns=columns,
        duplicate_labels=frozenset(
            label for label, count in label_counts.items() if count > 1
        ),
        duplicate_sources=frozenset(
            source for source, count in source_counts.items() if count > 1
        ),
    )

    if page_count == 1:
        return

    draw_space(layout, SPACING_SMALL)
    navigation = layout.row(align=True)
    previous = navigation.row(align=True)
    previous.enabled = page > 0
    previous.operator("pie_customizer.catalog_page", text="", icon="TRIA_LEFT").direction = -1
    navigation.label(text=f"{page + 1} / {page_count}  ({total})")
    following = navigation.row(align=True)
    following.enabled = page + 1 < page_count
    following.operator("pie_customizer.catalog_page", text="", icon="TRIA_RIGHT").direction = 1


def _draw_search_home(layout, prefs) -> None:
    draw_space(layout, SPACING_SMALL)
    layout.label(text=t(prefs, "catalog_search_hint"), icon="INFO")


def _available_categories(actions: tuple[BrowserAction, ...]) -> tuple[tuple[str, str, str, str], ...]:
    available = {broad_category_for_action(action) for action in actions}
    return tuple(item for item in BROAD_CATEGORIES if item[0] in available)


def _draw_section_root(layout, prefs, actions: tuple[BrowserAction, ...] | None = None) -> None:
    categories = _available_categories(actions) if actions is not None else BROAD_CATEGORIES
    if not categories:
        layout.label(text=t(prefs, "catalog_empty"), icon="INFO")
        return

    language = effective_language()
    for index, (category, label_ru, label_en, icon) in enumerate(categories):
        label = label_en if language == "EN" else label_ru
        row = layout.row(align=True)
        row.scale_y = SECTION_BUTTON_HEIGHT
        operator = row.operator(
            "pie_customizer.select_catalog_section",
            text=label,
            icon=icon,
        )
        operator.section = category
        if index + 1 < len(categories):
            draw_space(layout, SPACING_TIGHT)


def _draw_section_header(layout, prefs, category: str) -> None:
    item = BROAD_CATEGORY_MAP.get(category)
    icon = item[3] if item else "DOT"
    row = layout.row(align=True)
    back = row.operator("pie_customizer.select_catalog_section", text="", icon="TRIA_LEFT")
    back.section = ""
    row.label(text=_broad_category_label(prefs, category), icon=icon)


def _grouped_actions(actions: tuple[BrowserAction, ...], language: str):
    grouped = {}
    for action in actions:
        grouped.setdefault(action.group, []).append(action)
    return tuple(
        (group, tuple(grouped[group]))
        for group in sorted(grouped, key=lambda value: group_label(value, language).casefold())
    )


def _draw_grouped_actions(layout, prefs, actions: tuple[BrowserAction, ...]) -> None:
    language = effective_language()
    groups = _grouped_actions(actions, language)
    if not groups:
        layout.label(text=t(prefs, "catalog_empty"), icon="INFO")
        return

    for index, (group, group_actions) in enumerate(groups):
        heading = layout.row(align=True)
        heading.label(
            text=group_label(group, language).upper(),
            icon=runtime.safe_icon(group_icon(group)),
        )
        draw_space(layout, SPACING_TIGHT)
        _draw_action_grid(layout, prefs, group_actions, columns=CATALOG_GRID_COLUMNS)
        if index + 1 < len(groups):
            draw_space(layout, SPACING_MEDIUM)


def _draw_group_root(layout, prefs, actions: tuple[BrowserAction, ...]) -> None:
    language = effective_language()
    groups = _grouped_actions(actions, language)
    if not groups:
        layout.label(text=t(prefs, "catalog_empty"), icon="INFO")
        return

    for index, (group, _group_actions) in enumerate(groups):
        row = layout.row(align=True)
        row.scale_y = SECTION_BUTTON_HEIGHT
        operator = row.operator(
            "pie_customizer.select_catalog_group",
            text=group_label(group, language),
            icon=runtime.safe_icon(group_icon(group)),
        )
        operator.group = group
        if index + 1 < len(groups):
            draw_space(layout, SPACING_TIGHT)


def _draw_group_header(layout, prefs, group: str) -> None:
    row = layout.row(align=True)
    back = row.operator("pie_customizer.select_catalog_group", text="", icon="TRIA_LEFT")
    back.group = ""
    row.label(
        text=group_label(group, effective_language()),
        icon=runtime.safe_icon(group_icon(group)),
    )


def _draw_custom_action_editor(layout, prefs, slot) -> None:
    layout.prop(slot, "slot_type", text=t(prefs, "slot_type"))
    if slot.slot_type == "SEPARATOR":
        return

    draw_space(layout, SPACING_MEDIUM)
    layout.prop(slot, "command", text=t(prefs, "command"))

    if slot.slot_type == "OPERATOR":
        draw_space(layout, SPACING_MEDIUM)
        layout.prop(slot, "operator_context", text=t(prefs, "run_mode"))

    help_key = {
        "OPERATOR": "operator_help",
        "PROPERTY": "property_help",
        "MENU": "menu_help",
    }.get(slot.slot_type)
    if help_key:
        draw_space(layout, SPACING_MEDIUM)
        layout.label(text=t(prefs, help_key), icon="INFO")


def _draw_nested_menu_actions(layout, prefs, active_menu) -> None:
    targets = tuple(
        menu
        for menu in prefs.pie_menus
        if menu.uid != active_menu.uid and menu.enabled
    )
    if not targets:
        layout.label(text=t(prefs, "nested_menu_empty"), icon="INFO")
        return

    grid = layout.grid_flow(
        row_major=True,
        columns=2,
        even_columns=True,
        even_rows=True,
        align=False,
    )
    for target in targets:
        assign = grid.operator(
            "pie_customizer.assign_browser_action",
            text=target.name,
            icon="MENU_PANEL",
        )
        assign.item_id = target.uid
        assign.label = target.name
        assign.tooltip = f"{t(prefs, 'nested_menu_description')}: {target.name}"
        assign.command = runtime.menu_id_for(target)
        assign.icon = "MENU_PANEL"
        assign.slot_type = "MENU"
        assign.operator_context = "INVOKE_DEFAULT"


def _active_pie_menu(prefs):
    if not prefs.pie_menus:
        return None
    index = min(max(prefs.active_menu_index, 0), len(prefs.pie_menus) - 1)
    menu = prefs.pie_menus[index]
    runtime.ensure_menu_shape(menu)
    return menu


def _menu_availability_text(prefs, menu) -> str:
    if not menu.mode_filter_enabled:
        return t(prefs, "all_modes")

    selected = sorted(menu.allowed_modes)
    if len(selected) == 1:
        return mode_label(selected[0], effective_language())
    return t(prefs, "modes_selected").format(count=len(selected))


def _menu_hierarchy_rows(prefs):
    menus = list(prefs.pie_menus)
    menu_ids = [runtime.menu_id_for(menu) if menu.uid else "" for menu in menus]
    return build_menu_hierarchy(menus, menu_ids)


def _menu_index_by_uid(prefs, menu_uid: str) -> int | None:
    for index, menu in enumerate(prefs.pie_menus):
        if menu.uid == menu_uid:
            return index
    return None


def _active_hierarchy_entry_changed(prefs, context) -> None:
    index = prefs.active_hierarchy_index
    if index < 0 or index >= len(prefs.menu_hierarchy_entries):
        return
    menu_index = _menu_index_by_uid(
        prefs,
        prefs.menu_hierarchy_entries[index].menu_uid,
    )
    if menu_index is not None:
        prefs.active_menu_index = menu_index


def _sync_menu_hierarchy_entries(prefs) -> None:
    rows = _menu_hierarchy_rows(prefs)
    desired = [
        (
            prefs.pie_menus[row.index].uid,
            row.prefix,
            row.depth,
            row.occurrence_key,
        )
        for row in rows
    ]
    current = [
        (entry.menu_uid, entry.prefix, entry.depth, entry.occurrence_key)
        for entry in prefs.menu_hierarchy_entries
    ]

    selected_occurrence = ""
    if 0 <= prefs.active_hierarchy_index < len(prefs.menu_hierarchy_entries):
        selected_occurrence = prefs.menu_hierarchy_entries[
            prefs.active_hierarchy_index
        ].occurrence_key

    if current != desired:
        prefs.menu_hierarchy_entries.clear()
        for menu_uid, prefix, depth, occurrence_key in desired:
            entry = prefs.menu_hierarchy_entries.add()
            entry.menu_uid = menu_uid
            entry.prefix = prefix
            entry.depth = depth
            entry.occurrence_key = occurrence_key

    active_uid = ""
    if prefs.pie_menus:
        active_index = min(
            max(prefs.active_menu_index, 0),
            len(prefs.pie_menus) - 1,
        )
        active_uid = prefs.pie_menus[active_index].uid

    selected_index = next(
        (
            index
            for index, entry in enumerate(prefs.menu_hierarchy_entries)
            if entry.occurrence_key == selected_occurrence
            and entry.menu_uid == active_uid
        ),
        -1,
    )
    if selected_index < 0:
        selected_index = next(
            (
                index
                for index, entry in enumerate(prefs.menu_hierarchy_entries)
                if entry.menu_uid == active_uid
            ),
            0,
        )
    prefs.active_hierarchy_index = selected_index


def _draw_menus_content(layout, prefs) -> None:
    _sync_menu_hierarchy_entries(prefs)
    menu_row = layout.row()
    menu_row.template_list(
        "PC_UL_PieMenuList",
        "",
        prefs,
        "menu_hierarchy_entries",
        prefs,
        "active_hierarchy_index",
        rows=3,
    )
    menu_buttons = menu_row.column(align=True)
    menu_buttons.operator("pie_customizer.add_menu", text="", icon="ADD")
    menu_buttons.operator("pie_customizer.duplicate_menu", text="", icon="DUPLICATE")
    menu_buttons.operator("pie_customizer.remove_menu", text="", icon="TRASH")

    if prefs.pie_menus:
        draw_space(layout, SPACING_TIGHT)
        apply_row = layout.row(align=True)
        apply_row.operator("pie_customizer.rebuild", text=t(prefs, "apply"), icon="CHECKMARK")
        draw_space(layout, SPACING_SMALL)
        layout.label(text=t(prefs, "apply_help"), icon="INFO")
    else:
        draw_space(layout, SPACING_SMALL)
        layout.label(text=t(prefs, "empty_state"), icon="INFO")


def _draw_slots_content(layout, prefs, context, menu) -> None:
    workspace_shell = layout.column()
    workspace = workspace_shell.split(factor=0.46)
    position_box = workspace.column()
    for row_index, position_row in enumerate(POSITION_GRID):
        position_grid = position_box.grid_flow(
            row_major=True,
            columns=3,
            even_columns=True,
            even_rows=True,
            align=False,
        )
        for position in position_row:
            cell = position_grid.row(align=True)
            cell.scale_y = PIE_BUTTON_HEIGHT
            if position is None:
                cell.alignment = "CENTER"
                cell.label(text=PIE_DIRECTION_ARROWS[menu.active_slot_position])
                continue
            candidate = menu.slots[int(position)]
            is_assigned = candidate.slot_type != "SEPARATOR" and bool(candidate.command.strip())
            button_text = candidate.label if is_assigned and candidate.label else t(prefs, "empty_slot")
            button_icon = runtime.safe_icon(candidate.icon) if is_assigned else "NONE"
            if is_assigned and not candidate.enabled:
                select = cell.operator(
                    "pie_customizer.select_slot",
                    text=button_text,
                    icon=button_icon,
                    emboss=False,
                )
                select.position = position
            else:
                cell.prop_enum(
                    menu,
                    "active_slot_position",
                    position,
                    text=button_text,
                    icon=button_icon,
                )
        if row_index + 1 < len(POSITION_GRID):
            draw_space(position_box, SPACING_SMALL)

    slot = menu.slots[int(menu.active_slot_position)]
    details_region = workspace.row()
    details_region.separator(type="SPACE")
    details_box = details_region.column()
    if slot.slot_type == "SEPARATOR":
        details_box.label(text=t(prefs, "empty_position"), icon="INFO")
    else:
        controls = details_box.row(align=True)
        controls.prop(slot, "enabled", text="")
        controls.prop(slot, "label", text="")
        choose_icon = controls.operator(
            "pie_customizer.choose_slot_icon",
            text="",
            icon=(
                runtime.safe_icon(slot.icon)
                if runtime.safe_icon(slot.icon) != "NONE"
                else "IMAGE_DATA"
            ),
        )
        choose_icon.menu_uid = menu.uid
        choose_icon.slot_position = menu.active_slot_position
        controls.operator("pie_customizer.clear_slot", text="", icon="TRASH")

    if (
        prefs.catalog_mode != "CUSTOM"
        and slot.slot_type == "OPERATOR"
        and _slot_has_operator_parameters(slot)
    ):
        draw_space(details_box, SPACING_TIGHT)
        configure = details_box.operator(
            "pie_customizer.configure_operator",
            text=t(prefs, "operator_parameters"),
            icon="OPTIONS",
        )
        configure.menu_uid = menu.uid
        configure.slot_position = menu.active_slot_position

    draw_space(workspace_shell, CATALOG_TOP_SPACING)
    catalog_box = workspace_shell.column()
    catalog_mode_row = catalog_box.row(align=True)
    catalog_mode_row.scale_y = CATALOG_MODE_HEIGHT
    catalog_mode_row.prop(prefs, "catalog_mode", text="")
    draw_space(catalog_box, SPACING_MEDIUM)

    browser_actions = None
    browser_columns = 2
    if prefs.catalog_mode == "POPULAR":
        popular_actions = tuple(
            _catalog_browser_action(action, effective_language())
            for action in ACTIONS
        )
        if not prefs.catalog_section:
            _draw_section_root(catalog_box, prefs, popular_actions)
        else:
            _draw_section_header(catalog_box, prefs, prefs.catalog_section)
            draw_space(catalog_box, SPACING_SMALL)
            _draw_grouped_actions(
                catalog_box,
                prefs,
                filter_broad_category(popular_actions, prefs.catalog_section),
            )
    elif prefs.catalog_mode == "ALL":
        browse_mode_row = catalog_box.row(align=True)
        browse_mode_row.prop(prefs, "catalog_browse_mode", expand=True)
        draw_subsection_divider(catalog_box)
        if prefs.catalog_browse_mode == "SEARCH":
            search_row = catalog_box.row(align=True)
            search_row.prop(prefs, "command_search", text="", icon="VIEWZOOM")
            search_row.prop(
                prefs,
                "show_technical_filters",
                text="",
                icon="FILTER",
                toggle=True,
            )
            if prefs.show_technical_filters:
                normalized_group = canonical_operator_group(prefs.operator_group)
                if normalized_group != prefs.operator_group:
                    prefs.operator_group = normalized_group
                source_row = catalog_box.row(align=True)
                source_row.label(text=t(prefs, "command_category"))
                source_row.operator(
                    "pie_customizer.select_operator_group",
                    text=(
                        t(prefs, "all_sources")
                        if normalized_group == "ALL"
                        else group_label(normalized_group, effective_language(context))
                    ),
                    icon=(
                        "FILTER"
                        if normalized_group == "ALL"
                        else runtime.safe_icon(group_icon(normalized_group))
                    ),
                )

            query = prefs.command_search.strip()
            if query:
                favorite_tokens = {
                    favorite.token for favorite in prefs.favorite_actions
                }
                recent_item_ids = {
                    action.item_id for action in recent_operator_actions(context)
                }
                browser_actions = filter_actions(
                    _searchable_browser_actions(prefs),
                    query,
                    prefs.operator_group if prefs.show_technical_filters else "ALL",
                    rank_matches=True,
                    context_mode=getattr(context, "mode", ""),
                    favorite_tokens=favorite_tokens,
                    recent_item_ids=recent_item_ids,
                    fuzzy_fallback=True,
                )
            else:
                _draw_search_home(catalog_box, prefs)
        else:
            searchable_actions = _searchable_browser_actions(prefs)
            if not prefs.catalog_section:
                _draw_section_root(catalog_box, prefs, searchable_actions)
            else:
                section_actions = filter_broad_category(searchable_actions, prefs.catalog_section)
                if not prefs.catalog_group:
                    _draw_section_header(catalog_box, prefs, prefs.catalog_section)
                    draw_space(catalog_box, SPACING_SMALL)
                    _draw_group_root(catalog_box, prefs, section_actions)
                else:
                    _draw_group_header(catalog_box, prefs, prefs.catalog_group)
                    draw_space(catalog_box, SPACING_SMALL)
                    catalog_box.prop(prefs, "command_search", text="", icon="VIEWZOOM")
                    browser_actions = filter_actions(
                        section_actions,
                        prefs.command_search,
                        prefs.catalog_group,
                        rank_matches=bool(prefs.command_search.strip()),
                    )
                    browser_columns = CATALOG_GRID_COLUMNS
    elif prefs.catalog_mode == "RECENT":
        catalog_box.prop(prefs, "command_search", text="", icon="VIEWZOOM")
        recent_actions = filter_actions(recent_operator_actions(context), prefs.command_search)
        draw_space(catalog_box, SPACING_SMALL)
        if not prefs.catalog_section:
            _draw_section_root(catalog_box, prefs, recent_actions)
        else:
            _draw_section_header(catalog_box, prefs, prefs.catalog_section)
            draw_space(catalog_box, SPACING_SMALL)
            _draw_grouped_actions(
                catalog_box,
                prefs,
                filter_broad_category(recent_actions, prefs.catalog_section),
            )
    elif prefs.catalog_mode == "FAVORITES":
        catalog_box.prop(prefs, "command_search", text="", icon="VIEWZOOM")
        favorite_actions = filter_actions(_favorite_browser_actions(prefs), prefs.command_search)
        draw_space(catalog_box, SPACING_SMALL)
        if not prefs.catalog_section:
            _draw_section_root(catalog_box, prefs, favorite_actions)
        else:
            _draw_section_header(catalog_box, prefs, prefs.catalog_section)
            draw_space(catalog_box, SPACING_SMALL)
            _draw_grouped_actions(
                catalog_box,
                prefs,
                filter_broad_category(favorite_actions, prefs.catalog_section),
            )
    elif prefs.catalog_mode == "NESTED":
        _draw_nested_menu_actions(catalog_box, prefs, menu)
    elif prefs.catalog_mode == "CUSTOM":
        _draw_custom_action_editor(catalog_box, prefs, slot)

    if browser_actions is not None:
        if browser_actions:
            draw_space(catalog_box, SPACING_SMALL)
            _draw_browser_actions(
                catalog_box,
                prefs,
                browser_actions,
                columns=browser_columns,
            )
        else:
            catalog_box.label(text=t(prefs, "catalog_empty"), icon="INFO")


def _draw_advanced_content(layout, prefs) -> None:
    io_row = layout.row(align=True)
    io_row.operator("pie_customizer.import_preset", text=t(prefs, "import"), icon="IMPORT")
    io_row.operator("pie_customizer.export_preset", text=t(prefs, "export"), icon="EXPORT")


class PC_UL_PieMenuList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type not in {"DEFAULT", "COMPACT"}:
            return
        menu_index = _menu_index_by_uid(data, item.menu_uid)
        if menu_index is None:
            layout.label(text="Missing menu", icon="ERROR")
            return
        menu = data.pie_menus[menu_index]
        row = layout.row(align=True)
        columns = row.split(factor=0.36, align=True)
        name_row = columns.row(align=True)
        action_columns = columns.split(factor=0.48, align=True)
        availability_row = action_columns.row(align=True)
        shortcut_row = action_columns.row(align=True)
        if item.depth > 0:
            tree_split = name_row.split(
                factor=min(0.06 + (item.depth - 1) * 0.07, 0.38),
                align=True,
            )
            tree_split.row(align=True)
            name_controls = tree_split.row(align=True)
        else:
            name_controls = name_row
        name_controls.prop(menu, "enabled", text="")
        name_controls.prop(menu, "name", text="", emboss=False)
        availability = availability_row.operator(
            "pie_customizer.configure_menu_availability",
            text=_menu_availability_text(data, menu),
            icon="FILTER",
        )
        availability.menu_uid = menu.uid
        shortcut = (
            shortcut_display(
                menu.key,
                menu.ctrl,
                menu.shift,
                menu.alt,
                menu.oskey,
                menu.event_value,
            )
            if menu.key
            else t(data, "no_key")
        )
        shortcut_row.operator_context = "INVOKE_DEFAULT"
        capture = shortcut_row.operator(
            "pie_customizer.configure_shortcut",
            text=shortcut,
            icon="KEY_HLT",
        )
        capture.menu_uid = menu.uid


class PC_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = runtime.ADDON_ID

    pie_menus: CollectionProperty(type=PC_PieMenu)  # type: ignore
    active_menu_index: IntProperty(default=0)  # type: ignore
    menu_hierarchy_entries: CollectionProperty(  # type: ignore
        type=PC_MenuHierarchyEntry,
        options={"HIDDEN", "SKIP_SAVE"},
    )
    active_hierarchy_index: IntProperty(  # type: ignore
        default=0,
        min=0,
        options={"HIDDEN", "SKIP_SAVE"},
        update=_active_hierarchy_entry_changed,
    )
    catalog_mode: EnumProperty(  # type: ignore
        name="Catalog",
        description="Action source for the pie menu",
        items=_catalog_mode_enum_items,
        default=0,
        update=_reset_catalog_navigation,
    )
    catalog_browse_mode: EnumProperty(  # type: ignore
        name="Command Browser",
        items=_catalog_browse_mode_enum_items,
        default=0,
        update=_reset_catalog_navigation,
    )
    catalog_section: StringProperty(default="")  # type: ignore
    catalog_group: StringProperty(default="")  # type: ignore
    show_technical_filters: BoolProperty(  # type: ignore
        name="Technical Filter",
        description="Filter commands by their internal bpy.ops module",
        default=False,
        update=_reset_catalog_page,
    )
    operator_group: EnumProperty(  # type: ignore
        name="Blender Section",
        items=_operator_group_enum_items,
        update=_reset_catalog_page,
    )
    command_search: StringProperty(  # type: ignore
        name="Search",
        description="Search by name, description, or operator id",
        default="",
        update=_reset_catalog_page,
    )
    catalog_page: IntProperty(default=0, min=0)  # type: ignore
    favorite_actions: CollectionProperty(type=PC_FavoriteAction)  # type: ignore

    def draw(self, context):
        layout = self.layout

        draw_space(layout, SPACING_SMALL)
        draw_section_header(layout, t(self, "menus_title"), "MENU_PANEL")
        menus_content = inset_layout(layout)
        draw_space(menus_content, SPACING_SMALL)
        _draw_menus_content(menus_content, self)
        draw_space(layout, SECTION_BOTTOM_SPACING)

        menu = _active_pie_menu(self)
        if menu is not None:
            draw_space(layout, SPACING_SECTION)
            draw_section_header(layout, t(self, "slots"), "MOUSE_LMB")
            slots_content = inset_layout(layout)
            draw_space(slots_content, SPACING_SMALL)
            _draw_slots_content(slots_content, self, context, menu)
            draw_space(layout, SECTION_BOTTOM_SPACING)

        draw_space(layout, SPACING_SECTION)
        draw_section_header(layout, t(self, "advanced"), "PREFERENCES")
        advanced_content = inset_layout(layout)
        draw_space(advanced_content, SPACING_SMALL)
        _draw_advanced_content(advanced_content, self)
        draw_space(layout, SECTION_BOTTOM_SPACING)


CLASSES = (
    PC_UL_PieMenuList,
    PC_AddonPreferences,
)
