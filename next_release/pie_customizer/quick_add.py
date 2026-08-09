"""Add Blender buttons to Pie Customizer from the button context menu."""

from __future__ import annotations

import json
import logging
import uuid

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

from . import command_catalog, runtime
from .action_parser import parse_operator_command, parse_property_command
from .discovery import format_operator_command, operator_identifier_to_id
from .localization import t
from .model import SLOT_POSITION_ITEMS
from .quick_add_data import (
    context_space_type,
    format_property_command,
    keymap_settings_for_space_type,
    normalize_rna_value,
    supported_property_owner_path,
)
from .shortcuts import shortcut_display
from .ui_style import PIE_DIRECTION_ARROWS, SPACING_LARGE, SPACING_MEDIUM, draw_space


LOGGER = logging.getLogger(__name__)
NEW_MENU_ID = "__NEW__"
_MENU_ITEMS_CACHE: list[tuple[str, str, str]] = []
_PROPERTY_ENUM_ITEMS_CACHE: dict[str, list[tuple[str, str, str]]] = {}
_QUICK_ADD_ICON_ITEMS = None
_CATALOG_ICON_BY_COMMAND = {
    action.command: action.icon for action in command_catalog.SEARCH_ACTIONS
}
_context_menu_registered = False
_view3d_context_menu_types = []

_VIEW3D_CONTEXT_MENU_NAMES = (
    "VIEW3D_MT_object_context_menu",
    "VIEW3D_MT_edit_mesh_context_menu",
    "VIEW3D_MT_edit_curve_context_menu",
    "VIEW3D_MT_edit_curves_context_menu",
    "VIEW3D_MT_edit_font_context_menu",
    "VIEW3D_MT_edit_lattice_context_menu",
    "VIEW3D_MT_edit_metaball_context_menu",
    "VIEW3D_MT_armature_context_menu",
    "VIEW3D_MT_pose_context_menu",
    "VIEW3D_MT_particle_context_menu",
    "VIEW3D_MT_gpencil_edit_context_menu",
    "VIEW3D_MT_greasepencil_edit_context_menu",
)

_DIRECTION_GRID = (
    ("4", "3", "5"),
    ("0", None, "1"),
    ("6", "2", "7"),
)
_TRANSFORM_ORIENTATION_PROPERTY_PATH = (
    "context.scene.transform_orientation_slots[0].type"
)
_SUPPORTED_ENUM_FLAG_PROPERTIES = {
    "snap_elements",
    "snap_elements_base",
    "snap_elements_individual",
}
_PIVOT_ENUM_LABELS = {
    "BOUNDING_BOX_CENTER": "Pivot: Bounding Box Center",
    "CURSOR": "Pivot: 3D Cursor",
    "INDIVIDUAL_ORIGINS": "Pivot: Individual Origins",
    "MEDIAN_POINT": "Pivot: Median Point",
    "ACTIVE_ELEMENT": "Pivot: Active Element",
}
_PIVOT_CONTEXT_PATHS = {
    "tool_settings.transform_pivot_point",
    "scene.tool_settings.transform_pivot_point",
}


def _quick_add_icon_items(_self, _context):
    global _QUICK_ADD_ICON_ITEMS
    if _QUICK_ADD_ICON_ITEMS is None:
        _QUICK_ADD_ICON_ITEMS = tuple(
            (
                icon_name,
                icon_name.replace("_", " ").title(),
                icon_name,
                icon_name if icon_name != "NONE" else "X",
                index,
            )
            for index, icon_name in enumerate(runtime.builtin_icon_names())
        )
    return _QUICK_ADD_ICON_ITEMS


def _enum_value_icon(serialized_items: str, identifier: str) -> str:
    try:
        items = json.loads(serialized_items or "[]")
    except (TypeError, ValueError):
        return "NONE"
    for item in items:
        if item.get("identifier") == identifier:
            return runtime.safe_icon(item.get("icon", "NONE"))
    return "NONE"


def _quick_add_property_value_updated(self, _context):
    previous = runtime.safe_icon(getattr(self, "suggested_icon", "NONE"))
    selected = runtime.safe_icon(getattr(self, "slot_icon", "NONE"))
    suggestion = _enum_value_icon(
        getattr(self, "source_property_items_json", ""),
        getattr(self, "property_enum_value", ""),
    )
    if suggestion == "NONE":
        return
    self.suggested_icon = suggestion
    if selected == previous:
        self.slot_icon = suggestion


