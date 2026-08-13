"""Persistent settings used by the add-on preferences."""

from __future__ import annotations

import json

import bpy
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from .availability import MODE_FILTER_ITEMS
from .localization import effective_language
from .shortcuts import EVENT_VALUE_ITEMS


SLOT_TYPE_ITEMS = {
    "RU": (
        ("SEPARATOR", "Разделитель", "Пустой слот pie menu", "NONE", 0),
        ("OPERATOR", "Оператор", "Запустить оператор Blender, например object.delete()", "NONE", 1),
        ("PROPERTY", "Свойство", "Переключить или установить свойство Blender", "NONE", 2),
        ("MENU", "Меню", "Открыть другое меню Blender по bl_idname", "NONE", 3),
    ),
    "EN": (
        ("SEPARATOR", "Separator", "Leave this pie position empty", "NONE", 0),
        ("OPERATOR", "Operator", "Run a Blender operator such as object.delete()", "NONE", 1),
        ("PROPERTY", "Property", "Toggle or set a Blender property", "NONE", 2),
        ("MENU", "Menu", "Open another Blender menu by bl_idname", "NONE", 3),
    ),
}

SLOT_POSITION_ITEMS = (
    ("0", "Left", ""),
    ("1", "Right", ""),
    ("2", "Bottom", ""),
    ("3", "Top", ""),
    ("4", "Top Left", ""),
    ("5", "Top Right", ""),
    ("6", "Bottom Left", ""),
    ("7", "Bottom Right", ""),
)

KEYMAP_CONTEXT_ITEMS = (
    ("VIEW_3D", "3D View", "3D Viewport window"),
    ("OBJECT_MODE", "Object Mode", "Object Mode shortcuts"),
    ("MESH", "Mesh Edit", "Mesh Edit Mode shortcuts"),
    ("WINDOW", "Window", "Global Blender window shortcuts"),
    ("IMAGE", "Image Editor", "Image Editor shortcuts"),
    ("NODE_EDITOR", "Node Editor", "Node Editor shortcuts"),
    ("CUSTOM", "Custom", "Set a custom keymap name, space type, and region type"),
)

OPERATOR_CONTEXT_ITEMS = (
    ("INVOKE_DEFAULT", "Invoke", "Open the operator interface when available"),
    ("EXEC_DEFAULT", "Execute", "Run the operator immediately"),
)

KEYMAP_CONTEXTS = {
    "VIEW_3D": ("3D View", "VIEW_3D", "WINDOW"),
    "OBJECT_MODE": ("Object Mode", "EMPTY", "WINDOW"),
    "MESH": ("Mesh", "EMPTY", "WINDOW"),
    "WINDOW": ("Window", "EMPTY", "WINDOW"),
    "IMAGE": ("Image", "IMAGE_EDITOR", "WINDOW"),
    "NODE_EDITOR": ("Node Editor", "NODE_EDITOR", "WINDOW"),
}

_ENUM_ITEM_CACHE = {}

BOOLEAN_PARAMETER_MODE_ITEMS = {
    "RU": (
        ("DEFAULT", "По умолчанию", "Не добавлять параметр в команду"),
        ("TRUE", "Включено", "Передать значение True"),
        ("FALSE", "Выключено", "Передать значение False"),
    ),
    "EN": (
        ("DEFAULT", "Default", "Do not include this parameter in the command"),
        ("TRUE", "Enabled", "Pass True"),
        ("FALSE", "Disabled", "Pass False"),
    ),
}


def _boolean_parameter_mode_items(self, context):
    language = "EN"
    try:
        addon = context.preferences.addons.get(__package__)
        if addon is not None:
            language = effective_language(context)
    except (AttributeError, KeyError):
        pass
    return BOOLEAN_PARAMETER_MODE_ITEMS.get(language, BOOLEAN_PARAMETER_MODE_ITEMS["RU"])


def _slot_type_items(self, context):
    language = "EN"
    try:
        addon = context.preferences.addons.get(__package__)
        if addon is not None:
            language = effective_language(context)
    except (AttributeError, KeyError):
        pass
    return SLOT_TYPE_ITEMS[language]


def _parameter_enum_items(self, context):
    blob = self.enum_items_json or "[]"
    if blob not in _ENUM_ITEM_CACHE:
        try:
            items = json.loads(blob)
            _ENUM_ITEM_CACHE[blob] = tuple((str(item[0]), str(item[1]), str(item[2])) for item in items)
        except Exception:
            _ENUM_ITEM_CACHE[blob] = (("NONE", "None", ""),)
    return _ENUM_ITEM_CACHE[blob]


