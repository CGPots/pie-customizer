"""Curated Blender actions used by the visual pie menu editor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogAction:
    action_id: str
    category: str
    label_ru: str
    label_en: str
    icon: str
    slot_type: str
    command: str
    operator_context: str = "INVOKE_DEFAULT"
    group: str = ""


CATEGORY_ITEMS = (
    ("ADD", "Добавить", "Создание объектов и примитивов"),
    ("TRANSFORM", "Трансформация", "Перемещение, вращение и масштаб"),
    ("OBJECT", "Объект", "Действия Object Mode"),
    ("MESH", "Сетка", "Действия Edit Mode для сетки"),
    ("SCULPT", "Скульптинг", "Действия Sculpt Mode"),
    ("PAINT", "Рисование", "Texture, Vertex, Weight Paint и Grease Pencil"),
    ("SELECT", "Выделение", "Выделение объектов и элементов сетки"),
    ("VIEW", "Вид", "Навигация и отображение 3D View"),
    ("CUSTOM", "Своя команда", "Ручная настройка действия"),
)


def _variant_actions(category, variants, command_template):
    return tuple(
        CatalogAction(
            action_id,
            category,
            label_ru,
            label_en,
            icon,
            "OPERATOR",
            command_template.format(value=value),
            "EXEC_DEFAULT",
        )
        for action_id, value, label_ru, label_en, icon in variants
    )


def _property_actions(category, group, prefix, base_path, variants):
    return tuple(
        CatalogAction(
            f"{prefix}_{action_id}",
            category,
            label_ru,
            label_en,
            icon,
            "PROPERTY",
            f"{base_path}.{property_name}",
            group=group,
        )
        for action_id, property_name, label_ru, label_en, icon in variants
    )


def _tool_settings_rna_properties():
    """Return ToolSettings RNA properties inside Blender, or None in unit tests."""

    try:
        import bpy
    except ModuleNotFoundError:
        return None

    try:
        return bpy.types.ToolSettings.bl_rna.properties
    except (AttributeError, RuntimeError):
        return None


def _tool_settings_property_actions(category, group, prefix, variants):
    properties = _tool_settings_rna_properties()
    if properties is not None:
        variants = tuple(
            variant for variant in variants if properties.get(variant[1]) is not None
        )
    return _property_actions(
        category,
        group,
        prefix,
        "context.scene.tool_settings",
        variants,
    )


def _tool_settings_value_actions(category, group, prefix, variants):
    """Create version-aware actions that assign a ToolSettings literal value."""

    properties = _tool_settings_rna_properties()
    actions = []
    for action_id, property_name, value, label_ru, label_en, icon in variants:
        prop = properties.get(property_name) if properties is not None else None
        if properties is not None and prop is None:
            continue
        if prop is not None and prop.type == "ENUM":
            supported = {
                item.identifier for item in prop.enum_items_static if item.identifier
            }
            requested = set(value) if isinstance(value, set) else {value}
            if not requested.issubset(supported):
                continue
        actions.append(
            CatalogAction(
                f"{prefix}_{action_id}",
                category,
                label_ru,
                label_en,
                icon,
                "PROPERTY",
                f"context.scene.tool_settings.{property_name} = {value!r}",
                group=group,
            )
        )
    return tuple(actions)


def _supported_operator_enum_values(operator_id, property_name):
    """Return Blender's static enum values when running inside Blender."""

    try:
        import bpy
    except ModuleNotFoundError:
        return None

    try:
        namespace, name = operator_id.split(".", 1)
        operator = getattr(getattr(bpy.ops, namespace), name)
        prop = operator.get_rna_type().properties[property_name]
        return {item.identifier for item in prop.enum_items_static}
    except Exception:
        return None


def _convert_variants():
    supported = _supported_operator_enum_values("object.convert", "target")
    variants = [
        ("convert_curve", "CURVE", "Преобразовать в Curve", "Convert to Curve", "CURVE_DATA"),
        ("convert_mesh", "MESH", "Преобразовать в Mesh", "Convert to Mesh", "MESH_DATA"),
    ]
    if supported is None or "POINTCLOUD" in supported:
        variants.append(
            ("convert_pointcloud", "POINTCLOUD", "Преобразовать в Point Cloud", "Convert to Point Cloud", "POINTCLOUD_DATA")
        )
    variants.append(
        ("convert_curves", "CURVES", "Преобразовать в Curves", "Convert to Curves", "CURVES_DATA")
    )
    grease_pencil_target = "GREASEPENCIL"
    if supported is not None and grease_pencil_target not in supported:
        grease_pencil_target = "GPENCIL"
    variants.append(
        (
            "convert_grease_pencil",
            grease_pencil_target,
            "Преобразовать в Grease Pencil",
            "Convert to Grease Pencil",
            "GREASEPENCIL",
        )
    )
    return tuple(variants)


def catalog_action_group(action: CatalogAction) -> str:
    if action.group:
        return action.group

    action_id = action.action_id

    if action.category == "ADD":
        return "add_empties" if action_id.startswith("add_empty") else "add_primitives"

    if action.category == "TRANSFORM":
        if action_id.startswith("orientation_"):
            return "transform_orientations"
        if action_id.startswith("pivot_"):
            return "transform_pivots"
        if action_id.startswith("falloff_"):
            return "transform_falloff"
        if action_id.startswith("clear_") or action_id == "apply_transforms":
            return "transform_reset"
        return "transform_basic"

    if action.category == "OBJECT":
        if action_id.startswith("shade_"):
            return "object_shading"
        if action_id.startswith("origin_") or action_id == "geometry_to_origin":
            return "object_origin"
        if action_id.startswith("convert_"):
            return "object_convert"
        if action_id.startswith("mode_"):
            return "object_modes"
        return "object_actions"

    if action.category == "MESH":
        if action_id.startswith("mesh_merge_"):
            return "mesh_merge"
        if action_id.startswith("mesh_delete") or action_id == "mesh_dissolve":
            return "mesh_delete"
        if action_id.startswith("select_mode_"):
            return "mesh_select_mode"
        return "mesh_modeling"

    if action.category == "SCULPT":
        if action_id.startswith("sculpt_mask_"):
            return "sculpt_masks"
        if action_id.startswith("sculpt_voxel_"):
            return "sculpt_remesh"
        if action_id.startswith("sculpt_symmetr") or action_id == "sculpt_mirror_x":
            return "sculpt_symmetry"
        if action_id.startswith("sculpt_overlay_"):
            return "sculpt_display"
        return "sculpt_actions"

    if action.category == "PAINT":
        if action_id.startswith("mode_"):
            return "paint_modes"
        return "paint_actions"

    if action.category == "SELECT":
        return "select_objects" if action_id.endswith("_objects") else "select_mesh"

    if action.category == "VIEW":
        if action_id.startswith("shading_") or action_id == "toggle_overlays":
            return "view_display"
        if action_id.startswith("view_") and action_id not in {"view_selected", "view_all"}:
            return "view_axes"
        if action_id in {"search_menu", "maximize_area"}:
            return "view_interface"
        return "view_navigation"

    return action.category.casefold()