def capture_button_operator(context):
    """Return safe operator metadata for the button under the cursor."""

    properties = getattr(context, "button_operator", None)
    if properties is None:
        return None

    pivot_action = _capture_pivot_context_operator(properties, context)
    if pivot_action is not None:
        return pivot_action

    rna = getattr(properties, "bl_rna", None)
    identifier = getattr(rna, "identifier", "")
    operator_id = operator_identifier_to_id(identifier)
    if "." not in operator_id or operator_id.startswith("pie_customizer."):
        return None

    kwargs = {}
    for descriptor in getattr(rna, "properties", ()):
        property_id = getattr(descriptor, "identifier", "")
        if not property_id or property_id == "rna_type":
            continue
        try:
            is_set = properties.is_property_set(property_id)
        except (AttributeError, TypeError, ValueError):
            return None
        if not is_set:
            continue
        try:
            kwargs[property_id] = normalize_rna_value(
                getattr(descriptor, "type", ""),
                bool(getattr(descriptor, "is_array", False)),
                getattr(properties, property_id),
            )
        except (AttributeError, TypeError, ValueError):
            # A partially captured command is less trustworthy than no menu entry.
            return None

    label = getattr(rna, "name", "") or operator_id
    return {
        "operator_id": operator_id,
        "label": label,
        "command": format_operator_command(operator_id, kwargs),
        "space_type": context_space_type(context),
    }


def capture_button_property(context):
    """Return safe property metadata for the button under the cursor."""

    owner = getattr(context, "button_pointer", None)
    descriptor = getattr(context, "button_prop", None)
    if owner is None or descriptor is None:
        return None

    property_id = getattr(descriptor, "identifier", "")
    property_type = getattr(descriptor, "type", "")
    is_array = bool(getattr(descriptor, "is_array", False))
    if (
        not property_id
        or property_id == "rna_type"
        or bool(getattr(descriptor, "is_readonly", False))
    ):
        return None

    owner_path = supported_property_owner_path(context, owner)
    if not owner_path:
        return None

    try:
        instance_readonly = owner.is_property_readonly(property_id)
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        instance_readonly = False
    if instance_readonly or is_array or property_type not in {"BOOLEAN", "INT", "FLOAT", "ENUM"}:
        return None

    try:
        value = normalize_rna_value(
            property_type,
            is_array,
            getattr(owner, property_id),
        )
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        return None

    enum_items = []
    is_enum_flag = False
    if property_type == "ENUM":
        is_enum_flag = bool(getattr(descriptor, "is_enum_flag", False))
        if is_enum_flag and property_id not in _SUPPORTED_ENUM_FLAG_PROPERTIES:
            return None
        try:
            items = descriptor.enum_items_static
        except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
            items = ()
        for item in items:
            identifier = getattr(item, "identifier", "")
            if not identifier:
                continue
            enum_items.append(
                {
                    "identifier": identifier,
                    "name": getattr(item, "name", "") or identifier,
                    "description": getattr(item, "description", "") or "",
                    "icon": runtime.safe_icon(getattr(item, "icon", "NONE")),
                }
            )
        if not enum_items:
            return None

    label = getattr(descriptor, "name", "") or property_id.replace("_", " ").title()
    return {
        "label": label,
        "path": f"{owner_path}.{property_id}",
        "property_type": property_type,
        "value_json": json.dumps(_json_compatible(value), ensure_ascii=True),
        "enum_items_json": json.dumps(enum_items, ensure_ascii=True),
        "is_enum_flag": is_enum_flag,
        "space_type": context_space_type(context),
    }


def draw_button_context_menu(self, context):
    operator = capture_button_operator(context)
    property_data = capture_button_property(context) if operator is None else None
    if operator is None and property_data is None:
        return

    self.layout.separator()
    add = self.layout.operator(
        "pie_customizer.quick_add_operator",
        text=t(runtime.get_preferences(context), "quick_add_menu_entry"),
        icon="MENU_PANEL",
    )
    if operator is not None:
        add.source_action_type = "OPERATOR"
        add.source_operator_id = operator["operator_id"]
        add.source_label = operator["label"]
        add.source_command = operator["command"]
        add.source_space_type = operator["space_type"]
        return

    add.source_action_type = "PROPERTY"
    add.source_label = property_data["label"]
    add.source_property_path = property_data["path"]
    add.source_property_type = property_data["property_type"]
    add.source_property_value_json = property_data["value_json"]
    add.source_property_items_json = property_data["enum_items_json"]
    add.source_property_is_enum_flag = property_data["is_enum_flag"]
    add.source_space_type = property_data["space_type"]


