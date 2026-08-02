"""Parsing helpers that do not depend on Blender's Python runtime."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any


_OPERATOR_RE = re.compile(r"^[A-Za-z_]\w*\.[A-Za-z_]\w*$")
_PROPERTY_RE = re.compile(r"^(?:bpy\.)?context(?:\.[A-Za-z_]\w*)+$")


@dataclass(frozen=True)
class OperatorCommand:
    operator_id: str
    kwargs: dict[str, Any]


@dataclass(frozen=True)
class PropertyCommand:
    path: str
    value: Any
    has_value: bool


def parse_operator_command(command: str) -> OperatorCommand:
    """Parse mesh.primitive_cube_add(size=2) or bpy.ops.mesh.primitive_cube_add()."""

    text = command.strip()
    if not text:
        raise ValueError("Operator command is empty")

    if "(" not in text:
        operator_id = _normalize_operator_id(text)
        return OperatorCommand(operator_id=operator_id, kwargs={})

    call = _parse_expression_node(text, "Invalid operator syntax")
    if not isinstance(call, ast.Call):
        raise ValueError("Operator command must be a function call")

    if call.args:
        raise ValueError("Only keyword arguments are supported")

    operator_id = _normalize_operator_id(_dotted_name(call.func))
    kwargs: dict[str, Any] = {}
    for keyword in call.keywords:
        if keyword.arg is None:
            raise ValueError("Expanded keyword arguments are not supported")
        try:
            kwargs[keyword.arg] = _literal_from_node(keyword.value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Argument {keyword.arg!r} must be a Python literal") from exc

    return OperatorCommand(operator_id=operator_id, kwargs=kwargs)


def parse_property_command(command: str) -> PropertyCommand:
    """Parse context.scene.tool_settings.use_snap or path = value."""

    text = command.strip()
    if not text:
        raise ValueError("Property command is empty")

    if "=" in text:
        path, raw_value = text.split("=", 1)
        path = _normalize_property_path(path.strip())
        value = _parse_literal(raw_value.strip())
        return PropertyCommand(path=path, value=value, has_value=True)

    path = _normalize_property_path(text)
    return PropertyCommand(path=path, value=None, has_value=False)


def _normalize_operator_id(path: str) -> str:
    path = path.strip()
    if path.startswith("bpy.ops."):
        path = path[len("bpy.ops.") :]
    if not _OPERATOR_RE.match(path):
        raise ValueError("Use an operator id like object.delete or mesh.primitive_cube_add()")
    return path


def _normalize_property_path(path: str) -> str:
    path = path.strip()
    if path.startswith("bpy.context."):
        path = "context." + path[len("bpy.context.") :]
    if not _PROPERTY_RE.match(path):
        raise ValueError("Use a property path like context.space_data.overlay.show_overlays")
    return path


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted_name(node.value)}.{node.attr}"
    raise ValueError("Operator function must be a dotted name")


def _parse_literal(value: str) -> Any:
    if value == "":
        raise ValueError("Property value is empty")
    try:
        node = _parse_expression_node(value, "Invalid property value")
        return _literal_from_node(node)
    except (TypeError, ValueError):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        return value


def _parse_expression_node(source: str, error_prefix: str) -> ast.AST:
    try:
        module = ast.parse(f"_pie_customizer_value = {source}")
    except SyntaxError as exc:
        raise ValueError(f"{error_prefix}: {exc.msg}") from exc

    if len(module.body) != 1 or not isinstance(module.body[0], ast.Assign):
        raise ValueError(error_prefix)
    return module.body[0].value


def _literal_from_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_literal_from_node(item) for item in node.elts)
    if isinstance(node, ast.List):
        return [_literal_from_node(item) for item in node.elts]
    if isinstance(node, ast.Set):
        return {_literal_from_node(item) for item in node.elts}
    if isinstance(node, ast.Dict):
        return {
            _literal_from_node(key): _literal_from_node(value)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _literal_from_node(node.operand)
        if not isinstance(operand, (int, float, complex)):
            raise ValueError("Unary signs are only valid for numbers")
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "set"
        and not node.args
        and not node.keywords
    ):
        return set()
    raise ValueError("Only literal values are supported")
