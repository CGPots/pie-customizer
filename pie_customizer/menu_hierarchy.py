"""Pure helpers for presenting nested pie menus as a tree."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MenuHierarchyRow:
    index: int
    depth: int
    prefix: str
    parent_index: int | None
    has_children: bool
    reference_count: int
    occurrence_key: str


def build_menu_hierarchy(
    menus: Sequence[object],
    menu_ids: Sequence[str],
) -> tuple[MenuHierarchyRow, ...]:
    """Return a stable, cycle-safe visual tree without changing menu data."""

    count = len(menus)
    if len(menu_ids) != count:
        raise ValueError("menu_ids must match the number of menus")

    index_by_id = {
        menu_id: index
        for index, menu_id in enumerate(menu_ids)
        if menu_id
    }
    referenced_children: list[list[int]] = [[] for _ in range(count)]
    reference_count = [0] * count

    for parent_index, menu in enumerate(menus):
        child_indices = set()
        for slot in getattr(menu, "slots", ()):
            if not getattr(slot, "enabled", False):
                continue
            if getattr(slot, "slot_type", "") != "MENU":
                continue
            child_index = index_by_id.get(getattr(slot, "command", "").strip())
            if child_index is None or child_index == parent_index:
                continue
            child_indices.add(child_index)

        referenced_children[parent_index].extend(sorted(child_indices))
        for child_index in child_indices:
            reference_count[child_index] += 1

    roots = [index for index, incoming in enumerate(reference_count) if incoming == 0]
    rows: list[MenuHierarchyRow] = []
    covered_indices: set[int] = set()

    def append_rows(
        index: int,
        depth: int,
        parent_index: int | None,
        ancestor_path: tuple[int, ...],
    ) -> None:
        current_path = ancestor_path + (index,)
        covered_indices.add(index)

        children = [
            child_index
            for child_index in referenced_children[index]
            if child_index not in current_path
        ]
        rows.append(
            MenuHierarchyRow(
                index=index,
                depth=depth,
                prefix="",
                parent_index=parent_index,
                has_children=bool(children),
                reference_count=reference_count[index],
                occurrence_key="/".join(str(path_index) for path_index in current_path),
            )
        )
        for child_index in children:
            append_rows(
                child_index,
                depth + 1,
                index,
                current_path,
            )

    for root_index in roots:
        append_rows(
            root_index,
            0,
            None,
            (),
        )

    # Components made only of cyclic references have no natural root. Render
    # each such component once, while the path guard above prevents recursion.
    for index in range(count):
        if index not in covered_indices:
            append_rows(index, 0, None, ())

    return tuple(rows)


def hierarchy_new_order(
    rows: Sequence[MenuHierarchyRow],
    item_count: int,
) -> list[int]:
    """Map collection indices to their visual UIList indices."""

    if len(rows) != item_count:
        return []
    new_order = [0] * item_count
    for visual_index, row in enumerate(rows):
        new_order[row.index] = visual_index
    return new_order