def draw_view3d_context_menu(self, context):
    self.layout.separator()
    self.layout.operator(
        "pie_customizer.open_preferences",
        text=t(runtime.get_preferences(context), "open_settings"),
        icon="PREFERENCES",
    )


def register_context_menu():
    global _context_menu_registered
    if _context_menu_registered:
        return
    bpy.types.UI_MT_button_context_menu.append(draw_button_context_menu)
    _view3d_context_menu_types.clear()
    for menu_name in _VIEW3D_CONTEXT_MENU_NAMES:
        menu_type = getattr(bpy.types, menu_name, None)
        if menu_type is None:
            continue
        menu_type.append(draw_view3d_context_menu)
        _view3d_context_menu_types.append(menu_type)
    _context_menu_registered = True


def unregister_context_menu():
    global _context_menu_registered
    if not _context_menu_registered:
        return
    try:
        bpy.types.UI_MT_button_context_menu.remove(draw_button_context_menu)
    except (AttributeError, RuntimeError, ValueError):
        pass
    for menu_type in reversed(_view3d_context_menu_types):
        try:
            menu_type.remove(draw_view3d_context_menu)
        except (AttributeError, RuntimeError, ValueError):
            pass
    _view3d_context_menu_types.clear()
    _context_menu_registered = False


def _menu_items(_self, context):
    prefs = runtime.get_preferences(context)
    _MENU_ITEMS_CACHE.clear()
    if prefs is not None:
        for menu in prefs.pie_menus:
            _MENU_ITEMS_CACHE.append((menu.uid, menu.name or t(prefs, "custom_pie"), ""))
    _MENU_ITEMS_CACHE.append((NEW_MENU_ID, t(prefs, "quick_add_new_menu"), ""))
    return _MENU_ITEMS_CACHE


def _property_enum_items(self, _context):
    cache_key = self.source_property_items_json
    cached = _PROPERTY_ENUM_ITEMS_CACHE.get(cache_key)
    if cached is not None:
        return cached

    items = []
    try:
        serialized_items = json.loads(cache_key or "[]")
    except (TypeError, ValueError):
        serialized_items = []
    for item in serialized_items:
        identifier = item.get("identifier", "")
        if identifier:
            items.append(
                (
                    identifier,
                    item.get("name") or identifier,
                    item.get("description") or "",
                )
            )
    if not items:
        items.append(("NONE", "Unavailable", "No enum values are available"))
    _PROPERTY_ENUM_ITEMS_CACHE[cache_key] = items
    return items


def _focus_addon_preferences() -> bool:
    window_manager = getattr(bpy.context, "window_manager", None)
    if window_manager is None:
        return False

    for window in window_manager.windows:
        for area in window.screen.areas:
            if area.type != "PREFERENCES":
                continue
            region = next(
                (candidate for candidate in area.regions if candidate.type == "WINDOW"),
                None,
            )
            if region is None:
                continue
            bpy.context.preferences.active_section = "ADDONS"
            try:
                with bpy.context.temp_override(window=window, area=area, region=region):
                    result = bpy.ops.preferences.addon_show(module=runtime.ADDON_ID)
            except (RuntimeError, TypeError):
                continue
            if "FINISHED" not in result:
                continue
            area.tag_redraw()
            return True
    return False


class PC_OT_OpenPreferences(bpy.types.Operator):
    bl_idname = "pie_customizer.open_preferences"
    bl_label = "Open Pie Customizer Settings"
    bl_description = "Open the Pie Customizer add-on preferences"

    def execute(self, context):
        context.preferences.active_section = "ADDONS"
        # Blender reuses and raises an existing Preferences window here.  Do not
        # short-circuit when it is already open, because it may be behind the
        # main window.
        result = bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        if not ({"FINISHED", "RUNNING_MODAL"} & set(result)):
            self.report({"ERROR"}, t(runtime.get_preferences(context), "open_settings_failed"))
            return {"CANCELLED"}

        attempts_remaining = 20

        def focus_when_ready():
            nonlocal attempts_remaining
            if _focus_addon_preferences():
                return None
            attempts_remaining -= 1
            return 0.1 if attempts_remaining > 0 else None

        bpy.app.timers.register(focus_when_ready, first_interval=0.1)
        return {"FINISHED"}