class PC_OperatorParameter(bpy.types.PropertyGroup):
    identifier: StringProperty(default="")  # type: ignore
    label: StringProperty(default="")  # type: ignore
    description: StringProperty(default="")  # type: ignore
    value_type: StringProperty(default="STRING")  # type: ignore
    enabled: BoolProperty(name="Use", default=False)  # type: ignore
    bool_value: BoolProperty(default=False)  # type: ignore
    bool_mode: EnumProperty(items=_boolean_parameter_mode_items)  # type: ignore
    int_value: IntProperty(default=0)  # type: ignore
    float_value: FloatProperty(default=0.0)  # type: ignore
    string_value: StringProperty(default="")  # type: ignore
    enum_items_json: StringProperty(default="[]")  # type: ignore
    enum_value: EnumProperty(items=_parameter_enum_items)  # type: ignore


class PC_FavoriteAction(bpy.types.PropertyGroup):
    token: StringProperty(default="")  # type: ignore
    kind: StringProperty(default="OPERATOR")  # type: ignore
    item_id: StringProperty(default="")  # type: ignore
    group: StringProperty(default="")  # type: ignore
    label: StringProperty(default="")  # type: ignore
    description: StringProperty(default="")  # type: ignore
    command: StringProperty(default="")  # type: ignore
    icon: StringProperty(default="NONE")  # type: ignore
    slot_type: StringProperty(default="OPERATOR")  # type: ignore
    operator_context: StringProperty(default="INVOKE_DEFAULT")  # type: ignore


class PC_MenuHierarchyEntry(bpy.types.PropertyGroup):
    """Transient UI row pointing to a real menu, including shared aliases."""

    menu_uid: StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})  # type: ignore
    prefix: StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})  # type: ignore
    depth: IntProperty(default=0, min=0, options={"HIDDEN", "SKIP_SAVE"})  # type: ignore
    occurrence_key: StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})  # type: ignore


class PC_PieSlot(bpy.types.PropertyGroup):
    enabled: BoolProperty(name="Enabled", description="Show this slot in the pie menu", default=False)  # type: ignore
    label: StringProperty(name="Label", description="Button text in the pie menu", default="")  # type: ignore
    icon: StringProperty(name="Icon", description="Built-in Blender icon name, such as MESH_CUBE", default="NONE")  # type: ignore
    slot_type: EnumProperty(name="Type", description="Action type for this slot", items=_slot_type_items, default=0)  # type: ignore
    command: StringProperty(name="Command", description="Operator, property, or menu identifier", default="")  # type: ignore
    context_space_type: StringProperty(
        name="Editor Context",
        description="Editor required by a captured property action",
        default="",
        options={"HIDDEN"},
    )  # type: ignore
    operator_context: EnumProperty(  # type: ignore
        name="Run Mode",
        description="How to run the Blender operator",
        items=OPERATOR_CONTEXT_ITEMS,
        default="INVOKE_DEFAULT",
    )


class PC_PieMenu(bpy.types.PropertyGroup):
    uid: StringProperty(name="ID", default="")  # type: ignore
    enabled: BoolProperty(name="Enabled", description="Register this pie menu and its shortcut", default=True)  # type: ignore
    name: StringProperty(name="Name", description="Pie menu name", default="Custom Pie")  # type: ignore
    mode_filter_enabled: BoolProperty(  # type: ignore
        name="Limit by Mode",
        description="Show this pie menu only in the selected Blender modes",
        default=False,
    )
    allowed_modes: EnumProperty(  # type: ignore
        name="Available Modes",
        description="Blender modes where this pie menu is available",
        items=MODE_FILTER_ITEMS,
        options={"ENUM_FLAG"},
        default=set(),
    )
    keymap_context: EnumProperty(  # type: ignore
        name="Shortcut Context",
        description="Blender keymap where the shortcut will be created",
        items=KEYMAP_CONTEXT_ITEMS,
        default="VIEW_3D",
    )
    custom_keymap_name: StringProperty(name="Keymap Name", description="Keymap name for custom mode", default="3D View")  # type: ignore
    custom_space_type: StringProperty(name="Space Type", description="Space type for a custom keymap", default="VIEW_3D")  # type: ignore
    custom_region_type: StringProperty(name="Region Type", description="Region type for a custom keymap", default="WINDOW")  # type: ignore
    key: StringProperty(name="Key", description="Blender event type, such as Q, SPACE, or F5", default="")  # type: ignore
    event_value: EnumProperty(name="Event", description="Shortcut event type", items=EVENT_VALUE_ITEMS, default="PRESS")  # type: ignore
    ctrl: BoolProperty(name="Ctrl", default=False)  # type: ignore
    shift: BoolProperty(name="Shift", default=False)  # type: ignore
    alt: BoolProperty(name="Alt", default=False)  # type: ignore
    oskey: BoolProperty(name="Cmd/OS", default=False)  # type: ignore
    slots: CollectionProperty(type=PC_PieSlot)  # type: ignore
    active_slot_position: EnumProperty(  # type: ignore
        name="Position",
        description="Position of the slot inside the pie menu",
        items=SLOT_POSITION_ITEMS,
        default="0",
    )


CLASSES = (
    PC_OperatorParameter,
    PC_FavoriteAction,
    PC_MenuHierarchyEntry,
    PC_PieSlot,
    PC_PieMenu,
)