ACTIONS = (
    CatalogAction("add_cube", "ADD", "Куб", "Cube", "MESH_CUBE", "OPERATOR", "mesh.primitive_cube_add()"),
    CatalogAction("add_uv_sphere", "ADD", "UV-сфера", "UV Sphere", "MESH_UVSPHERE", "OPERATOR", "mesh.primitive_uv_sphere_add()"),
    CatalogAction("add_cylinder", "ADD", "Цилиндр", "Cylinder", "MESH_CYLINDER", "OPERATOR", "mesh.primitive_cylinder_add()"),
    CatalogAction("add_plane", "ADD", "Плоскость", "Plane", "MESH_PLANE", "OPERATOR", "mesh.primitive_plane_add()"),
    CatalogAction("add_cone", "ADD", "Конус", "Cone", "MESH_CONE", "OPERATOR", "mesh.primitive_cone_add()"),
    CatalogAction("add_torus", "ADD", "Тор", "Torus", "MESH_TORUS", "OPERATOR", "mesh.primitive_torus_add()"),
    *_variant_actions(
        "ADD",
        (
            ("add_empty", "PLAIN_AXES", "Пустышка: Оси", "Empty: Plain Axes", "EMPTY_AXIS"),
            ("add_empty_arrows", "ARROWS", "Пустышка: Стрелки", "Empty: Arrows", "EMPTY_ARROWS"),
            ("add_empty_single_arrow", "SINGLE_ARROW", "Пустышка: Одна стрелка", "Empty: Single Arrow", "EMPTY_SINGLE_ARROW"),
            ("add_empty_circle", "CIRCLE", "Пустышка: Круг", "Empty: Circle", "MESH_CIRCLE"),
            ("add_empty_cube", "CUBE", "Пустышка: Куб", "Empty: Cube", "MESH_CUBE"),
            ("add_empty_sphere", "SPHERE", "Пустышка: Сфера", "Empty: Sphere", "MESH_UVSPHERE"),
            ("add_empty_cone", "CONE", "Пустышка: Конус", "Empty: Cone", "MESH_CONE"),
            ("add_empty_image", "IMAGE", "Пустышка: Изображение", "Empty: Image", "IMAGE_DATA"),
        ),
        "object.empty_add(type='{value}')",
    ),

    CatalogAction("move", "TRANSFORM", "Переместить", "Move", "MOUSE_MOVE", "OPERATOR", "transform.translate()"),
    CatalogAction("rotate", "TRANSFORM", "Вращать", "Rotate", "GESTURE_ROTATE", "OPERATOR", "transform.rotate()"),
    CatalogAction("scale", "TRANSFORM", "Масштабировать", "Scale", "ARROW_LEFTRIGHT", "OPERATOR", "transform.resize()"),
    CatalogAction("mirror", "TRANSFORM", "Отразить", "Mirror", "MOD_MIRROR", "OPERATOR", "transform.mirror()"),
    CatalogAction("clear_location", "TRANSFORM", "Сбросить позицию", "Clear Location", "X", "OPERATOR", "object.location_clear()"),
    CatalogAction("clear_rotation", "TRANSFORM", "Сбросить вращение", "Clear Rotation", "X", "OPERATOR", "object.rotation_clear()"),
    CatalogAction("clear_scale", "TRANSFORM", "Сбросить масштаб", "Clear Scale", "X", "OPERATOR", "object.scale_clear()"),
    CatalogAction("apply_transforms", "TRANSFORM", "Применить трансформации", "Apply Transforms", "CHECKMARK", "OPERATOR", "object.transform_apply(location=True, rotation=True, scale=True)", "EXEC_DEFAULT"),
    CatalogAction("orientation_global", "TRANSFORM", "Ориентация: Глобальная", "Orientation: Global", "ORIENTATION_GLOBAL", "OPERATOR", "transform.select_orientation(orientation='GLOBAL')", "EXEC_DEFAULT"),
    CatalogAction("orientation_local", "TRANSFORM", "Ориентация: Локальная", "Orientation: Local", "ORIENTATION_LOCAL", "OPERATOR", "transform.select_orientation(orientation='LOCAL')", "EXEC_DEFAULT"),
    CatalogAction("orientation_normal", "TRANSFORM", "Ориентация: Нормаль", "Orientation: Normal", "ORIENTATION_NORMAL", "OPERATOR", "transform.select_orientation(orientation='NORMAL')", "EXEC_DEFAULT"),
    CatalogAction("orientation_gimbal", "TRANSFORM", "Ориентация: Кардан", "Orientation: Gimbal", "ORIENTATION_GIMBAL", "OPERATOR", "transform.select_orientation(orientation='GIMBAL')", "EXEC_DEFAULT"),
    CatalogAction("orientation_view", "TRANSFORM", "Ориентация: Вид", "Orientation: View", "ORIENTATION_VIEW", "OPERATOR", "transform.select_orientation(orientation='VIEW')", "EXEC_DEFAULT"),
    CatalogAction("orientation_cursor", "TRANSFORM", "Ориентация: Курсор", "Orientation: Cursor", "ORIENTATION_CURSOR", "OPERATOR", "transform.select_orientation(orientation='CURSOR')", "EXEC_DEFAULT"),
    CatalogAction("orientation_parent", "TRANSFORM", "Ориентация: Родитель", "Orientation: Parent", "ORIENTATION_PARENT", "OPERATOR", "transform.select_orientation(orientation='PARENT')", "EXEC_DEFAULT"),
    *_variant_actions(
        "TRANSFORM",
        (
            ("pivot_bounding_box", "BOUNDING_BOX_CENTER", "Pivot: Центр габаритов", "Pivot: Bounding Box Center", "PIVOT_BOUNDBOX"),
            ("pivot_cursor", "CURSOR", "Pivot: 3D-курсор", "Pivot: 3D Cursor", "PIVOT_CURSOR"),
            ("pivot_individual", "INDIVIDUAL_ORIGINS", "Pivot: Отдельные центры", "Pivot: Individual Origins", "PIVOT_INDIVIDUAL"),
            ("pivot_median", "MEDIAN_POINT", "Pivot: Медианная точка", "Pivot: Median Point", "PIVOT_MEDIAN"),
            ("pivot_active", "ACTIVE_ELEMENT", "Pivot: Активный элемент", "Pivot: Active Element", "PIVOT_ACTIVE"),
        ),
        "wm.context_set_enum(data_path='scene.tool_settings.transform_pivot_point', value='{value}')",
    ),
    *_variant_actions(
        "TRANSFORM",
        (
            ("falloff_smooth", "SMOOTH", "Спад: Плавный", "Falloff: Smooth", "SMOOTHCURVE"),
            ("falloff_sphere", "SPHERE", "Спад: Сфера", "Falloff: Sphere", "SPHERECURVE"),
            ("falloff_root", "ROOT", "Спад: Корень", "Falloff: Root", "ROOTCURVE"),
            ("falloff_inverse_square", "INVERSE_SQUARE", "Спад: Обратный квадрат", "Falloff: Inverse Square", "INVERSESQUARECURVE"),
            ("falloff_sharp", "SHARP", "Спад: Резкий", "Falloff: Sharp", "SHARPCURVE"),
            ("falloff_linear", "LINEAR", "Спад: Линейный", "Falloff: Linear", "LINCURVE"),
            ("falloff_constant", "CONSTANT", "Спад: Постоянный", "Falloff: Constant", "NOCURVE"),
            ("falloff_random", "RANDOM", "Спад: Случайный", "Falloff: Random", "RNDCURVE"),
        ),
        "wm.context_set_enum(data_path='scene.tool_settings.proportional_edit_falloff', value='{value}')",
    ),

    CatalogAction("delete_object", "OBJECT", "Удалить", "Delete", "TRASH", "OPERATOR", "object.delete()"),
    CatalogAction("duplicate_object", "OBJECT", "Дублировать", "Duplicate", "DUPLICATE", "OPERATOR", "object.duplicate_move()"),
    CatalogAction("join_objects", "OBJECT", "Объединить", "Join", "AUTOMERGE_ON", "OPERATOR", "object.join()", "EXEC_DEFAULT"),
    CatalogAction("shade_smooth", "OBJECT", "Гладкое затенение", "Shade Smooth", "SHADING_RENDERED", "OPERATOR", "object.shade_smooth()", "EXEC_DEFAULT"),
    CatalogAction("shade_flat", "OBJECT", "Плоское затенение", "Shade Flat", "SHADING_SOLID", "OPERATOR", "object.shade_flat()", "EXEC_DEFAULT"),
    *_variant_actions(
        "OBJECT",
        (
            ("geometry_to_origin", "GEOMETRY_ORIGIN", "Геометрию к Origin", "Geometry to Origin", "OBJECT_ORIGIN"),
            ("origin_geometry", "ORIGIN_GEOMETRY", "Origin в геометрию", "Origin to Geometry", "OBJECT_ORIGIN"),
            ("origin_cursor", "ORIGIN_CURSOR", "Origin к 3D-курсору", "Origin to 3D Cursor", "PIVOT_CURSOR"),
            ("origin_center_mass_surface", "ORIGIN_CENTER_OF_MASS", "Origin в центр массы (поверхность)", "Origin to Center of Mass (Surface)", "OBJECT_ORIGIN"),
            ("origin_center_mass_volume", "ORIGIN_CENTER_OF_VOLUME", "Origin в центр массы (объём)", "Origin to Center of Mass (Volume)", "OBJECT_ORIGIN"),
        ),
        "object.origin_set(type='{value}', center='MEDIAN')",
    ),
    *_variant_actions(
        "OBJECT",
        _convert_variants(),
        "object.convert(target='{value}')",
    ),
    *_variant_actions(
        "OBJECT",
        (
            ("mode_object", "OBJECT", "Режим: Объект", "Mode: Object", "OBJECT_DATAMODE"),
            ("mode_edit", "EDIT", "Режим: Редактирование", "Mode: Edit", "EDITMODE_HLT"),
            ("mode_pose", "POSE", "Режим: Поза", "Mode: Pose", "POSE_HLT"),
        ),
        "object.mode_set(mode='{value}')",
    ),
    *_variant_actions(
        "PAINT",
        (
            ("mode_vertex_paint", "VERTEX_PAINT", "Режим: Рисование вершин", "Mode: Vertex Paint", "VPAINT_HLT"),
            ("mode_weight_paint", "WEIGHT_PAINT", "Режим: Рисование весов", "Mode: Weight Paint", "WPAINT_HLT"),
            ("mode_texture_paint", "TEXTURE_PAINT", "Режим: Рисование текстуры", "Mode: Texture Paint", "TPAINT_HLT"),
        ),
        "object.mode_set(mode='{value}')",
    ),
    CatalogAction(
        "paint_flip_colors",
        "PAINT",
        "Поменять цвета местами",
        "Swap Colors",
        "FILE_REFRESH",
        "OPERATOR",
        "paint.brush_colors_flip()",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "paint_sample_color",
        "PAINT",
        "Взять образец цвета",
        "Sample Color",
        "EYEDROPPER",
        "OPERATOR",
        "paint.sample_color()",
    ),
    CatalogAction(
        "mode_sculpt",
        "SCULPT",
        "Режим: Скульптинг",
        "Mode: Sculpt",
        "SCULPTMODE_HLT",
        "OPERATOR",
        "object.mode_set(mode='SCULPT')",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_voxel_remesh",
        "SCULPT",
        "Воксельный ремеш",
        "Voxel Remesh",
        "MOD_REMESH",
        "OPERATOR",
        "object.voxel_remesh()",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_voxel_size",
        "SCULPT",
        "Размер вокселя",
        "Edit Voxel Size",
        "MOD_REMESH",
        "OPERATOR",
        "object.voxel_size_edit()",
    ),
    CatalogAction(
        "sculpt_dyntopo_toggle",
        "SCULPT",
        "Динамическая топология",
        "Dynamic Topology",
        "SCULPT_DYNTOPO",
        "OPERATOR",
        "sculpt.dynamic_topology_toggle()",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_symmetrize",
        "SCULPT",
        "Симметризовать",
        "Symmetrize",
        "MOD_MIRROR",
        "OPERATOR",
        "sculpt.symmetrize()",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_mask_fill",
        "SCULPT",
        "Заполнить маску",
        "Fill Mask",
        "MOD_MASK",
        "OPERATOR",
        "paint.mask_flood_fill(mode='VALUE', value=1.0)",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_mask_clear",
        "SCULPT",
        "Очистить маску",
        "Clear Mask",
        "MOD_MASK",
        "OPERATOR",
        "paint.mask_flood_fill(mode='VALUE', value=0.0)",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_mask_invert",
        "SCULPT",
        "Инвертировать маску",
        "Invert Mask",
        "MOD_MASK",
        "OPERATOR",
        "paint.mask_flood_fill(mode='INVERT')",
        "EXEC_DEFAULT",
    ),
    CatalogAction(
        "sculpt_mirror_x",
        "SCULPT",
        "Симметрия по X",
        "Mirror X",
        "MOD_MIRROR",
        "PROPERTY",
        "context.object.data.use_mirror_x",
    ),

    CatalogAction("mesh_extrude", "MESH", "Выдавить", "Extrude", "MOD_SOLIDIFY", "OPERATOR", "mesh.extrude_region_move()"),
    CatalogAction("mesh_inset", "MESH", "Вставка граней", "Inset Faces", "FACESEL", "OPERATOR", "mesh.inset()"),
    CatalogAction("mesh_bevel", "MESH", "Фаска", "Bevel", "MOD_BEVEL", "OPERATOR", "mesh.bevel()"),
    CatalogAction("mesh_loop_cut", "MESH", "Разрез петлёй", "Loop Cut and Slide", "LOOP_FORWARDS", "OPERATOR", "mesh.loopcut_slide()"),
    CatalogAction("mesh_subdivide", "MESH", "Подразделить", "Subdivide", "MOD_SUBSURF", "OPERATOR", "mesh.subdivide()"),
    CatalogAction("mesh_dissolve", "MESH", "Растворить вершины", "Dissolve Vertices", "REMOVE", "OPERATOR", "mesh.dissolve_verts()", "EXEC_DEFAULT"),
    CatalogAction("mesh_delete", "MESH", "Удалить элементы", "Delete Elements", "TRASH", "OPERATOR", "mesh.delete()"),
    CatalogAction("mesh_bevel_vertices", "MESH", "Фаска вершин", "Bevel Vertices", "MOD_BEVEL", "OPERATOR", "mesh.bevel(affect='VERTICES')"),
    CatalogAction("mesh_bevel_edges", "MESH", "Фаска рёбер", "Bevel Edges", "MOD_BEVEL", "OPERATOR", "mesh.bevel(affect='EDGES')"),
    CatalogAction(
        "mesh_mirror_x_clean_seam",
        "MESH",
        "Зеркало X от курсора + удалить стык",
        "Mirror X from Cursor + Clean Seam",
        "MOD_MIRROR",
        "OPERATOR",
        "pie_customizer.add_mirror_x_clean_seam()",
        "EXEC_DEFAULT",
    ),
    *_variant_actions(
        "MESH",
        (
            ("mesh_merge_center", "CENTER", "Объединить в центре", "Merge at Center", "AUTOMERGE_ON"),
            ("mesh_merge_cursor", "CURSOR", "Объединить у курсора", "Merge at Cursor", "PIVOT_CURSOR"),
            ("mesh_merge_collapse", "COLLAPSE", "Схлопнуть", "Collapse", "AUTOMERGE_ON"),
        ),
        "mesh.merge(type='{value}')",
    ),
    *_variant_actions(
        "MESH",
        (
            ("mesh_delete_vertices", "VERT", "Удалить вершины", "Delete Vertices", "VERTEXSEL"),
            ("mesh_delete_edges", "EDGE", "Удалить рёбра", "Delete Edges", "EDGESEL"),
            ("mesh_delete_faces", "FACE", "Удалить грани", "Delete Faces", "FACESEL"),
            ("mesh_delete_edges_faces", "EDGE_FACE", "Удалить только рёбра и грани", "Delete Only Edges & Faces", "EDGESEL"),
            ("mesh_delete_only_faces", "ONLY_FACE", "Удалить только грани", "Delete Only Faces", "FACESEL"),
        ),
        "mesh.delete(type='{value}')",
    ),
    *_variant_actions(
        "MESH",
        (
            ("select_mode_vertex", "VERT", "Выделение: Вершины", "Selection Mode: Vertex", "VERTEXSEL"),
            ("select_mode_edge", "EDGE", "Выделение: Рёбра", "Selection Mode: Edge", "EDGESEL"),
            ("select_mode_face", "FACE", "Выделение: Грани", "Selection Mode: Face", "FACESEL"),
        ),
        "mesh.select_mode(type='{value}', action='ENABLE')",
    ),

    CatalogAction("select_all_objects", "SELECT", "Все объекты", "All Objects", "RESTRICT_SELECT_OFF", "OPERATOR", "object.select_all(action='SELECT')", "EXEC_DEFAULT"),
    CatalogAction("deselect_all_objects", "SELECT", "Снять выделение объектов", "Deselect Objects", "X", "OPERATOR", "object.select_all(action='DESELECT')", "EXEC_DEFAULT"),
    CatalogAction("invert_objects", "SELECT", "Инвертировать объекты", "Invert Objects", "ARROW_LEFTRIGHT", "OPERATOR", "object.select_all(action='INVERT')", "EXEC_DEFAULT"),
    CatalogAction("toggle_objects", "SELECT", "Переключить выделение объектов", "Toggle Object Selection", "RESTRICT_SELECT_OFF", "OPERATOR", "object.select_all(action='TOGGLE')", "EXEC_DEFAULT"),
    CatalogAction("select_all_mesh", "SELECT", "Вся сетка", "All Mesh Elements", "VERTEXSEL", "OPERATOR", "mesh.select_all(action='SELECT')", "EXEC_DEFAULT"),
    CatalogAction("deselect_all_mesh", "SELECT", "Снять выделение сетки", "Deselect Mesh", "X", "OPERATOR", "mesh.select_all(action='DESELECT')", "EXEC_DEFAULT"),
    CatalogAction("invert_mesh", "SELECT", "Инвертировать сетку", "Invert Mesh", "ARROW_LEFTRIGHT", "OPERATOR", "mesh.select_all(action='INVERT')", "EXEC_DEFAULT"),
    CatalogAction("toggle_mesh", "SELECT", "Переключить выделение сетки", "Toggle Mesh Selection", "VERTEXSEL", "OPERATOR", "mesh.select_all(action='TOGGLE')", "EXEC_DEFAULT"),
    CatalogAction("select_more", "SELECT", "Выделить больше", "Select More", "ADD", "OPERATOR", "mesh.select_more()", "EXEC_DEFAULT"),
    CatalogAction("select_less", "SELECT", "Выделить меньше", "Select Less", "REMOVE", "OPERATOR", "mesh.select_less()", "EXEC_DEFAULT"),

    CatalogAction("view_selected", "VIEW", "Показать выделенное", "Frame Selected", "VIEWZOOM", "OPERATOR", "view3d.view_selected()"),
    CatalogAction("view_all", "VIEW", "Показать всё", "Frame All", "HOME", "OPERATOR", "view3d.view_all(center=False)"),
    CatalogAction("camera_view", "VIEW", "Вид из камеры", "Camera View", "CAMERA_DATA", "OPERATOR", "view3d.view_camera()"),
    CatalogAction("perspective_toggle", "VIEW", "Перспектива / Орто", "Perspective / Ortho", "VIEW_PERSPECTIVE", "OPERATOR", "view3d.view_persportho()"),
    CatalogAction("local_view", "VIEW", "Локальный вид", "Local View", "HIDE_OFF", "OPERATOR", "view3d.localview()"),
    CatalogAction("toggle_overlays", "VIEW", "Оверлеи", "Overlays", "OVERLAY", "PROPERTY", "context.space_data.overlay.show_overlays"),
    CatalogAction("search_menu", "VIEW", "Поиск Blender", "Blender Search", "VIEWZOOM", "OPERATOR", "wm.search_menu()"),
    CatalogAction("maximize_area", "VIEW", "Развернуть область", "Maximize Area", "FULLSCREEN_ENTER", "OPERATOR", "screen.screen_full_area()"),
    *_variant_actions(
        "VIEW",
        (
            ("view_left", "LEFT", "Вид: Слева", "View: Left", "AXIS_SIDE"),
            ("view_right", "RIGHT", "Вид: Справа", "View: Right", "AXIS_SIDE"),
            ("view_bottom", "BOTTOM", "Вид: Снизу", "View: Bottom", "AXIS_TOP"),
            ("view_top", "TOP", "Вид: Сверху", "View: Top", "AXIS_TOP"),
            ("view_front", "FRONT", "Вид: Спереди", "View: Front", "AXIS_FRONT"),
            ("view_back", "BACK", "Вид: Сзади", "View: Back", "AXIS_FRONT"),
        ),
        "view3d.view_axis(type='{value}')",
    ),
    *_variant_actions(
        "VIEW",
        (
            ("shading_wireframe", "WIREFRAME", "Затенение: Каркас", "Shading: Wireframe", "SHADING_WIRE"),
            ("shading_solid", "SOLID", "Затенение: Сплошное", "Shading: Solid", "SHADING_SOLID"),
            ("shading_material", "MATERIAL", "Затенение: Материал", "Shading: Material Preview", "SHADING_TEXTURE"),
            ("shading_rendered", "RENDERED", "Затенение: Рендер", "Shading: Rendered", "SHADING_RENDERED"),
        ),
        "wm.context_set_enum(data_path='space_data.shading.type', value='{value}')",
    ),
)