class PC_OT_QuickAddOperator(bpy.types.Operator):
    bl_idname = "pie_customizer.quick_add_operator"
    bl_label = "Add to Pie Customizer"
    bl_description = "Add this Blender action to a custom pie menu"

    source_action_type: EnumProperty(
        items=(
            ("OPERATOR", "Operator", ""),
            ("PROPERTY", "Property", ""),
        ),
        default="OPERATOR",
        options={"HIDDEN"},
    )  # type: ignore
    source_operator_id: StringProperty(options={"HIDDEN"})  # type: ignore
    source_label: StringProperty(options={"HIDDEN"})  # type: ignore
    source_command: StringProperty(options={"HIDDEN"})  # type: ignore
    source_property_path: StringProperty(options={"HIDDEN"})  # type: ignore
    source_property_type: StringProperty(options={"HIDDEN"})  # type: ignore
    source_property_value_json: StringProperty(options={"HIDDEN"})  # type: ignore
    source_property_items_json: StringProperty(options={"HIDDEN"})  # type: ignore
    source_property_is_enum_flag: BoolProperty(options={"HIDDEN"})  # type: ignore
    source_space_type: StringProperty(options={"HIDDEN"})  # type: ignore
    property_bool_mode: EnumProperty(
        name="Behavior",
        items=(
            ("TOGGLE", "Toggle", "Switch between enabled and disabled"),
            ("TRUE", "Enable", "Set the property to enabled"),
            ("FALSE", "Disable", "Set the property to disabled"),
        ),
        default="TOGGLE",
    )  # type: ignore
    property_enum_value: EnumProperty(
        name="Value",
        items=_property_enum_items,
        update=_quick_add_property_value_updated,
    )  # type: ignore
    menu_uid: EnumProperty(
        name="Pie Menu",
        items=_menu_items,
    )  # type: ignore
    new_menu_name: StringProperty(name="New Menu Name")  # type: ignore
    slot_position: EnumProperty(name="Direction", items=SLOT_POSITION_ITEMS, default="0")  # type: ignore
    replace_existing: BoolProperty(name="Replace Existing Action", default=False)  # type: ignore
    slot_icon: EnumProperty(
        name="Icon",
        description="Built-in Blender icon used by this pie button",
        items=_quick_add_icon_items,
    )  # type: ignore
    suggested_icon: StringProperty(default="NONE", options={"HIDDEN"})  # type: ignore
    shortcut_key: StringProperty(default="", options={"HIDDEN"})  # type: ignore
    shortcut_event_value: StringProperty(default="PRESS", options={"HIDDEN"})  # type: ignore
    shortcut_ctrl: BoolProperty(default=False, options={"HIDDEN"})  # type: ignore
    shortcut_shift: BoolProperty(default=False, options={"HIDDEN"})  # type: ignore
    shortcut_alt: BoolProperty(default=False, options={"HIDDEN"})  # type: ignore
    shortcut_oskey: BoolProperty(default=False, options={"HIDDEN"})  # type: ignore
    shortcut_edit_enabled: BoolProperty(default=False, options={"HIDDEN"})  # type: ignore

    def invoke(self, context, _event):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        if prefs.pie_menus:
            index = min(max(prefs.active_menu_index, 0), len(prefs.pie_menus) - 1)
            self.menu_uid = prefs.pie_menus[index].uid
        else:
            self.menu_uid = NEW_MENU_ID
        self.new_menu_name = f"{t(prefs, 'custom_pie')} {len(prefs.pie_menus) + 1}"
        self.shortcut_edit_enabled = False
        self._initialize_property_options()
        self._refresh_suggested_icon(force=True)
        return context.window_manager.invoke_props_dialog(self, width=520)

    def draw(self, context):
        prefs = runtime.get_preferences(context)
        layout = self.layout
        if self.source_action_type == "PROPERTY":
            layout.label(
                text=self.source_label or self.source_property_path,
                icon=runtime.safe_icon(self.slot_icon),
            )
            layout.label(text=self.source_property_path)
        else:
            layout.label(
                text=self.source_label or self.source_operator_id,
                icon=runtime.safe_icon(self.slot_icon),
            )
            layout.label(text=self.source_operator_id)
        layout.separator()
        layout.prop(self, "menu_uid")
        if self.menu_uid == NEW_MENU_ID:
            layout.prop(self, "new_menu_name")

        draw_space(layout, SPACING_MEDIUM)
        setting_row = layout.split(factor=0.24, align=True)
        if self.source_action_type == "PROPERTY":
            if self.source_property_type == "BOOLEAN":
                setting_row.label(text=f"{t(prefs, 'quick_add_behavior')}:")
            elif self.source_property_type == "ENUM":
                setting_row.label(text=f"{t(prefs, 'quick_add_value')}:")
            else:
                setting_row.label(text=f"{t(prefs, 'quick_add_current_value')}:")
        else:
            setting_row.label(text=f"{t(prefs, 'quick_add_icon')}:")

        value_and_icon = setting_row.split(factor=0.84, align=True)
        value_control = value_and_icon.row(align=True)
        if self.source_action_type == "PROPERTY":
            if self.source_property_type == "BOOLEAN":
                value_control.prop(
                    self,
                    "property_bool_mode",
                    text="",
                )
            elif self.source_property_type == "ENUM":
                value_control.prop(
                    self,
                    "property_enum_value",
                    text="",
                )
            else:
                value_control.label(
                    text=self._property_value_display(),
                    icon="INFO",
                )
        else:
            value_control.label(text="")

        icon_picker = value_and_icon.row(align=True)
        icon_picker.template_icon_view(
            self,
            "slot_icon",
            show_labels=False,
            scale=1.0,
            scale_popup=5.0,
        )

        target = _menu_by_uid(prefs, self.menu_uid)
        current_shortcut = (
            shortcut_display(
                target.key,
                target.ctrl,
                target.shift,
                target.alt,
                target.oskey,
                target.event_value,
            )
            if target is not None and target.key
            else t(prefs, "no_key")
        )
        draw_space(layout, SPACING_MEDIUM)
        shortcut_row = layout.split(factor=0.24)
        shortcut_row.label(text=f"{t(prefs, 'quick_add_shortcut')}:")
        shortcut_row.label(
            text=(
                current_shortcut
                if target is not None and target.key
                else t(prefs, "quick_add_capture_after_hint")
            ),
            icon="KEY_HLT",
        )

        draw_space(layout, SPACING_MEDIUM)
        layout.label(text=t(prefs, "quick_add_direction"))
        for position_row in _DIRECTION_GRID:
            position_grid = layout.grid_flow(
                row_major=True,
                columns=3,
                even_columns=True,
                even_rows=True,
                align=False,
            )
            for position in position_row:
                cell = position_grid.row(align=True)
                if position is None:
                    cell.alignment = "CENTER"
                    cell.label(text=PIE_DIRECTION_ARROWS[self.slot_position])
                    continue
                button_text, button_icon = _direction_button_content(prefs, target, position)
                cell.prop_enum(
                    self,
                    "slot_position",
                    position,
                    text=button_text,
                    icon=button_icon,
                )

        slot = _slot_for(target, self.slot_position)
        if _slot_is_assigned(slot):
            layout.label(
                text=f"{t(prefs, 'quick_add_occupied')}: {slot.label}",
                icon="ERROR",
            )
            layout.prop(self, "replace_existing")
        draw_space(layout, SPACING_LARGE)

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        try:
            normalized_command, action_label = self._normalized_action()
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        slot_type = self._normalized_slot_type()
        operator_context = (
            "EXEC_DEFAULT"
            if self.source_property_path == _TRANSFORM_ORIENTATION_PROPERTY_PATH
            else "INVOKE_DEFAULT"
        )
        previous_active_index = prefs.active_menu_index
        created_index = None
        previous_shortcut = None
        menu = _menu_by_uid(prefs, self.menu_uid)
        if self.menu_uid == NEW_MENU_ID:
            menu = prefs.pie_menus.add()
            menu.uid = uuid.uuid4().hex
            menu.name = self.new_menu_name.strip() or t(prefs, "custom_pie")
            runtime.initialize_empty_menu(menu)
            _configure_menu_keymap(menu, self.source_space_type)
            created_index = len(prefs.pie_menus) - 1
            prefs.active_menu_index = created_index
        elif menu is None:
            self.report({"ERROR"}, t(prefs, "pie_not_found"))
            return {"CANCELLED"}
        else:
            prefs.active_menu_index = _menu_index(prefs, menu.uid)
            previous_shortcut = _snapshot_menu_shortcut(menu)

        runtime.ensure_menu_shape(menu)
        slot = menu.slots[int(self.slot_position)]
        if _slot_is_assigned(slot) and not self.replace_existing:
            if created_index is not None:
                prefs.pie_menus.remove(created_index)
            prefs.active_menu_index = previous_active_index
            self.report({"WARNING"}, t(prefs, "quick_add_replace_required"))
            return {"CANCELLED"}

        previous_slot = _snapshot_slot(slot)
        if created_index is not None or self.shortcut_edit_enabled:
            _assign_menu_shortcut(self, menu)
        capture_missing_shortcut = not bool(menu.key)
        runtime.assign_slot_action(
            slot,
            label=action_label,
            icon=runtime.safe_icon(self.slot_icon),
            slot_type=slot_type,
            command=normalized_command,
            operator_context=operator_context,
            context_space_type=(
                self.source_space_type if slot_type == "PROPERTY" else ""
            ),
        )
        menu.active_slot_position = self.slot_position

        errors = runtime.rebuild_dynamic_menus(context)
        if errors:
            if created_index is not None:
                prefs.pie_menus.remove(created_index)
            else:
                _restore_slot(slot, previous_slot)
                _restore_menu_shortcut(menu, previous_shortcut)
            prefs.active_menu_index = previous_active_index
            runtime.rebuild_dynamic_menus(context)
            self.report({"ERROR"}, errors[0])
            return {"CANCELLED"}

        self.report({"INFO"}, t(prefs, "quick_add_done"))
        if capture_missing_shortcut:
            capture_result = bpy.ops.pie_customizer.capture_shortcut(
                "INVOKE_DEFAULT",
                menu_uid=menu.uid,
            )
            if not ({"FINISHED", "RUNNING_MODAL"} & set(capture_result)):
                self.report({"WARNING"}, t(prefs, "capture_shortcut_background"))
        return {"FINISHED"}

    def _initialize_property_options(self):
        if self.source_action_type != "PROPERTY" or self.source_property_type != "ENUM":
            return
        identifiers = [item[0] for item in _property_enum_items(self, None)]
        current = self._property_value()
        if isinstance(current, str) and current in identifiers:
            self.property_enum_value = current
        elif identifiers:
            self.property_enum_value = identifiers[0]

    def _suggested_icon(self):
        if self.source_action_type == "PROPERTY" and self.source_property_type == "ENUM":
            enum_icon = _enum_value_icon(
                self.source_property_items_json,
                self.property_enum_value,
            )
            if enum_icon != "NONE":
                return enum_icon

        try:
            command, _label = self._normalized_action()
        except ValueError:
            command = ""
        catalog_icon = runtime.safe_icon(_CATALOG_ICON_BY_COMMAND.get(command, "NONE"))
        if catalog_icon != "NONE":
            return catalog_icon
        return runtime.safe_icon("RNA" if self.source_action_type == "PROPERTY" else "PLAY")

    def _refresh_suggested_icon(self, force=False):
        previous = runtime.safe_icon(self.suggested_icon)
        selected = runtime.safe_icon(self.slot_icon)
        suggestion = self._suggested_icon()
        self.suggested_icon = suggestion
        if force or selected == previous:
            self.slot_icon = suggestion

    def _normalized_action(self):
        if self.source_action_type == "OPERATOR":
            if not self.source_command or not self.source_operator_id:
                raise ValueError("Missing captured operator metadata")
            command = runtime.normalize_operator_command(self.source_command)
            if parse_operator_command(command).operator_id != self.source_operator_id:
                raise ValueError("Captured operator metadata does not match")
            return command, self.source_label or self.source_operator_id

        if self.source_action_type != "PROPERTY" or not self.source_property_path:
            raise ValueError("Missing captured property metadata")
        value = ...
        label = self.source_label or self.source_property_path
        if self.source_property_type == "BOOLEAN":
            if self.property_bool_mode == "TRUE":
                value = True
            elif self.property_bool_mode == "FALSE":
                value = False
        elif self.source_property_type == "ENUM":
            selected = self.property_enum_value
            value = {selected} if self.source_property_is_enum_flag else selected
            label = self._enum_action_label(selected)
        else:
            value = self._property_value()
            label = f"{label}: {self._property_value_display()}"

        if self.source_property_path == _TRANSFORM_ORIENTATION_PROPERTY_PATH:
            command = format_operator_command(
                "transform.select_orientation",
                {"orientation": value},
            )
            parse_operator_command(command)
            return command, label

        command = format_property_command(self.source_property_path, value)
        parse_property_command(command)
        return command, label

    def _normalized_slot_type(self):
        if self.source_property_path == _TRANSFORM_ORIENTATION_PROPERTY_PATH:
            return "OPERATOR"
        return self.source_action_type

    def _property_value(self):
        try:
            return json.loads(self.source_property_value_json)
        except (TypeError, ValueError):
            return None

    def _property_value_display(self):
        value = self._property_value()
        if isinstance(value, list):
            return ", ".join(str(item) for item in value)
        return str(value)

    def _enum_action_label(self, identifier):
        for item_identifier, name, _description in _property_enum_items(self, None):
            if item_identifier == identifier:
                return f"{self.source_label}: {name}" if self.source_label else name
        return self.source_label or identifier


