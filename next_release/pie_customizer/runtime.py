"""Dynamic pie menu and keymap registration."""

from __future__ import annotations

import logging
import uuid
from typing import Iterable

import bpy

from .action_parser import parse_operator_command, parse_property_command
from .localization import t
from .model import KEYMAP_CONTEXTS
from .preset import normalize_preset_items
from .shortcuts import normalize_key_event


ADDON_ID = __package__ or "pie_customizer"
_dynamic_menu_classes: list[type[bpy.types.Menu]] = []
_dynamic_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []
_builtin_icon_names: set[str] | None = None
LOGGER = logging.getLogger(__name__)

_LEGACY_PROPERTY_PATHS = {
    "context.scene.tool_settings.sculpt.use_symmetry_x": (
        "context.object.data.use_mirror_x"
    ),
}

_OPERATOR_ENUM_ALIASES = {
    ("object.convert", "target"): {
        "GPENCIL": "GREASEPENCIL",
        "GREASEPENCIL": "GPENCIL",
    },
}


def get_preferences(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(ADDON_ID)
    if addon is None:
        return None
    return addon.preferences


def ensure_initial_preferences():
    prefs = get_preferences()
    if prefs is None:
        return
    for menu in prefs.pie_menus:
        ensure_menu_shape(menu)


def ensure_menu_shape(menu_config):
    _ensure_menu_uid(menu_config)
    _ensure_slots(menu_config)


def initialize_empty_menu(menu_config):
    ensure_menu_shape(menu_config)
    menu_config.active_slot_position = "0"
    for slot in menu_config.slots:
        clear_slot(slot)


def clear_slot(slot):
    slot.enabled = False
    slot.label = ""
    slot.icon = "NONE"
    slot.slot_type = "SEPARATOR"
    slot.command = ""
    slot.operator_context = "INVOKE_DEFAULT"


def rebuild_dynamic_menus(context=None):
    unregister_dynamic_menus()
    prefs = get_preferences(context)
    if prefs is None:
        return []

    wm = bpy.context.window_manager
    keyconfig = wm.keyconfigs.addon
    errors = []

    for menu_config in prefs.pie_menus:
        ensure_menu_shape(menu_config)
        if not menu_config.enabled:
            continue

        menu_id = menu_id_for(menu_config)
        list_menu_id = list_menu_id_for(menu_config)
        menu_cls = type(
            menu_id,
            (bpy.types.Menu,),
            {
                "bl_idname": menu_id,
                "bl_label": menu_config.name or t(prefs, "custom_pie"),
                "draw": _make_menu_draw(menu_config.uid),
            },
        )
        list_menu_cls = type(
            list_menu_id,
            (bpy.types.Menu,),
            {
                "bl_idname": list_menu_id,
                "bl_label": menu_config.name or t(prefs, "custom_pie"),
                "draw": _make_menu_list_draw(menu_config.uid),
            },
        )

        registered_classes = []
        try:
            for menu_class in (menu_cls, list_menu_cls):
                bpy.utils.register_class(menu_class)
                registered_classes.append(menu_class)
        except Exception as exc:
            LOGGER.exception("Failed to register dynamic menu %s", menu_id)
            for menu_class in reversed(registered_classes):
                try:
                    bpy.utils.unregister_class(menu_class)
                except Exception:
                    pass
            continue

        _dynamic_menu_classes.extend(registered_classes)
        if keyconfig and menu_config.key.strip():
            error = _register_keymap(keyconfig, menu_config, menu_id)
            if error:
                errors.append(error)

    return errors


def unregister_dynamic_menus():
    for keymap, keymap_item in _dynamic_keymaps:
        try:
            keymap.keymap_items.remove(keymap_item)
        except Exception:
            pass
    _dynamic_keymaps.clear()

    for menu_cls in reversed(_dynamic_menu_classes):
        try:
            bpy.utils.unregister_class(menu_cls)
        except Exception:
            pass
    _dynamic_menu_classes.clear()


def menu_id_for(menu_config) -> str:
    return _menu_id_for_uid(menu_config.uid or _new_uid())


def list_menu_id_for(menu_config) -> str:
    return _list_menu_id_for_uid(menu_config.uid or _new_uid())


def _menu_id_for_uid(uid: str) -> str:
    return f"PC_MT_custom_pie_{_safe_uid_fragment(uid)}"


def _list_menu_id_for_uid(uid: str) -> str:
    return f"PC_MT_custom_list_{_safe_uid_fragment(uid)}"


def _safe_uid_fragment(uid: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in uid)


def menu_config_for_id(prefs, menu_id: str):
    if prefs is None or not menu_id:
        return None
    for menu_config in prefs.pie_menus:
        if menu_id_for(menu_config) == menu_id:
            return menu_config
    return None


def keymap_tuple(menu_config):
    if menu_config.keymap_context == "CUSTOM":
        return (
            menu_config.custom_keymap_name or "3D View",
            menu_config.custom_space_type or "EMPTY",
            menu_config.custom_region_type or "WINDOW",
        )
    return KEYMAP_CONTEXTS.get(menu_config.keymap_context, KEYMAP_CONTEXTS["VIEW_3D"])


def run_operator_command(command: str, operator_context: str):
    prefs = get_preferences()
    parsed = parse_operator_command(normalize_operator_command(command))
    if (
        parsed.operator_id == "object.set_proportional_falloff"
        and not parsed.kwargs.get("falloff_shape")
    ):
        raise ValueError(t(prefs, "proportional_falloff_wrapper"))
    if (
        parsed.operator_id == "object.origin_set_any_mode"
        and not parsed.kwargs.get("type")
    ):
        raise ValueError(t(prefs, "origin_set_wrapper"))
    module_name, operator_name = parsed.operator_id.split(".", 1)
    module = getattr(bpy.ops, module_name, None)
    if module is None:
        raise ValueError(f"{t(prefs, 'unknown_operator_module')}: {module_name}")
    operator = getattr(module, operator_name, None)
    if operator is None:
        raise ValueError(f"{t(prefs, 'unknown_operator')}: {parsed.operator_id}")
    return operator(operator_context, **parsed.kwargs)


def normalize_operator_command(command: str) -> str:
    """Validate an operator command against this Blender and migrate known aliases."""

    parsed = parse_operator_command(command)
    module_name, operator_name = parsed.operator_id.split(".", 1)
    module = getattr(bpy.ops, module_name, None)
    operator = getattr(module, operator_name, None) if module is not None else None
    if operator is None:
        raise ValueError(
            f"Operator {parsed.operator_id!r} is unavailable in Blender "
            f"{bpy.app.version_string}"
        )

    try:
        properties = operator.get_rna_type().properties
    except Exception:
        # Some context-sensitive operators expose RNA only in their editor.
        return command

    kwargs = dict(parsed.kwargs)
    for name, value in tuple(kwargs.items()):
        prop = properties.get(name)
        if prop is None:
            raise ValueError(
                f"Operator {parsed.operator_id!r} has no parameter {name!r} "
                f"in Blender {bpy.app.version_string}"
            )

        type_error = _operator_value_error(prop, value)
        if type_error:
            raise ValueError(
                f"Invalid value for {parsed.operator_id}.{name} in Blender "
                f"{bpy.app.version_string}: {type_error}"
            )

        if prop.type == "ENUM":
            identifiers = _enum_identifiers(prop)
            if getattr(prop, "is_enum_flag", False):
                unknown = set(value) - identifiers
                if identifiers and unknown:
                    raise ValueError(
                        f"Unsupported values {sorted(unknown)!r} for "
                        f"{parsed.operator_id}.{name} in Blender {bpy.app.version_string}"
                    )
                continue

            if identifiers and (
                not isinstance(value, str) or value not in identifiers
            ):
                alias = _OPERATOR_ENUM_ALIASES.get((parsed.operator_id, name), {}).get(value)
                if alias in identifiers:
                    kwargs[name] = alias
                    continue
                raise ValueError(
                    f"Unsupported value {value!r} for {parsed.operator_id}.{name} "
                    f"in Blender {bpy.app.version_string}"
                )

    return _format_operator_command(parsed.operator_id, kwargs)


def _operator_value_error(prop, value) -> str:
    if getattr(prop, "is_array", False):
        return ""
    if prop.type == "BOOLEAN" and not isinstance(value, bool):
        return "expected a boolean"
    if prop.type == "INT" and (
        not isinstance(value, int) or isinstance(value, bool)
    ):
        return "expected an integer"
    if prop.type == "FLOAT" and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        return "expected a number"
    if prop.type == "STRING" and not isinstance(value, str):
        return "expected a string"
    if prop.type == "ENUM":
        if getattr(prop, "is_enum_flag", False):
            if not isinstance(value, (set, tuple, list)):
                return "expected an enum flag collection"
        elif not isinstance(value, str):
            return "expected an enum identifier"
    return ""


def _enum_identifiers(prop) -> set[str]:
    try:
        return {item.identifier for item in prop.enum_items_static if item.identifier}
    except (AttributeError, RuntimeError, TypeError):
        return set()


def _format_operator_command(operator_id: str, kwargs: dict) -> str:
    arguments = ", ".join(
        f"{name}={_format_literal(value)}" for name, value in kwargs.items()
    )
    return f"{operator_id}({arguments})"


def _format_literal(value) -> str:
    if isinstance(value, set):
        if not value:
            return "set()"
        return "{" + ", ".join(sorted(repr(item) for item in value)) + "}"
    return repr(value)


def run_property_command(command: str, context):
    prefs = get_preferences(context)
    parsed = parse_property_command(command)
    path = _LEGACY_PROPERTY_PATHS.get(parsed.path, parsed.path)
    owner, attribute = _resolve_property_owner(path, context)
    if parsed.has_value:
        setattr(owner, attribute, parsed.value)
        return {"FINISHED"}

    current = getattr(owner, attribute)
    if not isinstance(current, bool):
        raise ValueError(t(prefs, "bool_property_required"))
    setattr(owner, attribute, not current)
    return {"FINISHED"}


def serialize_menus(prefs) -> list[dict]:
    data = []
    for menu in prefs.pie_menus:
        data.append(
            {
                "uid": menu.uid,
                "enabled": menu.enabled,
                "name": menu.name,
                "keymap_context": menu.keymap_context,
                "custom_keymap_name": menu.custom_keymap_name,
                "custom_space_type": menu.custom_space_type,
                "custom_region_type": menu.custom_region_type,
                "key": menu.key,
                "event_value": menu.event_value,
                "ctrl": menu.ctrl,
                "shift": menu.shift,
                "alt": menu.alt,
                "oskey": menu.oskey,
                "slots": [
                    {
                        "enabled": slot.enabled,
                        "label": slot.label,
                        "icon": slot.icon,
                        "slot_type": slot.slot_type,
                        "command": slot.command,
                        "operator_context": slot.operator_context,
                    }
                    for slot in menu.slots
                ],
            }
        )
    return data


def load_menus(prefs, items: Iterable[dict], replace: bool):
    normalized = normalize_preset_items(list(items))
    normalized = _normalize_imported_commands(normalized)
    normalized = _prepare_import_uids(prefs, normalized, replace)

    if replace:
        prefs.pie_menus.clear()

    for item in normalized:
        menu = prefs.pie_menus.add()
        menu.uid = item.get("uid") or _new_uid()
        menu.enabled = bool(item.get("enabled", True))
        menu.name = item.get("name", t(prefs, "custom_pie"))
        menu.keymap_context = item.get("keymap_context", "VIEW_3D")
        menu.custom_keymap_name = item.get("custom_keymap_name", "3D View")
        menu.custom_space_type = item.get("custom_space_type", "VIEW_3D")
        menu.custom_region_type = item.get("custom_region_type", "WINDOW")
        menu.key = item.get("key", "")
        menu.event_value = item.get("event_value", "PRESS")
        menu.ctrl = bool(item.get("ctrl", False))
        menu.shift = bool(item.get("shift", False))
        menu.alt = bool(item.get("alt", False))
        menu.oskey = bool(item.get("oskey", False))
        _ensure_slots(menu)

        for index, slot_data in enumerate(item.get("slots", [])[:8]):
            slot = menu.slots[index]
            slot.enabled = bool(slot_data.get("enabled", True))
            slot.label = slot_data.get("label", "Action")
            slot.icon = slot_data.get("icon", "NONE")
            slot.slot_type = slot_data.get("slot_type", "SEPARATOR")
            slot.command = slot_data.get("command", "")
            slot.operator_context = slot_data.get("operator_context", "INVOKE_DEFAULT")


def _normalize_imported_commands(items: list[dict]) -> list[dict]:
    normalized = []
    for item in items:
        slots = []
        for slot in item["slots"]:
            command = slot["command"]
            if slot["slot_type"] == "OPERATOR" and command:
                command = normalize_operator_command(command)
            slots.append({**slot, "command": command})
        normalized.append({**item, "slots": slots})
    return normalized


def _prepare_import_uids(prefs, items: list[dict], replace: bool) -> list[dict]:
    reserved_ids = set()
    if not replace:
        reserved_ids = {_menu_id_for_uid(menu.uid) for menu in prefs.pie_menus if menu.uid}

    uid_map = {}
    prepared = []
    for item in items:
        source_uid = item["uid"]
        target_uid = source_uid or _new_uid()
        while _menu_id_for_uid(target_uid) in reserved_ids:
            target_uid = _new_uid()
        reserved_ids.add(_menu_id_for_uid(target_uid))
        if source_uid and source_uid not in uid_map:
            uid_map[source_uid] = target_uid
        prepared.append({**item, "uid": target_uid})

    nested_ids = {
        _menu_id_for_uid(source_uid): _menu_id_for_uid(target_uid)
        for source_uid, target_uid in uid_map.items()
        if source_uid != target_uid
    }
    if nested_ids:
        for item in prepared:
            item["slots"] = [
                {
                    **slot,
                    "command": nested_ids.get(slot["command"], slot["command"]),
                }
                for slot in item["slots"]
            ]
    return prepared


def _register_keymap(keyconfig, menu_config, menu_id: str):
    prefs = get_preferences()
    key_type = normalize_key_event(menu_config.key)
    if not key_type:
        return f"{menu_config.name}: {t(prefs, 'invalid_key')}"

    keymap_name, space_type, region_type = keymap_tuple(menu_config)
    keymap = keyconfig.keymaps.get(keymap_name)
    if keymap is None:
        keymap = keyconfig.keymaps.new(
            name=keymap_name,
            space_type=space_type,
            region_type=region_type,
        )

    try:
        keymap_item = keymap.keymap_items.new(
            "wm.call_menu_pie",
            key_type,
            menu_config.event_value,
            ctrl=menu_config.ctrl,
            shift=menu_config.shift,
            alt=menu_config.alt,
            oskey=menu_config.oskey,
        )
        keymap_item.properties.name = menu_id
        keymap_item.active = True
        _dynamic_keymaps.append((keymap, keymap_item))
    except Exception as exc:
        message = f"{menu_config.name}: {t(prefs, 'keymap_failed')}: {exc}"
        LOGGER.exception("Failed to register shortcut for %s", menu_id)
        return message

    return None


def _make_menu_draw(menu_uid: str):
    def draw(self, context):
        prefs = get_preferences(context)
        menu_config = _find_menu_by_uid(prefs, menu_uid) if prefs else None
        pie = self.layout.menu_pie()
        if menu_config is None:
            pie.label(text=t(prefs, "pie_not_found"), icon="ERROR")
            return

        _ensure_slots(menu_config)
        for slot in menu_config.slots[:8]:
            _draw_slot(pie, slot, context)

    return draw


def _make_menu_list_draw(menu_uid: str):
    def draw(self, context):
        prefs = get_preferences(context)
        menu_config = _find_menu_by_uid(prefs, menu_uid) if prefs else None
        if menu_config is None:
            self.layout.label(text=t(prefs, "pie_not_found"), icon="ERROR")
            return
        draw_menu_as_list(self.layout, menu_config, context)

    return draw


def _draw_slot(layout, slot, context):
    if not slot.enabled or slot.slot_type == "SEPARATOR":
        layout.separator()
        return

    icon = safe_icon(slot.icon)
    prefs = get_preferences(context)
    label = slot.label or slot.command or t(prefs, "label")

    if slot.slot_type == "OPERATOR":
        try:
            parsed = parse_operator_command(slot.command)
            if parsed.kwargs:
                raise ValueError(t(prefs, "operator_arguments_runner"))
            layout.operator_context = slot.operator_context
            layout.operator(parsed.operator_id, text=label, icon=icon)
            return
        except Exception:
            operator = layout.operator("pie_customizer.run_action", text=label, icon=icon)
            operator.action_type = "OPERATOR"
            operator.command = slot.command
            operator.operator_context = slot.operator_context
            return

    if slot.slot_type == "MENU":
        menu_id = slot.command.strip()
        nested_menu = menu_config_for_id(prefs, menu_id)
        nested_list_id = list_menu_id_for(nested_menu) if nested_menu is not None else ""
        if nested_menu is not None and nested_menu.enabled and hasattr(bpy.types, nested_list_id):
            layout.menu(nested_list_id, text=label, icon=icon)
        elif menu_id and hasattr(bpy.types, menu_id):
            layout.menu(menu_id, text=label, icon=icon)
        else:
            layout.label(text=label, icon="ERROR")
        return

    operator = layout.operator("pie_customizer.run_action", text=label, icon=icon)
    operator.action_type = slot.slot_type
    operator.command = slot.command
    operator.operator_context = slot.operator_context


def draw_menu_as_list(layout, menu_config, context):
    prefs = get_preferences(context)
    _ensure_slots(menu_config)
    visible_slots = tuple(
        slot
        for slot in menu_config.slots[:8]
        if slot.enabled and slot.slot_type != "SEPARATOR"
    )
    if not visible_slots:
        layout.label(text=t(prefs, "nested_menu_no_actions"), icon="INFO")
        return

    column = layout.column(align=True)
    for slot in visible_slots:
        _draw_slot(column, slot, context)


def _resolve_property_owner(path: str, context):
    prefs = get_preferences(context)
    parts = path.split(".")
    if parts[:2] == ["bpy", "context"]:
        parts = ["context", *parts[2:]]
    if not parts or parts[0] != "context":
        raise ValueError(t(prefs, "context_property_required"))

    target = context
    for part in parts[1:-1]:
        target = getattr(target, part)
    return target, parts[-1]


def safe_icon(icon_name: str) -> str:
    icon = (icon_name or "NONE").strip().upper() or "NONE"
    if icon == "NONE":
        return icon
    if icon in _get_builtin_icon_names():
        return icon
    return "NONE"


def _get_builtin_icon_names() -> set[str]:
    global _builtin_icon_names
    if _builtin_icon_names is None:
        try:
            parameter = bpy.types.UILayout.bl_rna.functions["operator"].parameters["icon"]
            _builtin_icon_names = {item.identifier for item in parameter.enum_items}
        except Exception:
            _builtin_icon_names = {"NONE"}
    return _builtin_icon_names


def _find_menu_by_uid(prefs, uid: str):
    for menu in prefs.pie_menus:
        if menu.uid == uid:
            return menu
    return None


def _ensure_menu_uid(menu_config):
    if not menu_config.uid:
        menu_config.uid = _new_uid()


def _ensure_slots(menu_config):
    while len(menu_config.slots) < 8:
        menu_config.slots.add()
    while len(menu_config.slots) > 8:
        menu_config.slots.remove(len(menu_config.slots) - 1)


def _new_uid() -> str:
    return uuid.uuid4().hex
