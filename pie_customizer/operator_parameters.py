"""Build a generic editor for scalar Blender operator properties."""

from __future__ import annotations

import json


SUPPORTED_TYPES = {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}


def _static_enum_items(prop) -> tuple:
    if prop.type != "ENUM":
        return ()
    try:
        return tuple(item for item in prop.enum_items_static if item.identifier)
    except (AttributeError, RuntimeError, TypeError):
        return ()


def _is_editable_property(prop) -> bool:
    if prop.identifier == "rna_type" or prop.type not in SUPPORTED_TYPES:
        return False
    if getattr(prop, "is_readonly", False) or getattr(prop, "is_hidden", False):
        return False
    if prop.type == "ENUM" and not _static_enum_items(prop):
        return False
    return not getattr(prop, "is_array", False)


def _enum_default(prop, enum_items: tuple) -> str:
    default = getattr(prop, "default", "")
    identifiers = {item.identifier for item in enum_items}
    if default in identifiers:
        return default
    return enum_items[0].identifier if enum_items else ""


def operator_has_editable_parameters(operator_id: str) -> bool:
    """Return whether Blender exposes scalar parameters for an operator."""

    try:
        import bpy

        module_name, operator_name = operator_id.split(".", 1)
        operator = getattr(getattr(bpy.ops, module_name), operator_name)
        return any(_is_editable_property(prop) for prop in operator.get_rna_type().properties)
    except (AttributeError, KeyError, RuntimeError, ValueError):
        return False


def populate_parameters(collection, operator_id: str, current_kwargs: dict | None = None) -> int:
    import bpy

    collection.clear()
    current_kwargs = current_kwargs or {}
    module_name, operator_name = operator_id.split(".", 1)
    operator = getattr(getattr(bpy.ops, module_name), operator_name)
    rna = operator.get_rna_type()

    for prop in rna.properties:
        if not _is_editable_property(prop):
            continue

        item = collection.add()
        item.identifier = prop.identifier
        item.label = bpy.app.translations.pgettext_iface(prop.name or prop.identifier)
        item.description = prop.description or prop.identifier
        item.enabled = prop.identifier in current_kwargs or bool(getattr(prop, "is_required", False))
        if prop.type == "ENUM" and getattr(prop, "is_enum_flag", False):
            default_value = getattr(prop, "default_flag", set())
        elif prop.type == "ENUM":
            enum_items = _static_enum_items(prop)
            default_value = _enum_default(prop, enum_items)
        else:
            default_value = getattr(prop, "default", None)
        value = current_kwargs.get(prop.identifier, default_value)

        if prop.type == "BOOLEAN":
            item.value_type = "BOOLEAN"
            item.bool_value = bool(value)
            if item.enabled:
                item.bool_mode = "TRUE" if item.bool_value else "FALSE"
            else:
                item.bool_mode = "DEFAULT"
        elif prop.type == "INT":
            item.value_type = "INT"
            item.int_value = int(value or 0)
        elif prop.type == "FLOAT":
            item.value_type = "FLOAT"
            item.float_value = float(value or 0.0)
        elif prop.type == "STRING":
            item.value_type = "STRING"
            item.string_value = str(value or "")
        elif prop.type == "ENUM" and getattr(prop, "is_enum_flag", False):
            item.value_type = "ENUM_FLAG"
            item.string_value = ", ".join(sorted(value or ()))
        elif prop.type == "ENUM":
            item.value_type = "ENUM"
            enum_items = [
                (enum.identifier, enum.name, enum.description or "")
                for enum in _static_enum_items(prop)
            ]
            item.enum_items_json = json.dumps(enum_items, ensure_ascii=False)
            identifiers = {entry[0] for entry in enum_items}
            enum_value = str(value or "")
            if enum_value not in identifiers and enum_items:
                enum_value = enum_items[0][0]
            if enum_value:
                item.enum_value = enum_value

    return len(collection)


def parameters_to_kwargs(parameters) -> dict:
    kwargs = {}
    for item in parameters:
        if item.value_type == "BOOLEAN" and hasattr(item, "bool_mode"):
            if item.bool_mode == "DEFAULT":
                continue
            kwargs[item.identifier] = item.bool_mode == "TRUE"
            continue
        if not item.enabled:
            continue
        if item.value_type == "BOOLEAN":
            value = item.bool_value
        elif item.value_type == "INT":
            value = item.int_value
        elif item.value_type == "FLOAT":
            value = item.float_value
        elif item.value_type == "ENUM":
            value = item.enum_value
        elif item.value_type == "ENUM_FLAG":
            value = {part.strip() for part in item.string_value.split(",") if part.strip()}
        else:
            value = item.string_value
        kwargs[item.identifier] = value
    return kwargs