def _menu_by_uid(prefs, uid):
    if prefs is None or not uid or uid == NEW_MENU_ID:
        return None
    for menu in prefs.pie_menus:
        if menu.uid == uid:
            return menu
    return None


def _menu_index(prefs, uid):
    for index, menu in enumerate(prefs.pie_menus):
        if menu.uid == uid:
            return index
    return 0


def _slot_for(menu, position):
    if menu is None:
        return None
    runtime.ensure_menu_shape(menu)
    return menu.slots[int(position)]


def _position_is_occupied(menu, position):
    return _slot_is_assigned(_slot_for(menu, position))


def _direction_button_content(prefs, menu, position):
    slot = _slot_for(menu, position)
    if not _slot_is_assigned(slot):
        return t(prefs, "empty_slot"), "NONE"
    return slot.label or t(prefs, "empty_slot"), runtime.safe_icon(slot.icon)


def _slot_is_assigned(slot):
    return bool(
        slot is not None
        and slot.slot_type != "SEPARATOR"
        and slot.command.strip()
    )


def _snapshot_slot(slot):
    return {
        "enabled": slot.enabled,
        "label": slot.label,
        "icon": slot.icon,
        "slot_type": slot.slot_type,
        "command": slot.command,
        "operator_context": slot.operator_context,
        "context_space_type": slot.context_space_type,
    }


