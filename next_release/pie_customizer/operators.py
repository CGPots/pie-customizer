"""Operators used by Pie Customizer."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

import bmesh
import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import runtime
from .action_parser import parse_operator_command
from .discovery import (
    canonical_operator_group,
    format_operator_command,
    operator_group_items,
)
from .localization import effective_language, t
from .model import PC_OperatorParameter
from .operator_parameters import parameters_to_kwargs, populate_parameters
from .shortcuts import MODIFIER_EVENT_TYPES, key_storage_name, shortcut_display, update_modifier_state
from .ui_style import SPACING_SMALL, draw_space


LOGGER = logging.getLogger(__name__)


class PC_OT_AddPieMenu(bpy.types.Operator):
    bl_idname = "pie_customizer.add_menu"
    bl_label = "Add Pie Menu"
    bl_description = "Create a new custom pie menu"

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        menu = prefs.pie_menus.add()
        menu.uid = uuid.uuid4().hex
        menu.name = f"{t(prefs, 'custom_pie')} {len(prefs.pie_menus)}"
        runtime.initialize_empty_menu(menu)
        prefs.active_menu_index = len(prefs.pie_menus) - 1
        return {"FINISHED"}


class PC_OT_RemovePieMenu(bpy.types.Operator):
    bl_idname = "pie_customizer.remove_menu"
    bl_label = "Remove Pie Menu"
    bl_description = "Remove the selected custom pie menu"

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        index = prefs.active_menu_index
        if 0 <= index < len(prefs.pie_menus):
            prefs.pie_menus.remove(index)
            prefs.active_menu_index = min(max(0, index - 1), max(0, len(prefs.pie_menus) - 1))
            runtime.rebuild_dynamic_menus(context)
        return {"FINISHED"}


class PC_OT_DuplicatePieMenu(bpy.types.Operator):
    bl_idname = "pie_customizer.duplicate_menu"
    bl_label = "Duplicate Pie Menu"
    bl_description = "Create a copy of the selected pie menu"

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        index = prefs.active_menu_index
        if not (0 <= index < len(prefs.pie_menus)):
            return {"CANCELLED"}

        source = prefs.pie_menus[index]
        data = runtime.serialize_menus(prefs)[index]
        data["uid"] = uuid.uuid4().hex
        data["name"] = (
            f"{source.name} Copy"
            if effective_language(context) == "EN"
            else f"{source.name} Копия"
        )
        runtime.load_menus(prefs, [data], replace=False)
        prefs.active_menu_index = len(prefs.pie_menus) - 1
        return {"FINISHED"}


class PC_OT_RebuildPieMenus(bpy.types.Operator):
    bl_idname = "pie_customizer.rebuild"
    bl_label = "Apply Pie Menus"
    bl_description = "Register custom pie menus and shortcuts"

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        errors = runtime.rebuild_dynamic_menus(context)
        if errors:
            self.report({"ERROR"}, errors[0])
            return {"CANCELLED"}
        self.report({"INFO"}, t(prefs, "registered"))
        return {"FINISHED"}


class PC_OT_CaptureShortcut(bpy.types.Operator):
    bl_idname = "pie_customizer.capture_shortcut"
    bl_label = "Assign Shortcut"
    bl_description = "Press a key to assign it to the selected pie menu"

    menu_uid: StringProperty(default="")  # type: ignore
    _modifier_state = None

    def invoke(self, context, event):
        return self._start_capture(context, event)

    def execute(self, context):
        return self._start_capture(context)

    def _start_capture(self, context, initial_event=None):
        prefs = runtime.get_preferences(context)
        if prefs is None or not prefs.pie_menus:
            self.report({"ERROR"}, t(prefs, "no_active_menu"))
            return {"CANCELLED"}

        menu = _menu_by_uid(prefs, self.menu_uid) if self.menu_uid else _active_menu(prefs)
        if menu is None:
            self.report({"ERROR"}, t(prefs, "no_active_menu"))
            return {"CANCELLED"}
        self.menu_uid = menu.uid
        for index, candidate in enumerate(prefs.pie_menus):
            if candidate.uid == menu.uid:
                prefs.active_menu_index = index
                break

        if bpy.app.background or context.window is None:
            self.report({"WARNING"}, t(prefs, "capture_shortcut_background"))
            return {"FINISHED"}

        self._modifier_state = {
            "ctrl": bool(getattr(initial_event, "ctrl", False)),
            "shift": bool(getattr(initial_event, "shift", False)),
            "alt": bool(getattr(initial_event, "alt", False)),
            "oskey": bool(getattr(initial_event, "oskey", False)),
        }
        self.report({"INFO"}, t(prefs, "capture_shortcut_prompt"))
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        prefs = runtime.get_preferences(context)
        menu = _menu_by_uid(prefs, self.menu_uid) if prefs is not None else None
        if menu is None:
            self.report({"ERROR"}, t(prefs, "no_active_menu"))
            return {"CANCELLED"}
        if event.type == "ESC" and event.value == "PRESS":
            self.report({"INFO"}, t(prefs, "capture_shortcut_cancelled"))
            return {"CANCELLED"}

        if event.type in MODIFIER_EVENT_TYPES:
            self._update_modifier_state(event)
            return {"RUNNING_MODAL"}
        if event.value != "PRESS":
            return {"RUNNING_MODAL"}
        if event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TIMER", "WINDOW_DEACTIVATE"}:
            return {"RUNNING_MODAL"}

        menu.key = key_storage_name(event.type)
        state = self._modifier_state or {}
        menu.ctrl = bool(event.ctrl or state.get("ctrl"))
        menu.shift = bool(event.shift or state.get("shift"))
        menu.alt = bool(event.alt or state.get("alt"))
        menu.oskey = bool(event.oskey or state.get("oskey"))

        readable = shortcut_display(menu.key, menu.ctrl, menu.shift, menu.alt, menu.oskey)
        errors = runtime.rebuild_dynamic_menus(context)
        if errors:
            self.report({"ERROR"}, errors[0])
            return {"CANCELLED"}

        self.report({"INFO"}, f"{t(prefs, 'capture_shortcut_set')}: {readable}")
        return {"FINISHED"}

    def _update_modifier_state(self, event):
        if self._modifier_state is None:
            self._modifier_state = {}
        update_modifier_state(self._modifier_state, event.type, event.value)


class PC_OT_AssignBrowserAction(bpy.types.Operator):
    bl_idname = "pie_customizer.assign_browser_action"
    bl_label = "Add Action to Pie Menu"
    bl_description = "Assign an action to the selected pie position"

    item_id: StringProperty(default="")  # type: ignore
    label: StringProperty(default="")  # type: ignore
    tooltip: StringProperty(default="")  # type: ignore
    command: StringProperty(default="")  # type: ignore
    icon: StringProperty(default="NONE")  # type: ignore
    slot_type: StringProperty(default="OPERATOR")  # type: ignore
    operator_context: StringProperty(default="INVOKE_DEFAULT")  # type: ignore

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip or cls.bl_description

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        menu = _active_menu(prefs)
        if menu is None:
            self.report({"ERROR"}, t(prefs, "no_active_menu"))
            return {"CANCELLED"}

        runtime.ensure_menu_shape(menu)
        slot = menu.slots[int(menu.active_slot_position)]
        slot.enabled = True
        slot.label = self.label or self.item_id
        slot.icon = self.icon or "NONE"
        slot.slot_type = self.slot_type
        slot.command = self.command
        slot.operator_context = self.operator_context
        self.report({"INFO"}, f"{t(prefs, 'catalog_action_assigned')}: {slot.label}")
        return {"FINISHED"}


class PC_OT_ToggleFavorite(bpy.types.Operator):
    bl_idname = "pie_customizer.toggle_favorite"
    bl_label = "Add or Remove Favorite"
    bl_description = "Save this action in catalog favorites"

    token: StringProperty(default="")  # type: ignore
    kind: StringProperty(default="OPERATOR")  # type: ignore
    item_id: StringProperty(default="")  # type: ignore
    group: StringProperty(default="")  # type: ignore
    label: StringProperty(default="")  # type: ignore
    tooltip: StringProperty(default="")  # type: ignore
    command: StringProperty(default="")  # type: ignore
    icon: StringProperty(default="NONE")  # type: ignore
    slot_type: StringProperty(default="OPERATOR")  # type: ignore
    operator_context: StringProperty(default="INVOKE_DEFAULT")  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        for index, favorite in enumerate(prefs.favorite_actions):
            if favorite.token == self.token:
                prefs.favorite_actions.remove(index)
                prefs.catalog_page = 0
                self.report({"INFO"}, t(prefs, "favorite_removed"))
                return {"FINISHED"}

        favorite = prefs.favorite_actions.add()
        favorite.token = self.token
        favorite.kind = self.kind
        favorite.item_id = self.item_id
        favorite.group = self.group
        favorite.label = self.label
        favorite.description = self.tooltip
        favorite.command = self.command
        favorite.icon = self.icon
        favorite.slot_type = self.slot_type
        favorite.operator_context = self.operator_context
        prefs.catalog_page = 0
        self.report({"INFO"}, t(prefs, "favorite_added"))
        return {"FINISHED"}


class PC_OT_CatalogPage(bpy.types.Operator):
    bl_idname = "pie_customizer.catalog_page"
    bl_label = "Change Catalog Page"

    direction: IntProperty(default=1)  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        prefs.catalog_page = max(0, prefs.catalog_page + self.direction)
        return {"FINISHED"}


class PC_OT_SelectCatalogSection(bpy.types.Operator):
    bl_idname = "pie_customizer.select_catalog_section"
    bl_label = "Open Command Section"
    bl_description = "Show commands in the selected section"

    section: StringProperty(default="")  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        prefs.catalog_section = self.section
        prefs.catalog_group = ""
        prefs.catalog_page = 0
        prefs.command_search = ""
        return {"FINISHED"}


class PC_OT_SelectCatalogGroup(bpy.types.Operator):
    bl_idname = "pie_customizer.select_catalog_group"
    bl_label = "Open Command Group"
    bl_description = "Show operators in the selected group"

    group: StringProperty(default="")  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        prefs.catalog_group = self.group
        prefs.catalog_page = 0
        prefs.command_search = ""
        return {"FINISHED"}


def _operator_group_search_items(self, context):
    return operator_group_items(effective_language(context))


class PC_OT_SelectOperatorGroup(bpy.types.Operator):
    bl_idname = "pie_customizer.select_operator_group"
    bl_label = "Select Command Source"
    bl_description = "Search and select a Blender operator source"
    bl_property = "group"

    group: EnumProperty(items=_operator_group_search_items)  # type: ignore

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None:
            return {"CANCELLED"}
        prefs.operator_group = canonical_operator_group(self.group)
        prefs.catalog_page = 0
        return {"FINISHED"}


class PC_OT_ConfigureOperator(bpy.types.Operator):
    bl_idname = "pie_customizer.configure_operator"
    bl_label = "Command Parameters"
    bl_description = "Configure Blender operator parameters"

    menu_uid: StringProperty(default="")  # type: ignore
    slot_position: StringProperty(default="0")  # type: ignore
    operator_id: StringProperty(default="")  # type: ignore
    parameters: CollectionProperty(type=PC_OperatorParameter)  # type: ignore

    def invoke(self, context, event):
        prefs = runtime.get_preferences(context)
        menu = _menu_by_uid(prefs, self.menu_uid)
        if menu is None:
            return {"CANCELLED"}
        slot = menu.slots[int(self.slot_position)]
        try:
            parsed = parse_operator_command(slot.command)
            self.operator_id = parsed.operator_id
            count = populate_parameters(self.parameters, self.operator_id, parsed.kwargs)
        except Exception as exc:
            LOGGER.exception("Could not open operator parameters")
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        if count == 0:
            self.report({"INFO"}, t(prefs, "no_operator_parameters"))
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self, width=560)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.operator_id, icon="OPTIONS")
        draw_space(layout, SPACING_SMALL)
        parameter_box = layout.box()
        parameter_column = parameter_box.column(align=False)
        for parameter in self.parameters:
            row = parameter_column.row(align=True)
            split = row.split(factor=0.45, align=True)
            label = parameter.label or parameter.identifier
            if parameter.value_type == "BOOLEAN":
                split.label(text=label)
                split.prop(parameter, "bool_mode", text="")
                continue

            label_row = split.row(align=True)
            label_row.prop(parameter, "enabled", text="")
            label_row.label(text=label)
            value_row = split.row(align=True)
            value_row.enabled = parameter.enabled
            if parameter.value_type == "INT":
                value_row.prop(parameter, "int_value", text="")
            elif parameter.value_type == "FLOAT":
                value_row.prop(parameter, "float_value", text="")
            elif parameter.value_type == "ENUM":
                value_row.prop(parameter, "enum_value", text="")
            else:
                value_row.prop(parameter, "string_value", text="")

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        menu = _menu_by_uid(prefs, self.menu_uid)
        if menu is None:
            return {"CANCELLED"}
        slot = menu.slots[int(self.slot_position)]
        slot.command = format_operator_command(self.operator_id, parameters_to_kwargs(self.parameters))
        self.report({"INFO"}, t(prefs, "operator_parameters_saved"))
        return {"FINISHED"}


class PC_OT_ClearSlot(bpy.types.Operator):
    bl_idname = "pie_customizer.clear_slot"
    bl_label = "Clear Position"
    bl_description = "Remove the action from the selected pie position"

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        if prefs is None or not prefs.pie_menus:
            self.report({"ERROR"}, t(prefs, "no_active_menu"))
            return {"CANCELLED"}

        index = min(max(prefs.active_menu_index, 0), len(prefs.pie_menus) - 1)
        menu = prefs.pie_menus[index]
        runtime.ensure_menu_shape(menu)
        slot = menu.slots[int(menu.active_slot_position)]
        runtime.clear_slot(slot)
        self.report({"INFO"}, t(prefs, "slot_cleared"))
        return {"FINISHED"}


class PC_OT_SelectSlot(bpy.types.Operator):
    bl_idname = "pie_customizer.select_slot"
    bl_label = "Select Position"
    bl_description = "Select a disabled position for editing"

    position: StringProperty(default="0")  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        menu = _active_menu(prefs)
        if menu is None or self.position not in {str(index) for index in range(8)}:
            return {"CANCELLED"}
        menu.active_slot_position = self.position
        return {"FINISHED"}


class PC_OT_AddMirrorXCleanSeam(bpy.types.Operator):
    bl_idname = "pie_customizer.add_mirror_x_clean_seam"
    bl_label = "Add Mirror X from 3D Cursor and Clean Seam"
    bl_description = (
        "Create a Plain Axes Empty at the 3D Cursor, use it as the Mirror "
        "Object, and delete selected or automatically detected seam faces"
    )
    bl_options = {"REGISTER", "UNDO"}

    delete_selected_faces: BoolProperty(  # type: ignore
        name="Delete Seam Faces",
        description=(
            "Delete selected faces, or automatically delete the closest cap "
            "facing the mirror plane when no faces are selected"
        ),
        default=True,
    )
    use_clip: BoolProperty(  # type: ignore
        name="Clip at Mirror Plane",
        description="Prevent vertices from crossing the mirror plane",
        default=True,
    )
    merge_threshold: FloatProperty(  # type: ignore
        name="Merge Distance",
        description="Distance used to merge vertices at the mirror plane",
        default=0.001,
        min=0.0,
        max=1.0,
        precision=4,
        subtype="DISTANCE",
    )
    use_bisect: BoolProperty(  # type: ignore
        name="Bisect X",
        description="Cut the mesh at the X mirror plane before mirroring",
        default=False,
    )
    flip_bisect: BoolProperty(  # type: ignore
        name="Flip Bisect Side",
        description="Keep the opposite side of the X bisect",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        return (
            active_object is not None
            and active_object.type == "MESH"
            and context.mode in {"OBJECT", "EDIT_MESH"}
        )

    def execute(self, context):
        active_object = context.active_object
        deleted_faces = 0
        mirror_matrix = context.scene.cursor.matrix.copy()

        if self.delete_selected_faces:
            if context.mode == "EDIT_MESH":
                edit_mesh = bmesh.from_edit_mesh(active_object.data)
                edit_mesh.normal_update()
                seam_faces = [
                    face for face in edit_mesh.faces if face.select and not face.hide
                ]
                if not seam_faces:
                    seam_faces = _automatic_mirror_seam_faces(
                        edit_mesh.faces,
                        active_object.matrix_world,
                        mirror_matrix,
                        self.merge_threshold,
                    )
                deleted_faces = len(seam_faces)
                if seam_faces:
                    bmesh.ops.delete(
                        edit_mesh,
                        geom=seam_faces,
                        context="FACES_ONLY",
                    )
                    bmesh.update_edit_mesh(
                        active_object.data,
                        loop_triangles=False,
                        destructive=True,
                    )
            else:
                object_mesh = bmesh.new()
                object_mesh.from_mesh(active_object.data)
                object_mesh.normal_update()
                seam_faces = _automatic_mirror_seam_faces(
                    object_mesh.faces,
                    active_object.matrix_world,
                    mirror_matrix,
                    self.merge_threshold,
                )
                deleted_faces = len(seam_faces)
                if seam_faces:
                    bmesh.ops.delete(
                        object_mesh,
                        geom=seam_faces,
                        context="FACES_ONLY",
                    )
                    object_mesh.to_mesh(active_object.data)
                    active_object.data.update()
                object_mesh.free()

        modifier = active_object.modifiers.new(name="Mirror X", type="MIRROR")
        modifier.use_axis[0] = True
        modifier.use_axis[1] = False
        modifier.use_axis[2] = False
        modifier.use_clip = self.use_clip
        modifier.use_mirror_merge = True
        modifier.merge_threshold = self.merge_threshold
        modifier.use_bisect_axis[0] = self.use_bisect
        modifier.use_bisect_flip_axis[0] = self.flip_bisect

        mirror_object = bpy.data.objects.new(
            name="mrr",
            object_data=None,
        )
        mirror_object.empty_display_type = "PLAIN_AXES"
        mirror_object.empty_display_size = 1.0
        mirror_object.matrix_world = mirror_matrix
        target_collection = (
            active_object.users_collection[0]
            if active_object.users_collection
            else context.collection
        )
        target_collection.objects.link(mirror_object)
        modifier.mirror_object = mirror_object

        self.report(
            {"INFO"},
            f"{t(runtime.get_preferences(context), 'mirror_x_added')}: {deleted_faces}",
        )
        return {"FINISHED"}


def _automatic_mirror_seam_faces(
    faces,
    object_matrix,
    mirror_matrix,
    merge_threshold,
):
    """Find the nearest cap facing the local-X plane of the mirror object."""

    object_to_mirror = mirror_matrix.inverted_safe() @ object_matrix
    normal_matrix = object_to_mirror.to_3x3().inverted_safe().transposed()
    tolerance = max(float(merge_threshold), 1e-6)
    candidates = []

    for face in faces:
        if face.hide:
            continue
        center = object_to_mirror @ face.calc_center_median()
        normal = normal_matrix @ face.normal
        if normal.length_squared == 0.0:
            continue
        normal.normalize()

        if abs(center.x) <= tolerance:
            facing_amount = abs(normal.x)
        else:
            direction_to_plane = -1.0 if center.x > 0.0 else 1.0
            facing_amount = normal.x * direction_to_plane
        if facing_amount < 0.5:
            continue
        candidates.append((abs(center.x), face))

    if not candidates:
        return []
    nearest_distance = min(distance for distance, _face in candidates)
    return [
        face
        for distance, face in candidates
        if distance <= nearest_distance + tolerance
    ]


def _active_menu(prefs):
    if prefs is None or not prefs.pie_menus:
        return None
    index = min(max(prefs.active_menu_index, 0), len(prefs.pie_menus) - 1)
    return prefs.pie_menus[index]


def _menu_by_uid(prefs, uid: str):
    if prefs is None:
        return None
    for menu in prefs.pie_menus:
        if menu.uid == uid:
            return menu
    return None


class PC_OT_RunAction(bpy.types.Operator):
    bl_idname = "pie_customizer.run_action"
    bl_label = "Run Pie Menu Action"
    bl_options = {"REGISTER", "UNDO"}

    action_type: EnumProperty(  # type: ignore
        items=(
            ("OPERATOR", "Operator", ""),
            ("PROPERTY", "Property", ""),
        ),
        default="OPERATOR",
    )
    command: StringProperty(default="")  # type: ignore
    operator_context: StringProperty(default="INVOKE_DEFAULT")  # type: ignore

    def execute(self, context):
        try:
            if self.action_type == "OPERATOR":
                return runtime.run_operator_command(self.command, self.operator_context)
            if self.action_type == "PROPERTY":
                return runtime.run_property_command(self.command, context)
        except Exception as exc:
            LOGGER.exception("Pie action failed | type=%s", self.action_type)
            self.report({"ERROR"}, f"Pie Customizer: {exc}")
            return {"CANCELLED"}

        return {"CANCELLED"}


class PC_OT_ExportPreset(bpy.types.Operator, ExportHelper):
    bl_idname = "pie_customizer.export_preset"
    bl_label = "Export Pie Menus"
    bl_description = "Export custom pie menus to a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        payload = {
            "version": 1,
            "addon": "pie_customizer",
            "pie_menus": runtime.serialize_menus(prefs),
        }
        try:
            Path(self.filepath).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as exc:
            LOGGER.exception("Preset export failed")
            self.report({"ERROR"}, f"{t(prefs, 'export_failed')}: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{t(prefs, 'exported')}: {len(payload['pie_menus'])}")
        return {"FINISHED"}


class PC_OT_ImportPreset(bpy.types.Operator, ImportHelper):
    bl_idname = "pie_customizer.import_preset"
    bl_label = "Import Pie Menus"
    bl_description = "Import custom pie menus from a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})  # type: ignore
    merge_mode: EnumProperty(  # type: ignore
        name="Import Mode",
        items=(
            ("APPEND", "Append", "Append imported menus to the existing menus"),
            ("REPLACE", "Replace", "Remove existing menus and load the imported menus"),
        ),
        default="APPEND",
    )

    def draw(self, context):
        self.layout.prop(self, "merge_mode", expand=True)

    def execute(self, context):
        prefs = runtime.get_preferences(context)
        backup = runtime.serialize_menus(prefs)
        try:
            payload = json.loads(Path(self.filepath).read_text(encoding="utf-8"))
            items = payload.get("pie_menus")
            if not isinstance(items, list):
                raise ValueError(t(prefs, "missing_menus"))
            runtime.load_menus(prefs, items, replace=self.merge_mode == "REPLACE")
        except Exception as exc:
            LOGGER.exception("Preset import failed")
            if runtime.serialize_menus(prefs) != backup:
                runtime.load_menus(prefs, backup, replace=True)
            self.report({"ERROR"}, f"{t(prefs, 'import_failed')}: {exc}")
            return {"CANCELLED"}

        prefs.active_menu_index = max(0, len(prefs.pie_menus) - 1)
        runtime.rebuild_dynamic_menus(context)
        self.report({"INFO"}, f"{t(prefs, 'imported')}: {len(items)}")
        return {"FINISHED"}


CLASSES = (
    PC_OT_AddPieMenu,
    PC_OT_RemovePieMenu,
    PC_OT_DuplicatePieMenu,
    PC_OT_RebuildPieMenus,
    PC_OT_CaptureShortcut,
    PC_OT_AssignBrowserAction,
    PC_OT_ToggleFavorite,
    PC_OT_CatalogPage,
    PC_OT_SelectCatalogSection,
    PC_OT_SelectCatalogGroup,
    PC_OT_SelectOperatorGroup,
    PC_OT_ConfigureOperator,
    PC_OT_ClearSlot,
    PC_OT_SelectSlot,
    PC_OT_AddMirrorXCleanSeam,
    PC_OT_RunAction,
    PC_OT_ExportPreset,
    PC_OT_ImportPreset,
)
