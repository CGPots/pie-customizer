"""Audit catalog operators without executing destructive Blender actions.

Run with Blender in background mode. The audit validates every curated command
against the active Blender RNA schema and inspects every automatically
discovered operator for broken defaults and poll-time exceptions.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import addon_utils
import bpy


def _operator(operator_id: str):
    namespace, name = operator_id.split(".", 1)
    operator_namespace = getattr(bpy.ops, namespace, None)
    return getattr(operator_namespace, name, None) if operator_namespace else None


def _enum_identifiers(prop) -> set[str]:
    try:
        return {item.identifier for item in prop.enum_items_static}
    except Exception:
        return set()


def _value_error(prop, value: Any) -> str | None:
    prop_type = prop.type
    if prop_type == "BOOLEAN" and not isinstance(value, bool):
        return "expected boolean"
    if prop_type == "INT" and (not isinstance(value, int) or isinstance(value, bool)):
        return "expected integer"
    if prop_type == "FLOAT" and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        return "expected number"
    if prop_type == "STRING" and not isinstance(value, str):
        return "expected string"
    if prop_type == "ENUM":
        identifiers = _enum_identifiers(prop)
        if prop.is_enum_flag:
            if not isinstance(value, (set, tuple, list)):
                return "expected an enum flag collection"
            unknown = set(value) - identifiers
            if unknown:
                return f"unknown enum flags: {sorted(unknown)}"
        elif not isinstance(value, str):
            return "expected enum identifier"
        elif identifiers and value not in identifiers:
            return f"unknown enum value {value!r}; expected one of {sorted(identifiers)}"
    return None


def _audit_curated_actions(actions, parse_operator_command) -> list[str]:
    errors: list[str] = []
    for action in actions:
        if action.slot_type != "OPERATOR":
            continue
        try:
            parsed = parse_operator_command(action.command)
        except ValueError as exc:
            errors.append(f"{action.action_id}: parse error: {exc}")
            continue

        operator = _operator(parsed.operator_id)
        if operator is None:
            errors.append(f"{action.action_id}: missing operator {parsed.operator_id}")
            continue

        try:
            properties = operator.get_rna_type().properties
        except Exception as exc:
            errors.append(f"{action.action_id}: RNA lookup failed: {exc}")
            continue

        for name, value in parsed.kwargs.items():
            prop = properties.get(name)
            if prop is None:
                errors.append(
                    f"{action.action_id}: {parsed.operator_id} has no argument {name!r}"
                )
                continue
            value_error = _value_error(prop, value)
            if value_error:
                errors.append(f"{action.action_id}.{name}: {value_error}")
    return errors


def _audit_discovered(actions, parse_operator_command) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    poll_errors: list[str] = []
    empty_string_inputs: list[str] = []

    for action in actions:
        counts["operators"] += 1
        parsed = parse_operator_command(action.command)
        operator = _operator(parsed.operator_id)
        if operator is None:
            counts["missing"] += 1
            continue

        try:
            rna = operator.get_rna_type()
        except Exception as exc:
            counts["rna_errors"] += 1
            poll_errors.append(f"{parsed.operator_id}: RNA lookup failed: {exc}")
            continue

        properties = [prop for prop in rna.properties if prop.identifier != "rna_type"]
        if not properties:
            counts["without_parameters"] += 1
        else:
            counts["with_parameters"] += 1

        for prop in properties:
            if (
                prop.type == "STRING"
                and getattr(prop, "default", None) == ""
                and not prop.is_hidden
            ):
                empty_string_inputs.append(f"{parsed.operator_id}.{prop.identifier}")

        try:
            if operator.poll():
                counts["poll_true"] += 1
            else:
                counts["poll_false"] += 1
        except Exception as exc:
            poll_errors.append(f"{parsed.operator_id}: {type(exc).__name__}: {exc}")

    counts["poll_errors"] = len(poll_errors)
    counts["empty_string_inputs"] = len(empty_string_inputs)
    return {
        "counts": dict(sorted(counts.items())),
        "poll_errors": poll_errors,
        "empty_string_inputs": empty_string_inputs,
    }


def _audit_parameter_editors(
    actions,
    parse_operator_command,
    operator_has_editable_parameters,
    populate_parameters,
    parameters_to_kwargs,
    parameter_type,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    errors: list[str] = []
    property_name = "pie_customizer_parameter_audit"
    setattr(
        bpy.types.Scene,
        property_name,
        bpy.props.CollectionProperty(type=parameter_type),
    )
    parameters = getattr(bpy.context.scene, property_name)

    try:
        for action in actions:
            parsed = parse_operator_command(action.command)
            operator_id = parsed.operator_id
            try:
                count = populate_parameters(parameters, operator_id)
                has_parameters = operator_has_editable_parameters(operator_id)
            except Exception as exc:
                errors.append(
                    f"{operator_id}: parameter editor failed: "
                    f"{type(exc).__name__}: {exc}"
                )
                continue

            if has_parameters != bool(count):
                errors.append(
                    f"{operator_id}: button={has_parameters}, populated={count}"
                )
                continue

            if count:
                counts["with_editable_parameters"] += 1
            else:
                counts["without_editable_parameters"] += 1

            try:
                kwargs = parameters_to_kwargs(parameters)
                operator = _operator(operator_id)
                properties = operator.get_rna_type().properties
                for name, value in kwargs.items():
                    prop = properties.get(name)
                    if prop is None:
                        errors.append(f"{operator_id}: unknown parameter {name!r}")
                        continue
                    value_error = _value_error(prop, value)
                    if value_error:
                        errors.append(f"{operator_id}.{name}: {value_error}")
            except Exception as exc:
                errors.append(
                    f"{operator_id}: parameter serialization failed: "
                    f"{type(exc).__name__}: {exc}"
                )
    finally:
        delattr(bpy.types.Scene, property_name)

    counts["errors"] = len(errors)
    return {
        "counts": dict(sorted(counts.items())),
        "errors": errors,
    }


def main() -> None:
    source_path = None
    if "--" in sys.argv:
        source_path = str(Path(sys.argv[sys.argv.index("--") + 1]).resolve())
        sys.path.insert(0, source_path)

    module = addon_utils.enable("pie_customizer", default_set=False, persistent=False)
    assert module is not None

    from pie_customizer.action_parser import parse_operator_command
    from pie_customizer.command_catalog import ACTIONS
    from pie_customizer.discovery import (
        DISCOVERY_EXCLUDED_OPERATOR_IDS,
        discover_operator_actions,
    )
    from pie_customizer.model import PC_OperatorParameter
    from pie_customizer.operator_parameters import (
        operator_has_editable_parameters,
        parameters_to_kwargs,
        populate_parameters,
    )

    curated_errors = _audit_curated_actions(ACTIONS, parse_operator_command)
    discovered_actions = discover_operator_actions()
    discovered_ids = {
        parse_operator_command(action.command).operator_id for action in discovered_actions
    }
    leaked_exclusions = sorted(DISCOVERY_EXCLUDED_OPERATOR_IDS & discovered_ids)
    discovered_report = _audit_discovered(discovered_actions, parse_operator_command)
    parameter_report = _audit_parameter_editors(
        discovered_actions,
        parse_operator_command,
        operator_has_editable_parameters,
        populate_parameters,
        parameters_to_kwargs,
        PC_OperatorParameter,
    )

    report = {
        "blender": bpy.app.version_string,
        "curated_actions": len(ACTIONS),
        "curated_errors": curated_errors,
        "discovered_counts": discovered_report["counts"],
        "discovered_poll_errors": discovered_report["poll_errors"],
        "discovered_empty_string_samples": discovered_report[
            "empty_string_inputs"
        ][:10],
        "parameter_editor_counts": parameter_report["counts"],
        "parameter_editor_errors": parameter_report["errors"],
        "excluded_operators": sorted(DISCOVERY_EXCLUDED_OPERATOR_IDS),
        "leaked_exclusions": leaked_exclusions,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    assert not curated_errors, "Curated operator audit failed"
    assert not leaked_exclusions, "Excluded operators leaked into discovery"
    assert not discovered_report["poll_errors"], "Operator poll raised an exception"
    assert not parameter_report["errors"], "Operator parameter editor audit failed"

    addon_utils.disable("pie_customizer", default_set=False)
    if source_path is not None:
        sys.path.remove(source_path)
    print("PIE_CUSTOMIZER_OPERATOR_AUDIT_OK")


if __name__ == "__main__":
    main()