SNAPPING_VALUE_ACTIONS = (
    *_tool_settings_value_actions(
        "TRANSFORM",
        "transform_snapping",
        "snap_base",
        (
            ("closest", "snap_target", "CLOSEST", "База привязки: Ближайшая", "Snap Base: Closest", "SNAP_ON"),
            ("center", "snap_target", "CENTER", "База привязки: Центр", "Snap Base: Center", "SNAP_ON"),
            ("median", "snap_target", "MEDIAN", "База привязки: Медиана", "Snap Base: Median", "SNAP_MIDPOINT"),
            ("active", "snap_target", "ACTIVE", "База привязки: Активный", "Snap Base: Active", "EDITMODE_HLT"),
        ),
    ),
    *_tool_settings_value_actions(
        "TRANSFORM",
        "transform_snapping",
        "snap_target",
        (
            ("increment", "snap_elements_base", {"INCREMENT"}, "Цель привязки: Шаг", "Snap Target: Increment", "SNAP_INCREMENT"),
            ("grid", "snap_elements_base", {"GRID"}, "Цель привязки: Сетка", "Snap Target: Grid", "SNAP_GRID"),
            ("vertex", "snap_elements_base", {"VERTEX"}, "Цель привязки: Вершина", "Snap Target: Vertex", "SNAP_VERTEX"),
            ("edge", "snap_elements_base", {"EDGE"}, "Цель привязки: Ребро", "Snap Target: Edge", "SNAP_EDGE"),
            ("face", "snap_elements_base", {"FACE"}, "Цель привязки: Грань", "Snap Target: Face", "SNAP_FACE"),
            ("volume", "snap_elements_base", {"VOLUME"}, "Цель привязки: Объём", "Snap Target: Volume", "SNAP_VOLUME"),
            ("edge_center", "snap_elements_base", {"EDGE_MIDPOINT"}, "Цель привязки: Центр ребра", "Snap Target: Edge Center", "SNAP_MIDPOINT"),
            ("edge_perpendicular", "snap_elements_base", {"EDGE_PERPENDICULAR"}, "Цель привязки: Перпендикуляр ребра", "Snap Target: Edge Perpendicular", "SNAP_PERPENDICULAR"),
            ("face_center", "snap_elements_base", {"FACE_MIDPOINT"}, "Цель привязки: Центр грани", "Snap Target: Face Center", "SNAP_FACE_CENTER"),
        ),
    ),
    *_tool_settings_value_actions(
        "TRANSFORM",
        "transform_snapping",
        "snap_individual",
        (
            ("face_project", "snap_elements_individual", {"FACE_PROJECT"}, "Индивидуальная привязка: Проекция на грань", "Individual Snap: Face Project", "SNAP_FACE"),
            ("face_nearest", "snap_elements_individual", {"FACE_NEAREST"}, "Индивидуальная привязка: Ближайшая грань", "Individual Snap: Face Nearest", "MOD_SHRINKWRAP"),
        ),
    ),
    *_tool_settings_value_actions(
        "TRANSFORM",
        "transform_snapping",
        "snap_rotation_increment",
        (
            ("standard", "snap_angle_increment_3d", 0.08726646259971647, "Шаг вращения: 5°", "Rotation Increment: 5°", "DRIVER_ROTATIONAL_DIFFERENCE"),
            ("precision", "snap_angle_increment_3d_precision", 0.017453292519943295, "Точный шаг вращения: 1°", "Precision Rotation Increment: 1°", "DRIVER_ROTATIONAL_DIFFERENCE"),
        ),
    ),
)