def _snapshot_menu_shortcut(menu):
    return {
        "key": menu.key,
        "event_value": menu.event_value,
        "ctrl": menu.ctrl,
        "shift": menu.shift,
        "alt": menu.alt,
        "oskey": menu.oskey,
    }


def _restore_menu_shortcut(menu, data):
    if menu is None or not data:
        return
    for key, value in data.items():
        setattr(menu, key, value)


def _assign_menu_shortcut(operator, menu):
    menu.key = operator.shortcut_key
    menu.event_value = operator.shortcut_event_value or "PRESS"
    menu.ctrl = operator.shortcut_ctrl
    menu.shift = operator.shortcut_shift
    menu.alt = operator.shortcut_alt
    menu.oskey = operator.shortcut_oskey


def _restore_slot(slot, data):
    for key, value in data.items():
        setattr(slot, key, value)


def _json_compatible(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def _capture_pivot_context_operator(properties, context):
    try:
        data_path = properties.data_path
        value = properties.value
    except (AttributeError, ReferenceError, RuntimeError, TypeError, ValueError):
        return None
    if data_path not in _PIVOT_CONTEXT_PATHS or value not in _PIVOT_ENUM_LABELS:
        return None
    return {
        "operator_id": "wm.context_set_enum",
        "label": _PIVOT_ENUM_LABELS[value],
        "command": format_operator_command(
            "wm.context_set_enum",
            {
                "data_path": "scene.tool_settings.transform_pivot_point",
                "value": value,
            },
        ),
        "space_type": context_space_type(context),
    }


def _configure_menu_keymap(menu, space_type):
    settings = keymap_settings_for_space_type(space_type)
    if settings is None:
        return
    keymap_context, keymap_name, custom_space_type, region_type = settings
    menu.keymap_context = keymap_context
    menu.custom_keymap_name = keymap_name
    menu.custom_space_type = custom_space_type
    menu.custom_region_type = region_type


CLASSES = (PC_OT_OpenPreferences, PC_OT_QuickAddOperator)