VIEWPORT_TOGGLE_ACTIONS = (
    *_property_actions(
        "VIEW",
        "view_overlay_guides",
        "overlay_guides",
        "context.space_data.overlay",
        (
            ("ortho_grid", "show_ortho_grid", "Оверлеи: Ортографическая сетка", "Overlay: Orthographic Grid", "GRID"),
            ("floor", "show_floor", "Оверлеи: Сетка пола", "Overlay: Floor Grid", "GRID"),
            ("axis_x", "show_axis_x", "Оверлеи: Ось X", "Overlay: X Axis", "EVENT_X"),
            ("axis_y", "show_axis_y", "Оверлеи: Ось Y", "Overlay: Y Axis", "EVENT_Y"),
            ("axis_z", "show_axis_z", "Оверлеи: Ось Z", "Overlay: Z Axis", "EVENT_Z"),
            ("cursor", "show_cursor", "Оверлеи: 3D-курсор", "Overlay: 3D Cursor", "PIVOT_CURSOR"),
            ("annotation", "show_annotation", "Оверлеи: Аннотации", "Overlay: Annotations", "GREASEPENCIL"),
            ("camera_guides", "show_camera_guides", "Оверлеи: Направляющие камеры", "Overlay: Camera Guides", "CAMERA_DATA"),
            ("reference_spheres", "show_look_dev", "Оверлеи: Эталонные сферы", "Overlay: Reference Spheres", "MATERIAL"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_overlay_info",
        "overlay_info",
        "context.space_data.overlay",
        (
            ("text", "show_text", "Оверлеи: Информация", "Overlay: Text Info", "INFO"),
            ("statistics", "show_stats", "Оверлеи: Статистика", "Overlay: Statistics", "STATUSBAR"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_overlay_objects",
        "overlay_objects",
        "context.space_data.overlay",
        (
            ("extras", "show_extras", "Оверлеи объектов: Дополнения", "Object Overlay: Extras", "EMPTY_AXIS"),
            ("light_colors", "show_light_colors", "Оверлеи объектов: Цвета источников света", "Object Overlay: Light Colors", "LIGHT"),
            ("relationships", "show_relationship_lines", "Оверлеи объектов: Линии связей", "Object Overlay: Relationship Lines", "LINKED"),
            ("outline", "show_outline_selected", "Оверлеи объектов: Контур выделенного", "Object Overlay: Outline Selected", "RESTRICT_SELECT_OFF"),
            ("bones", "show_bones", "Оверлеи объектов: Кости", "Object Overlay: Bones", "BONE_DATA"),
            ("motion_paths", "show_motion_paths", "Оверлеи объектов: Пути движения", "Object Overlay: Motion Paths", "ANIM_DATA"),
            ("origins", "show_object_origins", "Оверлеи объектов: Центры", "Object Overlay: Origins", "OBJECT_ORIGIN"),
            ("origins_all", "show_object_origins_all", "Оверлеи объектов: Все центры", "Object Overlay: All Origins", "OBJECT_ORIGIN"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_overlay_geometry",
        "overlay_geometry",
        "context.space_data.overlay",
        (
            ("wireframes", "show_wireframes", "Оверлеи геометрии: Каркас", "Geometry Overlay: Wireframe", "SHADING_WIRE"),
            ("fade_inactive", "show_fade_inactive", "Оверлеи геометрии: Затемнить неактивное", "Geometry Overlay: Fade Inactive", "GHOST_ENABLED"),
            ("face_orientation", "show_face_orientation", "Оверлеи геометрии: Ориентация граней", "Geometry Overlay: Face Orientation", "NORMALS_FACE"),
        ),
    ),
    *_property_actions(
        "MESH",
        "view_overlay_mesh",
        "overlay_mesh",
        "context.space_data.overlay",
        (
            ("faces", "show_faces", "Сетка: Грани", "Mesh Overlay: Faces", "FACESEL"),
            ("face_centers", "show_face_center", "Сетка: Центры граней", "Mesh Overlay: Face Centers", "SNAP_FACE_CENTER"),
            ("creases", "show_edge_crease", "Сетка: Складки", "Mesh Overlay: Creases", "EDGE_CREASE"),
            ("bevel_weights", "show_edge_bevel_weight", "Сетка: Веса фаски", "Mesh Overlay: Bevel Weights", "EDGE_BEVEL"),
            ("seams", "show_edge_seams", "Сетка: Швы", "Mesh Overlay: Seams", "EDGE_SEAM"),
            ("sharp", "show_edge_sharp", "Сетка: Резкие рёбра", "Mesh Overlay: Sharp Edges", "SHARPCURVE"),
            ("indices", "show_extra_indices", "Сетка: Индексы", "Mesh Overlay: Indices", "LINENUMBERS_ON"),
            ("retopology", "show_retopology", "Сетка: Ретопология", "Mesh Overlay: Retopology", "MOD_SHRINKWRAP"),
            ("weights", "show_weight", "Сетка: Веса вершин", "Mesh Overlay: Vertex Weights", "GROUP_VERTEX"),
            ("analysis", "show_statvis", "Сетка: Анализ", "Mesh Overlay: Mesh Analysis", "MOD_DATA_TRANSFER"),
        ),
    ),
    *_property_actions(
        "MESH",
        "view_overlay_measurements",
        "overlay_measurements",
        "context.space_data.overlay",
        (
            ("edge_length", "show_extra_edge_length", "Измерения: Длина рёбер", "Measurements: Edge Length", "DRIVER_DISTANCE"),
            ("edge_angle", "show_extra_edge_angle", "Измерения: Угол рёбер", "Measurements: Edge Angle", "DRIVER_ROTATIONAL_DIFFERENCE"),
            ("face_angle", "show_extra_face_angle", "Измерения: Угол граней", "Measurements: Face Angles", "DRIVER_ROTATIONAL_DIFFERENCE"),
            ("face_area", "show_extra_face_area", "Измерения: Площадь граней", "Measurements: Face Area", "AREA_DOCK"),
        ),
    ),
    *_property_actions(
        "MESH",
        "view_overlay_normals",
        "overlay_normals",
        "context.space_data.overlay",
        (
            ("vertex", "show_vertex_normals", "Нормали: Вершины", "Normals: Vertex", "NORMALS_VERTEX"),
            ("split", "show_split_normals", "Нормали: Разделённые", "Normals: Split", "NORMALS_VERTEX_FACE"),
            ("face", "show_face_normals", "Нормали: Грани", "Normals: Face", "NORMALS_FACE"),
            ("constant_size", "use_normals_constant_screen_size", "Нормали: Постоянный размер", "Normals: Constant Screen Size", "FIXED_SIZE"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_overlay_modes",
        "overlay_modes",
        "context.space_data.overlay",
        (
            ("bone_xray", "show_xray_bone", "Режимы: Кости сквозь объекты", "Mode Overlay: Bone X-Ray", "XRAY"),
            ("paint_wire", "show_paint_wire", "Режимы: Каркас рисования", "Mode Overlay: Paint Wire", "VPAINT_HLT"),
            ("weight_contours", "show_wpaint_contours", "Режимы: Контуры весов", "Mode Overlay: Weight Contours", "WPAINT_HLT"),
            ("curve_normals", "show_curve_normals", "Режимы: Нормали кривой", "Mode Overlay: Curve Normals", "CURVE_DATA"),
            ("viewer_node", "show_viewer_attribute", "Режимы: Viewer Node", "Mode Overlay: Viewer Node", "NODE"),
        ),
    ),
    *_property_actions(
        "SCULPT",
        "sculpt_display",
        "sculpt_overlay",
        "context.space_data.overlay",
        (
            ("mask", "show_sculpt_mask", "Отображать маску", "Show Sculpt Mask", "SCULPTMODE_HLT"),
            ("face_sets", "show_sculpt_face_sets", "Отображать наборы граней", "Show Face Sets", "FACESEL"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_regions",
        "viewport_region",
        "context.space_data",
        (
            ("header", "show_region_header", "3D View: Заголовок", "3D View: Header", "TOPBAR"),
            ("tool_header", "show_region_tool_header", "3D View: Настройки инструмента", "3D View: Tool Settings", "TOOL_SETTINGS"),
            ("toolbar", "show_region_toolbar", "3D View: Панель инструментов", "3D View: Toolbar", "TOOL_SETTINGS"),
            ("sidebar", "show_region_ui", "3D View: Боковая панель", "3D View: Sidebar", "SIDEBAR"),
            ("asset_shelf", "show_region_asset_shelf", "3D View: Полка ассетов", "3D View: Asset Shelf", "ASSET_MANAGER"),
            ("hud", "show_region_hud", "3D View: Последняя операция", "3D View: Adjust Last Operation", "PREFERENCES"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_gizmos",
        "viewport_gizmo",
        "context.space_data",
        (
            ("all", "show_gizmo", "Gizmo: Все", "Gizmo: All", "GIZMO"),
            ("navigate", "show_gizmo_navigate", "Gizmo: Навигация", "Gizmo: Navigate", "ORIENTATION_VIEW"),
            ("tools", "show_gizmo_tool", "Gizmo: Активные инструменты", "Gizmo: Active Tools", "TOOL_SETTINGS"),
            ("context", "show_gizmo_context", "Gizmo: Активный объект", "Gizmo: Active Object", "OBJECT_DATA"),
            ("move", "show_gizmo_object_translate", "Gizmo: Перемещение", "Gizmo: Move", "MOUSE_MOVE"),
            ("rotate", "show_gizmo_object_rotate", "Gizmo: Вращение", "Gizmo: Rotate", "GESTURE_ROTATE"),
            ("scale", "show_gizmo_object_scale", "Gizmo: Масштаб", "Gizmo: Scale", "ARROW_LEFTRIGHT"),
            ("empty_image", "show_gizmo_empty_image", "Gizmo: Изображения-пустышки", "Gizmo: Empty Images", "IMAGE_DATA"),
            ("force_field", "show_gizmo_empty_force_field", "Gizmo: Силовые поля", "Gizmo: Force Fields", "FORCE_FORCE"),
            ("light_size", "show_gizmo_light_size", "Gizmo: Размер света", "Gizmo: Light Size", "LIGHT"),
            ("camera_lens", "show_gizmo_camera_lens", "Gizmo: Объектив камеры", "Gizmo: Camera Lens", "CAMERA_DATA"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_shading_options",
        "viewport_shading",
        "context.space_data.shading",
        (
            ("outline", "show_object_outline", "Затенение: Контур объектов", "Shading: Object Outline", "SHADING_SOLID"),
            ("backface_culling", "show_backface_culling", "Затенение: Отсечение обратных граней", "Shading: Backface Culling", "FACESEL"),
            ("cavity", "show_cavity", "Затенение: Полости", "Shading: Cavity", "MATCAP_02"),
            ("shadows", "show_shadows", "Затенение: Тени", "Shading: Shadows", "MOD_SHADOW"),
            ("xray", "show_xray", "Затенение: Рентген", "Shading: X-Ray", "XRAY"),
            ("xray_wireframe", "show_xray_wireframe", "Затенение: Рентген каркаса", "Shading: Wireframe X-Ray", "SHADING_WIRE"),
            ("depth_of_field", "use_dof", "Затенение: Глубина резкости", "Shading: Depth of Field", "CAMERA_DATA"),
            ("scene_lights", "use_scene_lights", "Затенение: Свет сцены", "Shading: Scene Lights", "LIGHT"),
            ("scene_world", "use_scene_world", "Затенение: Мир сцены", "Shading: Scene World", "WORLD"),
            ("specular", "show_specular_highlight", "Затенение: Блики", "Shading: Specular Highlights", "SHADING_RENDERED"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_object_visibility",
        "object_visibility",
        "context.space_data",
        (
            ("mesh", "show_object_viewport_mesh", "Видимость: Сетки", "Visibility: Meshes", "MESH_DATA"),
            ("curve", "show_object_viewport_curve", "Видимость: Кривые", "Visibility: Curves", "CURVE_DATA"),
            ("surface", "show_object_viewport_surf", "Видимость: Поверхности", "Visibility: Surfaces", "SURFACE_DATA"),
            ("metaball", "show_object_viewport_meta", "Видимость: Метасферы", "Visibility: Metaballs", "META_DATA"),
            ("text", "show_object_viewport_font", "Видимость: Текст", "Visibility: Text", "FONT_DATA"),
            ("hair", "show_object_viewport_curves", "Видимость: Волосы", "Visibility: Hair Curves", "CURVES_DATA"),
            ("point_cloud", "show_object_viewport_pointcloud", "Видимость: Облака точек", "Visibility: Point Clouds", "POINTCLOUD_DATA"),
            ("volume", "show_object_viewport_volume", "Видимость: Объёмы", "Visibility: Volumes", "VOLUME_DATA"),
            ("armature", "show_object_viewport_armature", "Видимость: Арматуры", "Visibility: Armatures", "ARMATURE_DATA"),
            ("lattice", "show_object_viewport_lattice", "Видимость: Решётки", "Visibility: Lattices", "LATTICE_DATA"),
            ("empty", "show_object_viewport_empty", "Видимость: Пустышки", "Visibility: Empties", "EMPTY_AXIS"),
            ("grease_pencil", "show_object_viewport_grease_pencil", "Видимость: Grease Pencil", "Visibility: Grease Pencil", "GREASEPENCIL"),
            ("camera", "show_object_viewport_camera", "Видимость: Камеры", "Visibility: Cameras", "CAMERA_DATA"),
            ("light", "show_object_viewport_light", "Видимость: Источники света", "Visibility: Lights", "LIGHT"),
            ("speaker", "show_object_viewport_speaker", "Видимость: Динамики", "Visibility: Speakers", "SPEAKER"),
            ("light_probe", "show_object_viewport_light_probe", "Видимость: Зонды освещения", "Visibility: Light Probes", "LIGHTPROBE_SPHERE"),
        ),
    ),
    *_property_actions(
        "VIEW",
        "view_object_selectability",
        "object_selectability",
        "context.space_data",
        (
            ("mesh", "show_object_select_mesh", "Выделяемость: Сетки", "Selectable: Meshes", "MESH_DATA"),
            ("curve", "show_object_select_curve", "Выделяемость: Кривые", "Selectable: Curves", "CURVE_DATA"),
            ("surface", "show_object_select_surf", "Выделяемость: Поверхности", "Selectable: Surfaces", "SURFACE_DATA"),
            ("metaball", "show_object_select_meta", "Выделяемость: Метасферы", "Selectable: Metaballs", "META_DATA"),
            ("text", "show_object_select_font", "Выделяемость: Текст", "Selectable: Text", "FONT_DATA"),
            ("hair", "show_object_select_curves", "Выделяемость: Волосы", "Selectable: Hair Curves", "CURVES_DATA"),
            ("point_cloud", "show_object_select_pointcloud", "Выделяемость: Облака точек", "Selectable: Point Clouds", "POINTCLOUD_DATA"),
            ("volume", "show_object_select_volume", "Выделяемость: Объёмы", "Selectable: Volumes", "VOLUME_DATA"),
            ("armature", "show_object_select_armature", "Выделяемость: Арматуры", "Selectable: Armatures", "ARMATURE_DATA"),
            ("lattice", "show_object_select_lattice", "Выделяемость: Решётки", "Selectable: Lattices", "LATTICE_DATA"),
            ("empty", "show_object_select_empty", "Выделяемость: Пустышки", "Selectable: Empties", "EMPTY_AXIS"),
            ("grease_pencil", "show_object_select_grease_pencil", "Выделяемость: Grease Pencil", "Selectable: Grease Pencil", "GREASEPENCIL"),
            ("camera", "show_object_select_camera", "Выделяемость: Камеры", "Selectable: Cameras", "CAMERA_DATA"),
            ("light", "show_object_select_light", "Выделяемость: Источники света", "Selectable: Lights", "LIGHT"),
            ("speaker", "show_object_select_speaker", "Выделяемость: Динамики", "Selectable: Speakers", "SPEAKER"),
            ("light_probe", "show_object_select_light_probe", "Выделяемость: Зонды освещения", "Selectable: Light Probes", "LIGHTPROBE_SPHERE"),
        ),
    ),
    *_property_actions(
        "TRANSFORM",
        "transform_options",
        "transform_option",
        "context.scene.tool_settings",
        (
            ("origins", "use_transform_data_origin", "Трансформация: Только центры", "Transform: Affect Origins", "OBJECT_ORIGIN"),
            ("skip_children", "use_transform_skip_children", "Трансформация: Не затрагивать дочерние", "Transform: Skip Children", "CON_CHILDOF"),
            ("correct_faces", "use_transform_correct_face_attributes", "Трансформация: Корректировать атрибуты граней", "Transform: Correct Face Attributes", "FACESEL"),
            ("keep_connected", "use_transform_correct_keep_connected", "Трансформация: Сохранять соединение", "Transform: Keep Connected", "LINKED"),
            ("auto_merge", "use_mesh_automerge", "Сетка: Автообъединение", "Mesh: Auto Merge", "AUTOMERGE_ON"),
            ("auto_split", "use_mesh_automerge_and_split", "Сетка: Разделять рёбра и грани", "Mesh: Split Edges & Faces", "MOD_EDGESPLIT"),
        ),
    ),
    *_property_actions(
        "TRANSFORM",
        "transform_proportional",
        "proportional_option",
        "context.scene.tool_settings",
        (
            ("edit", "use_proportional_edit", "Пропорциональное редактирование: Edit Mode", "Proportional Editing: Edit Mode", "PROP_ON"),
            ("object", "use_proportional_edit_objects", "Пропорциональное редактирование: Object Mode", "Proportional Editing: Object Mode", "PROP_ON"),
            ("connected", "use_proportional_connected", "Пропорциональное: Только связанное", "Proportional Editing: Connected Only", "PROP_CON"),
            ("projected", "use_proportional_projected", "Пропорциональное: Проекция из вида", "Proportional Editing: Projected from View", "PROP_PROJECTED"),
        ),
    ),
    *_tool_settings_property_actions(
        "TRANSFORM",
        "transform_snapping",
        "snap_option",
        (
            ("enabled", "use_snap", "Привязка: Включить", "Snap: Enable", "SNAP_ON"),
            ("absolute_grid", "use_snap_grid_absolute", "Привязка: Абсолютный шаг", "Snap: Absolute Increment", "SNAP_INCREMENT"),
            ("same_target", "use_snap_to_same_target", "Привязка: К той же цели", "Snap: Same Target", "SNAP_ON"),
            ("peel_object", "use_snap_peel_object", "Привязка: Объект Peel", "Snap: Peel Object", "MOD_SHRINKWRAP"),
            ("align_rotation", "use_snap_align_rotation", "Привязка: Выровнять вращение по цели", "Snap: Align Rotation to Target", "ORIENTATION_NORMAL"),
            ("backface_culling", "use_snap_backface_culling", "Привязка: Отсечение обратных граней", "Snap: Backface Culling", "FACESEL"),
            ("active", "use_snap_self", "Выбор цели: Включая активный объект", "Target Selection: Include Active", "EDITMODE_HLT"),
            ("edited", "use_snap_edit", "Выбор цели: Включая редактируемые", "Target Selection: Include Edited", "OUTLINER_DATA_MESH"),
            ("nonedited", "use_snap_nonedit", "Выбор цели: Включая нередактируемые", "Target Selection: Include Non-Edited", "OUTLINER_OB_MESH"),
            ("selectable", "use_snap_selectable", "Выбор цели: Исключить невыделяемые", "Target Selection: Exclude Non-Selectable", "RESTRICT_SELECT_OFF"),
            ("translate", "use_snap_translate", "Влияние привязки: Перемещение", "Snap Affect: Move", "MOUSE_MOVE"),
            ("rotate", "use_snap_rotate", "Влияние привязки: Вращение", "Snap Affect: Rotate", "DRIVER_ROTATIONAL_DIFFERENCE"),
            ("scale", "use_snap_scale", "Влияние привязки: Масштаб", "Snap Affect: Scale", "ARROW_LEFTRIGHT"),
        ),
    ),
)


SEARCH_ACTIONS = ACTIONS + SNAPPING_VALUE_ACTIONS + VIEWPORT_TOGGLE_ACTIONS


_ACTIONS_BY_ID = {action.action_id: action for action in SEARCH_ACTIONS}


def actions_for_category(category: str) -> tuple[CatalogAction, ...]:
    return tuple(action for action in SEARCH_ACTIONS if action.category == category)


def action_by_id(action_id: str) -> CatalogAction | None:
    return _ACTIONS_BY_ID.get(action_id)


def action_label(action: CatalogAction, language: str) -> str:
    return action.label_en if language == "EN" else action.label_ru


def apply_action(slot, action: CatalogAction, language: str) -> None:
    slot.enabled = True
    slot.label = action_label(action, language)
    slot.icon = action.icon
    slot.slot_type = action.slot_type
    slot.command = action.command
    slot.operator_context = action.operator_context
