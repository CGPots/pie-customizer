"""Discover Blender operators, menus, and recent actions for the command browser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from .command_catalog import SEARCH_ACTIONS
from .ui_style import CATALOG_PAGE_SIZE


@dataclass(frozen=True)
class BrowserAction:
    token: str
    kind: str
    item_id: str
    group: str
    label: str
    description: str
    command: str
    icon: str
    slot_type: str
    operator_context: str = "INVOKE_DEFAULT"
    search_terms: str = ""


GROUP_LABELS = {
    "RU": {
        "add_empties": "Пустышки",
        "add_primitives": "Примитивы",
        "mesh_delete": "Удаление",
        "mesh_merge": "Объединение",
        "mesh_modeling": "Моделирование",
        "mesh_select_mode": "Режим выделения",
        "object_actions": "Основные действия",
        "object_convert": "Преобразование",
        "object_modifiers": "Модификаторы",
        "object_modes": "Режимы работы",
        "object_origin": "Origin",
        "object_shading": "Затенение",
        "grease_pencil_modifiers": "Модификаторы Grease Pencil",
        "physics_modifiers": "Физические модификаторы",
        "paint_actions": "Основные действия",
        "paint_modes": "Режимы рисования",
        "select_mesh": "Элементы сетки",
        "select_objects": "Объекты",
        "transform_basic": "Основные операции",
        "transform_falloff": "Спад пропорционального редактирования",
        "transform_orientations": "Ориентации",
        "transform_pivots": "Точки опоры",
        "transform_reset": "Сброс и применение",
        "view_axes": "Стандартные виды",
        "view_display": "Отображение и затенение",
        "view_gizmos": "Gizmo 3D View",
        "view_interface": "Интерфейс",
        "view_navigation": "Навигация и просмотр",
        "view_overlay_geometry": "Оверлеи: Геометрия",
        "view_overlay_guides": "Оверлеи: Направляющие",
        "view_overlay_info": "Оверлеи: Информация",
        "view_overlay_measurements": "Оверлеи: Измерения",
        "view_overlay_mesh": "Оверлеи: Редактирование сетки",
        "view_overlay_modes": "Оверлеи: Режимы работы",
        "view_overlay_normals": "Оверлеи: Нормали",
        "view_overlay_objects": "Оверлеи: Объекты",
        "view_object_selectability": "Выделяемость типов объектов",
        "view_object_visibility": "Видимость типов объектов",
        "view_regions": "Панели 3D View",
        "view_shading_options": "Параметры затенения",
        "transform_options": "Параметры трансформации",
        "transform_proportional": "Пропорциональное редактирование",
        "transform_snapping": "Параметры привязки",
        "action": "Редактор действий и ключевые кадры",
        "anim": "Инструменты анимации",
        "armature": "Арматура",
        "asset": "Ассеты и библиотеки",
        "bc": "BoxCutter",
        "bk": "BlenderKit",
        "blenderkit": "BlenderKit",
        "boid": "Рой частиц",
        "bpm": "Better Pie Menus",
        "brush": "Кисти",
        "buttons": "Редактор свойств",
        "cachefile": "Файлы кэша",
        "camera": "Камера",
        "cbl": "Cablerator",
        "clear": "Очистка",
        "clip": "Трекинг видео",
        "cloth": "Ткань",
        "collection": "Коллекции",
        "console": "Консоль",
        "constraint": "Ограничения",
        "curve": "Кривые",
        "curves": "Кривые волос",
        "curvetools": "Curve Tools",
        "cycles": "Cycles",
        "data": "Hard Ops: Проверка сетки",
        "dpaint": "Динамическое рисование",
        "ed": "Системные операции редактирования",
        "export_anim": "Экспорт анимации",
        "export_gcode_format": "Экспорт G-code",
        "export_scene": "Экспорт сцены",
        "export_svg_format": "Экспорт SVG",
        "export": "OctaneRender: Экспорт",
        "extensions": "Расширения",
        "file": "Файлы",
        "fluid": "Жидкость",
        "font": "Текстовые объекты",
        "geometry": "Атрибуты геометрии",
        "gizmogroup": "Гизмо",
        "gpencil": "Grease Pencil (старый)",
        "graph": "Редактор графиков",
        "grease_pencil": "Grease Pencil",
        "hardflow": "Hard Ops: Инструменты сетки",
        "hardflow_om": "Hard Ops: Инструменты объектов",
        "hops": "Hard Ops",
        "image": "Изображения",
        "import_anim": "Импорт анимации",
        "import_curve": "Импорт кривых",
        "import_scene": "Импорт сцены",
        "info": "Отчёты и история операций",
        "lattice": "Решётка",
        "light": "Свет",
        "magicsdf": "MagicSDF",
        "kitcad": "KitCAD",
        "make": "Hard Ops: Связи",
        "marker": "Маркеры",
        "mask": "Маски",
        "material": "Материалы",
        "mball": "Метасферы",
        "mesh": "Операции с сеткой",
        "nla": "Нелинейная анимация",
        "node": "Ноды",
        "object": "Действия с объектами",
        "octane": "OctaneRender",
        "octane_render_aov": "OctaneRender: Каналы вывода",
        "operator": "Better Pie Menus: Операторы",
        "outliner": "Структура сцены",
        "paint": "Рисование",
        "paintcurve": "Кривые кисти",
        "palette": "Палитры",
        "particle": "Частицы",
        "pie_customizer": "Pie Customizer",
        "pointcloud": "Облака точек",
        "pose": "Поза",
        "poselib": "Библиотека поз",
        "preferences": "Настройки Blender",
        "ptcache": "Кэш симуляций",
        "remove": "Удаление",
        "render": "Рендер",
        "rigidbody": "Физика твёрдых тел",
        "sculpt_actions": "Основные действия",
        "sculpt_brushes_curves": "Кисти кривых",
        "sculpt_brushes_general": "Кисти: Основные",
        "sculpt_brushes_grease_pencil": "Кисти Grease Pencil",
        "sculpt_brushes_paint": "Кисти: Рисование",
        "sculpt_brushes_simulation": "Кисти: Симуляция",
        "sculpt_display": "Отображение",
        "sculpt_masks": "Маски",
        "sculpt_remesh": "Ремеш",
        "sculpt_symmetry": "Симметрия",
        "paint_brushes_grease_pencil": "Кисти: Grease Pencil Draw",
        "paint_brushes_grease_pencil_vertex": "Кисти: Grease Pencil Vertex Paint",
        "paint_brushes_grease_pencil_weight": "Кисти: Grease Pencil Weight Paint",
        "paint_brushes_texture": "Кисти: Texture Paint",
        "paint_brushes_vertex": "Кисти: Vertex Paint",
        "paint_brushes_weight": "Кисти: Weight Paint",
        "scene": "Сцена",
        "screen": "Управление экраном",
        "script": "Скрипты",
        "sculpt": "Скульптинг",
        "sculpt_curves": "Скульптинг кривых",
        "sequencer": "Видеомонтаж",
        "sound": "Звук",
        "spreadsheet": "Таблица данных",
        "supadupafusion": "SupaDupaFusion",
        "surface": "Поверхности",
        "template": "Better Pie Menus: Шаблоны",
        "text": "Текстовый редактор",
        "text_editor": "Настройки текстового редактора",
        "texture": "Текстуры",
        "transform": "Инструменты трансформации",
        "ui": "Элементы интерфейса",
        "uilist": "Списки интерфейса",
        "unlink": "Hard Ops: Разрыв связей",
        "uv": "UV-развёртка",
        "view": "Better Pie Menus: Вид",
        "view2d": "Двумерный вид",
        "view3d": "Трёхмерный вид",
        "window": "Окно",
        "wm": "Общие команды",
        "workspace": "Рабочие пространства",
        "world": "Мир сцены",
    },
    "EN": {
        "action": "Action Editor & Keyframes",
        "add_empties": "Empties",
        "add_primitives": "Primitives",
        "anim": "Animation Tools",
        "asset": "Assets & Libraries",
        "mesh": "Mesh Operations",
        "mesh_delete": "Delete",
        "mesh_merge": "Merge",
        "mesh_modeling": "Modeling",
        "mesh_select_mode": "Selection Mode",
        "object": "Object Actions",
        "object_actions": "Basic Actions",
        "object_convert": "Conversion",
        "object_modifiers": "Modifiers",
        "object_modes": "Modes",
        "object_origin": "Origin",
        "object_shading": "Shading",
        "grease_pencil_modifiers": "Grease Pencil Modifiers",
        "physics_modifiers": "Physics Modifiers",
        "paint_actions": "Basic Actions",
        "paint_modes": "Paint Modes",
        "screen": "Screen Management",
        "select_mesh": "Mesh Elements",
        "select_objects": "Objects",
        "transform": "Transform Tools",
        "transform_basic": "Basic Operations",
        "transform_falloff": "Proportional Falloff",
        "transform_orientations": "Orientations",
        "transform_pivots": "Pivot Points",
        "transform_reset": "Reset & Apply",
        "view_axes": "Standard Views",
        "view_display": "Display & Shading",
        "view_gizmos": "3D View Gizmos",
        "view_interface": "Interface",
        "view_navigation": "Navigation & View",
        "view_overlay_geometry": "Overlays: Geometry",
        "view_overlay_guides": "Overlays: Guides",
        "view_overlay_info": "Overlays: Text Info",
        "view_overlay_measurements": "Overlays: Measurements",
        "view_overlay_mesh": "Overlays: Mesh Edit",
        "view_overlay_modes": "Overlays: Modes",
        "view_overlay_normals": "Overlays: Normals",
        "view_overlay_objects": "Overlays: Objects",
        "view_object_selectability": "Object Type Selectability",
        "view_object_visibility": "Object Type Visibility",
        "view_regions": "3D View Regions",
        "view_shading_options": "Shading Options",
        "transform_options": "Transform Options",
        "transform_proportional": "Proportional Editing",
        "transform_snapping": "Snapping Options",
        "bc": "BoxCutter",
        "bk": "BlenderKit",
        "blenderkit": "BlenderKit",
        "bpm": "Better Pie Menus",
        "cbl": "Cablerator",
        "curvetools": "Curve Tools",
        "data": "Hard Ops: Mesh Check",
        "dpaint": "Dynamic Paint",
        "ed": "Editing Utilities",
        "geometry": "Geometry Attributes",
        "gpencil": "Grease Pencil (Legacy)",
        "hardflow": "Hard Ops: Mesh Tools",
        "hardflow_om": "Hard Ops: Object Tools",
        "hops": "Hard Ops",
        "info": "Reports & Operator History",
        "kitcad": "KitCAD",
        "magicsdf": "MagicSDF",
        "nla": "Nonlinear Animation",
        "pie_customizer": "Pie Customizer",
        "ptcache": "Simulation Cache",
        "rigidbody": "Rigid Body Physics",
        "sculpt_actions": "Basic Actions",
        "sculpt_brushes_curves": "Curve Sculpt Brushes",
        "sculpt_brushes_general": "General Brushes",
        "sculpt_brushes_grease_pencil": "Grease Pencil Sculpt Brushes",
        "sculpt_brushes_paint": "Paint Brushes",
        "sculpt_brushes_simulation": "Simulation Brushes",
        "sculpt_display": "Display",
        "sculpt_masks": "Masks",
        "sculpt_remesh": "Remesh",
        "sculpt_symmetry": "Symmetry",
        "paint_brushes_grease_pencil": "Grease Pencil Draw Brushes",
        "paint_brushes_grease_pencil_vertex": "Grease Pencil Vertex Paint Brushes",
        "paint_brushes_grease_pencil_weight": "Grease Pencil Weight Paint Brushes",
        "paint_brushes_texture": "Texture Paint Brushes",
        "paint_brushes_vertex": "Vertex Paint Brushes",
        "paint_brushes_weight": "Weight Paint Brushes",
        "supadupafusion": "SupaDupaFusion",
        "octane": "OctaneRender",
        "octane_render_aov": "OctaneRender: Output Channels",
        "text": "Text Editor",
        "text_editor": "Text Editor Settings",
        "ui": "Interface Controls",
        "uilist": "Interface Lists",
        "uv": "UV Mapping",
        "view2d": "2D View",
        "view3d": "3D View",
        "wm": "General Commands",
        "world": "Scene World",
    },
}


OPERATOR_GROUP_ALIASES = {
    "bk": "blenderkit",
}

DISCOVERY_EXCLUDED_OPERATOR_IDS = {
    # Viewport Pie Menus sets this required string only from its own menu.
    "object.set_proportional_falloff",
    # This wrapper also expects its origin type to be injected by its own menu.
    "object.origin_set_any_mode",
}

DISCOVERY_EXCLUDED_OPERATOR_PREFIXES = (
    # Add-on implementation details must never be assignable as user actions.
    "pie_customizer.",
)

GROUP_ICONS = {
    "add_empties": "EMPTY_AXIS",
    "add_primitives": "MESH_CUBE",
    "mesh_delete": "TRASH",
    "mesh_merge": "AUTOMERGE_ON",
    "mesh_modeling": "MESH_DATA",
    "mesh_select_mode": "VERTEXSEL",
    "object_actions": "OBJECT_DATA",
    "object_convert": "FILE_REFRESH",
    "object_modifiers": "MODIFIER",
    "object_modes": "OBJECT_DATAMODE",
    "object_origin": "OBJECT_ORIGIN",
    "object_shading": "SHADING_RENDERED",
    "grease_pencil_modifiers": "GREASEPENCIL",
    "physics_modifiers": "RIGID_BODY",
    "paint_actions": "BRUSH_DATA",
    "paint_brushes_grease_pencil": "GREASEPENCIL",
    "paint_brushes_grease_pencil_vertex": "VPAINT_HLT",
    "paint_brushes_grease_pencil_weight": "WPAINT_HLT",
    "paint_brushes_texture": "TPAINT_HLT",
    "paint_brushes_vertex": "VPAINT_HLT",
    "paint_brushes_weight": "WPAINT_HLT",
    "paint_modes": "TPAINT_HLT",
    "sculpt_actions": "SCULPTMODE_HLT",
    "sculpt_brushes_curves": "CURVES",
    "sculpt_brushes_general": "BRUSH_DATA",
    "sculpt_brushes_grease_pencil": "GREASEPENCIL",
    "sculpt_brushes_paint": "BRUSH_DATA",
    "sculpt_brushes_simulation": "MOD_CLOTH",
    "sculpt_display": "OVERLAY",
    "sculpt_masks": "MOD_MASK",
    "sculpt_remesh": "MOD_REMESH",
    "sculpt_symmetry": "MOD_MIRROR",
    "select_mesh": "MESH_DATA",
    "select_objects": "OBJECT_DATA",
    "transform_basic": "ORIENTATION_GLOBAL",
    "transform_falloff": "SMOOTHCURVE",
    "transform_orientations": "ORIENTATION_GLOBAL",
    "transform_pivots": "PIVOT_BOUNDBOX",
    "transform_reset": "CHECKMARK",
    "view_axes": "AXIS_FRONT",
    "view_display": "SHADING_SOLID",
    "view_gizmos": "GIZMO",
    "view_interface": "WINDOW",
    "view_navigation": "VIEW3D",
    "view_overlay_geometry": "SHADING_WIRE",
    "view_overlay_guides": "GRID",
    "view_overlay_info": "INFO",
    "view_overlay_measurements": "DRIVER_DISTANCE",
    "view_overlay_mesh": "EDITMODE_HLT",
    "view_overlay_modes": "OVERLAY",
    "view_overlay_normals": "NORMALS_FACE",
    "view_overlay_objects": "OBJECT_DATA",
    "view_object_selectability": "RESTRICT_SELECT_OFF",
    "view_object_visibility": "HIDE_OFF",
    "view_regions": "SIDEBAR",
    "view_shading_options": "SHADING_SOLID",
    "transform_options": "ORIENTATION_GLOBAL",
    "transform_proportional": "PROP_ON",
    "transform_snapping": "SNAP_ON",
    "action": "ACTION",
    "anim": "ACTION",
    "armature": "ARMATURE_DATA",
    "asset": "ASSET_MANAGER",
    "bc": "MOD_BOOLEAN",
    "bk": "ASSET_MANAGER",
    "blenderkit": "ASSET_MANAGER",
    "boid": "PARTICLES",
    "bpm": "MENU_PANEL",
    "brush": "BRUSH_DATA",
    "buttons": "PROPERTIES",
    "cachefile": "FILE_CACHE",
    "camera": "CAMERA_DATA",
    "cbl": "CURVE_DATA",
    "clear": "TRASH",
    "clip": "TRACKER",
    "cloth": "MOD_CLOTH",
    "collection": "OUTLINER_COLLECTION",
    "console": "CONSOLE",
    "constraint": "CONSTRAINT",
    "curve": "CURVE_DATA",
    "curves": "CURVES_DATA",
    "curvetools": "CURVE_DATA",
    "cycles": "RENDER_STILL",
    "data": "MESH_DATA",
    "dpaint": "MOD_DYNAMICPAINT",
    "ed": "EDITMODE_HLT",
    "export_anim": "EXPORT",
    "export": "EXPORT",
    "export_gcode_format": "EXPORT",
    "export_scene": "EXPORT",
    "export_svg_format": "EXPORT",
    "extensions": "INTERNET",
    "file": "FILE_FOLDER",
    "fluid": "MOD_FLUIDSIM",
    "font": "FONT_DATA",
    "geometry": "GEOMETRY_SET",
    "gizmogroup": "GIZMO",
    "gpencil": "GREASEPENCIL",
    "graph": "GRAPH",
    "grease_pencil": "GREASEPENCIL",
    "hardflow": "EDITMODE_HLT",
    "hardflow_om": "OBJECT_DATA",
    "hops": "MODIFIER",
    "image": "IMAGE_DATA",
    "import_anim": "IMPORT",
    "import_curve": "IMPORT",
    "import_scene": "IMPORT",
    "info": "INFO",
    "lattice": "LATTICE_DATA",
    "light": "LIGHT",
    "magicsdf": "MOD_BOOLEAN",
    "kitcad": "MODIFIER",
    "make": "LINKED",
    "marker": "MARKER",
    "mask": "MOD_MASK",
    "material": "MATERIAL_DATA",
    "mball": "META_DATA",
    "mesh": "MESH_DATA",
    "nla": "NLA",
    "node": "NODETREE",
    "object": "OBJECT_DATA",
    "octane": "RENDER_STILL",
    "octane_render_aov": "RENDERLAYERS",
    "operator": "MENU_PANEL",
    "outliner": "OUTLINER",
    "paint": "BRUSH_DATA",
    "paintcurve": "CURVE_BEZCURVE",
    "palette": "COLOR",
    "particle": "PARTICLES",
    "pie_customizer": "MENU_PANEL",
    "pointcloud": "POINTCLOUD_DATA",
    "pose": "POSE_HLT",
    "poselib": "ASSET_MANAGER",
    "preferences": "PREFERENCES",
    "ptcache": "FILE_CACHE",
    "remove": "TRASH",
    "render": "RENDER_STILL",
    "rigidbody": "RIGID_BODY",
    "scene": "SCENE_DATA",
    "screen": "WINDOW",
    "script": "SCRIPT",
    "sculpt": "SCULPTMODE_HLT",
    "sculpt_curves": "CURVES",
    "sequencer": "SEQUENCE",
    "sound": "SOUND",
    "spreadsheet": "SPREADSHEET",
    "supadupafusion": "MOD_BOOLEAN",
    "surface": "SURFACE_DATA",
    "template": "PRESET",
    "text": "TEXT",
    "text_editor": "TEXT",
    "texture": "TEXTURE_DATA",
    "transform": "ORIENTATION_GLOBAL",
    "ui": "WINDOW",
    "uilist": "PRESET",
    "unlink": "UNLINKED",
    "uv": "UV",
    "view": "VIEW3D",
    "view2d": "VIEWZOOM",
    "view3d": "VIEW3D",
    "window": "WINDOW",
    "wm": "BLENDER",
    "workspace": "WORKSPACE",
    "world": "WORLD_DATA",
}

ANIMATION_GROUPS = {
    "action",
    "anim",
    "graph",
    "marker",
    "nla",
    "pose",
    "ptcache",
}

MESH_GROUPS = {
    "curve",
    "curves",
    "font",
    "geometry",
    "grease_pencil",
    "mball",
    "mesh",
    "paint",
    "pointcloud",
    "sculpt",
    "surface",
    "uv",
}

EDITOR_GROUPS = {
    "asset",
    "buttons",
    "clip",
    "console",
    "image",
    "mask",
    "node",
    "outliner",
    "sequencer",
    "spreadsheet",
    "text",
    "ui",
    "view2d",
}

OBJECT_GROUPS = {
    "armature",
    "collection",
    "constraint",
    "grease_pencil_modifiers",
    "material",
    "object",
    "object_modifiers",
    "particle",
    "physics_modifiers",
    "rigidbody",
    "scene",
    "world",
}

PHYSICS_MODIFIER_IDS = frozenset(
    {
        "CLOTH",
        "COLLISION",
        "DYNAMIC_PAINT",
        "EXPLODE",
        "FLUID",
        "OCEAN",
        "PARTICLE_INSTANCE",
        "PARTICLE_SYSTEM",
        "SOFT_BODY",
        "SURFACE",
    }
)

COMMON_GROUP_PRIORITY = {
    "object": 0,
    "mesh": 1,
    "transform": 2,
    "view3d": 3,
    "screen": 4,
    "wm": 5,
    "scene": 6,
    "node": 7,
    "image": 8,
}

CONTEXT_CATEGORY_PRIORITY = {
    "OBJECT": ("OBJECT", "TRANSFORM", "SELECT", "ADD", "VIEW", "MESH"),
    "EDIT_MESH": ("MESH", "SELECT", "TRANSFORM", "ADD", "VIEW", "OBJECT"),
    "EDIT_CURVE": ("MESH", "SELECT", "TRANSFORM", "ADD", "VIEW", "OBJECT"),
    "EDIT_SURFACE": ("MESH", "SELECT", "TRANSFORM", "ADD", "VIEW", "OBJECT"),
    "EDIT_METABALL": ("MESH", "SELECT", "TRANSFORM", "ADD", "VIEW", "OBJECT"),
    "EDIT_LATTICE": ("MESH", "SELECT", "TRANSFORM", "VIEW", "OBJECT"),
    "EDIT_CURVES": ("MESH", "SELECT", "TRANSFORM", "VIEW", "OBJECT"),
    "SCULPT": ("SCULPT", "MESH", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "SCULPT_CURVES": ("SCULPT", "MESH", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "PAINT_TEXTURE": ("PAINT", "MESH", "VIEW", "OBJECT", "TRANSFORM"),
    "PAINT_VERTEX": ("PAINT", "MESH", "VIEW", "OBJECT", "TRANSFORM"),
    "PAINT_WEIGHT": ("PAINT", "MESH", "VIEW", "OBJECT", "TRANSFORM"),
    "PAINT_GREASE_PENCIL": ("PAINT", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "SCULPT_GREASE_PENCIL": ("PAINT", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "VERTEX_GREASE_PENCIL": ("PAINT", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "WEIGHT_GREASE_PENCIL": ("PAINT", "VIEW", "OBJECT", "TRANSFORM", "SELECT"),
    "POSE": ("ANIMATION", "OBJECT", "TRANSFORM", "SELECT", "VIEW"),
    "EDIT_ARMATURE": ("ANIMATION", "OBJECT", "TRANSFORM", "SELECT", "VIEW"),
}

SCULPT_GROUPS = {"sculpt", "sculpt_curves"}

SCULPT_PAINT_OPERATOR_PREFIXES = (
    "hide_show",
    "mask_",
    "visibility_",
)

SCULPT_OBJECT_OPERATOR_NAMES = {
    "voxel_remesh",
    "voxel_size_edit",
}

PAINT_GROUPS = {
    "brush",
    "gpencil",
    "grease_pencil",
    "paint",
    "paintcurve",
    "palette",
}

NODE_GROUPS = {"node"}

SCULPT_BRUSH_ASSET_GROUPS = {
    "sculpt_brushes_curves",
    "sculpt_brushes_general",
    "sculpt_brushes_grease_pencil",
    "sculpt_brushes_paint",
    "sculpt_brushes_simulation",
}

PAINT_BRUSH_ASSET_GROUPS = {
    "paint_brushes_grease_pencil",
    "paint_brushes_grease_pencil_vertex",
    "paint_brushes_grease_pencil_weight",
    "paint_brushes_texture",
    "paint_brushes_vertex",
    "paint_brushes_weight",
}

BRUSH_ASSET_LIBRARY_GROUPS = (
    ("essentials_brushes-mesh_sculpt.blend", "sculpt_brushes_general"),
    ("essentials_brushes-curve_sculpt.blend", "sculpt_brushes_curves"),
    ("essentials_brushes-gp_sculpt.blend", "sculpt_brushes_grease_pencil"),
    ("essentials_brushes-mesh_texture.blend", "paint_brushes_texture"),
    ("essentials_brushes-mesh_vertex.blend", "paint_brushes_vertex"),
    ("essentials_brushes-mesh_weight.blend", "paint_brushes_weight"),
    ("essentials_brushes-gp_draw.blend", "paint_brushes_grease_pencil"),
    ("essentials_brushes-gp_vertex.blend", "paint_brushes_grease_pencil_vertex"),
    ("essentials_brushes-gp_weight.blend", "paint_brushes_grease_pencil_weight"),
)

LEGACY_BRUSH_ENUM_GROUPS = (
    ("sculpt_tool", "sculpt_brushes_general"),
    ("curves_sculpt_tool", "sculpt_brushes_curves"),
    ("gpencil_sculpt_tool", "sculpt_brushes_grease_pencil"),
    ("image_tool", "paint_brushes_texture"),
    ("vertex_tool", "paint_brushes_vertex"),
    ("weight_tool", "paint_brushes_weight"),
    ("gpencil_tool", "paint_brushes_grease_pencil"),
    ("gpencil_vertex_tool", "paint_brushes_grease_pencil_vertex"),
    ("gpencil_weight_tool", "paint_brushes_grease_pencil_weight"),
)

MESH_SCULPT_PAINT_BRUSHES = frozenset(
    {
        "Airbrush",
        "Blend Hard",
        "Blend Soft",
        "Blend Square",
        "Blur",
        "Paint Blend",
        "Paint Hard",
        "Paint Hard Pressure",
        "Paint Soft",
        "Paint Soft Pressure",
        "Paint Square",
        "Sharpen",
        "Smear",
    }
)

MESH_SCULPT_SIMULATION_BRUSHES = frozenset(
    {
        "Bend Boundary Cloth",
        "Bend/Twist Cloth",
        "Drag Cloth",
        "Expand/Contract Cloth",
        "Grab Cloth",
        "Grab Planar Cloth",
        "Grab Random Cloth",
        "Inflate Cloth",
        "Pinch Folds Cloth",
        "Pinch Point Cloth",
        "Push Cloth",
        "Stretch/Move Cloth",
        "Twist Boundary Cloth",
    }
)

_CURATED_BY_OPERATOR_ID = {
    action.command.split("(", 1)[0]: action
    for action in SEARCH_ACTIONS
    if action.slot_type == "OPERATOR"
}

_CURATED_CATEGORY_BY_ID = {
    action.action_id: action.category
    for action in SEARCH_ACTIONS
}


def format_operator_command(operator_id: str, kwargs: dict | None = None) -> str:
    kwargs = kwargs or {}
    arguments = ", ".join(f"{name}={_format_literal(value)}" for name, value in kwargs.items())
    return f"{operator_id}({arguments})"


def _format_literal(value) -> str:
    if isinstance(value, set):
        if not value:
            return "set()"
        return "{" + ", ".join(sorted(repr(item) for item in value)) + "}"
    return repr(value)


def operator_identifier_to_id(identifier: str) -> str:
    if "_OT_" not in identifier:
        return identifier.lower()
    module, name = identifier.split("_OT_", 1)
    return f"{module.lower()}.{name.lower()}"


def group_label(group: str, language: str) -> str:
    translated = GROUP_LABELS.get(language, {}).get(group)
    if translated:
        return translated
    return group.replace("_", " ").title()


def group_icon(group: str) -> str:
    return GROUP_ICONS.get(group, "PLUGIN")


def canonical_operator_group(group: str) -> str:
    return OPERATOR_GROUP_ALIASES.get(group, group)


def operator_group_items(language: str) -> tuple[tuple[str, str, str], ...]:
    groups = sorted(
        {
            canonical_operator_group(action.group)
            for action in discover_operator_actions() + discover_brush_asset_actions()
        },
        key=lambda item: group_label(item, language),
    )
    all_label = "Все источники" if language == "RU" else "All Sources"
    return (("ALL", all_label, ""),) + tuple(
        (group, group_label(group, language), "")
        for group in groups
    )


def operator_icon(operator_id: str) -> str:
    curated = _CURATED_BY_OPERATOR_ID.get(operator_id)
    if curated is not None:
        return curated.icon
    group = operator_id.split(".", 1)[0]
    return group_icon(group)


def operator_is_catalog_safe(operator_id: str, operator=None) -> bool:
    if operator_id in DISCOVERY_EXCLUDED_OPERATOR_IDS:
        return False
    if operator_id.startswith(DISCOVERY_EXCLUDED_OPERATOR_PREFIXES):
        return False

    if operator is None:
        return True

    try:
        import bpy

        operator_type = getattr(bpy.types, operator.get_rna_type().identifier, None)
        if operator_type is not None and "INTERNAL" in getattr(
            operator_type, "bl_options", set()
        ):
            return False
    except Exception:
        # Discovery already handles unavailable RNA below. Do not hide a public
        # operator merely because optional metadata could not be inspected.
        pass
    return True


def discover_operator_actions() -> tuple[BrowserAction, ...]:
    return _discover_operator_actions(_enabled_addon_signature())


def _enabled_addon_signature() -> tuple[str, ...]:
    try:
        import bpy

        return tuple(sorted(bpy.context.preferences.addons.keys()))
    except Exception:
        return ()


def brush_asset_catalog_supported(version: tuple[int, ...]) -> bool:
    """Return whether this Blender version has the supported brush asset layout."""

    return tuple(version[:2]) >= (4, 3)


def legacy_brush_catalog_supported(version: tuple[int, ...]) -> bool:
    """Return whether this Blender version uses legacy built-in brush tools."""

    return (4, 2) <= tuple(version[:2]) < (4, 3)


def brush_asset_group(library_name: str, brush_name: str) -> str:
    """Resolve a built-in brush asset to its human-facing catalog group."""

    default_groups = dict(BRUSH_ASSET_LIBRARY_GROUPS)
    default_group = default_groups.get(library_name, "")
    if library_name != "essentials_brushes-mesh_sculpt.blend":
        return default_group

    normalized_name = brush_name.strip()
    if (
        normalized_name in MESH_SCULPT_SIMULATION_BRUSHES
        or "cloth" in normalized_name.casefold()
    ):
        return "sculpt_brushes_simulation"
    if normalized_name in MESH_SCULPT_PAINT_BRUSHES:
        return "sculpt_brushes_paint"
    return default_group


def legacy_brush_group(enum_property: str, identifier: str) -> str:
    """Resolve a Blender 4.2 brush enum item to a catalog group."""

    default_groups = dict(LEGACY_BRUSH_ENUM_GROUPS)
    default_group = default_groups.get(enum_property, "")
    if enum_property != "sculpt_tool":
        return default_group
    if identifier == "CLOTH":
        return "sculpt_brushes_simulation"
    if identifier in {"PAINT", "SMEAR"}:
        return "sculpt_brushes_paint"
    return default_group


def legacy_brush_tool_id(brush_name: str) -> str:
    """Return the workspace tool id used by Blender 4.2 for a brush."""

    return f"builtin_brush.{brush_name}"


def discover_brush_asset_actions() -> tuple[BrowserAction, ...]:
    """Discover built-in brushes using the API available in this Blender version."""

    return _discover_brush_asset_actions(_brush_asset_library_signature())


def _brush_asset_library_signature() -> tuple:
    try:
        import bpy
    except ModuleNotFoundError:
        return ()

    version = tuple(bpy.app.version[:3])
    if legacy_brush_catalog_supported(version):
        return (version, ("LEGACY", _legacy_brush_enum_signature(bpy)))
    if not brush_asset_catalog_supported(version):
        return (version,)

    files = []
    for root in _brush_asset_roots(bpy):
        for library_name, _group in BRUSH_ASSET_LIBRARY_GROUPS:
            path = root / library_name
            if not path.is_file():
                continue
            try:
                stat = path.stat()
                files.append((str(path), stat.st_size, stat.st_mtime_ns))
            except OSError:
                files.append((str(path), 0, 0))
        if files:
            break
    return (version, ("ASSET", tuple(files)))


def _legacy_brush_enum_signature(bpy_module) -> tuple:
    entries = []
    properties = bpy_module.types.Brush.bl_rna.properties
    for enum_property, _default_group in LEGACY_BRUSH_ENUM_GROUPS:
        prop = properties.get(enum_property)
        if prop is None:
            continue
        for item in getattr(prop, "enum_items_static", ()):
            identifier = getattr(item, "identifier", "")
            name = getattr(item, "name", "")
            if not identifier or not name:
                continue
            entries.append(
                (
                    enum_property,
                    identifier,
                    name,
                    getattr(item, "description", "") or "",
                )
            )
    return tuple(entries)


def _brush_asset_roots(bpy_module) -> tuple[Path, ...]:
    roots = []
    for scope in ("LOCAL", "SYSTEM"):
        try:
            resource_path = bpy_module.utils.resource_path(scope)
        except (AttributeError, RuntimeError, TypeError):
            continue
        if not resource_path:
            continue
        root = Path(resource_path) / "datafiles" / "assets" / "brushes"
        if root not in roots:
            roots.append(root)
    return tuple(roots)


@lru_cache(maxsize=4)
def _discover_brush_asset_actions(_signature: tuple) -> tuple[BrowserAction, ...]:
    try:
        import bpy
    except ModuleNotFoundError:
        return ()

    version = tuple(bpy.app.version)
    if not (
        brush_asset_catalog_supported(version)
        or legacy_brush_catalog_supported(version)
    ):
        return ()

    if len(_signature) < 2:
        return ()
    source_type, source_payload = _signature[1]
    if source_type == "LEGACY":
        return _legacy_brush_actions(source_payload)
    if source_type != "ASSET":
        return ()

    paths = {
        Path(path_string).name: Path(path_string)
        for path_string, _size, _modified in source_payload
    }
    actions = []
    for library_name, default_group in BRUSH_ASSET_LIBRARY_GROUPS:
        path = paths.get(library_name)
        if path is None:
            continue
        try:
            with bpy.data.libraries.load(
                str(path),
                link=False,
                assets_only=True,
            ) as (data_from, _data_to):
                brush_names = tuple(getattr(data_from, "brushes", ()))
        except (OSError, RuntimeError):
            continue

        for brush_name in sorted(brush_names, key=lambda value: value.casefold()):
            display_name = brush_name.strip() or brush_name
            group = brush_asset_group(library_name, brush_name) or default_group
            relative_identifier = f"brushes/{library_name}/Brush/{brush_name}"
            item_id = f"brush_asset:{path.stem}:{display_name}"
            actions.append(
                BrowserAction(
                    token=f"BRUSH_ASSET:{path.stem}:{display_name}",
                    kind="BRUSH_ASSET",
                    item_id=item_id,
                    group=group,
                    label=display_name,
                    description=f"Blender brush asset: {display_name}",
                    command=format_operator_command(
                        "brush.asset_activate",
                        {
                            "asset_library_type": "ESSENTIALS",
                            "relative_asset_identifier": relative_identifier,
                        },
                    ),
                    icon="BRUSH_DATA",
                    slot_type="OPERATOR",
                    operator_context="EXEC_DEFAULT",
                    search_terms=(
                        "brush brushes кисть кисти "
                        f"{group_label(group, 'EN')} {group_label(group, 'RU')} "
                        f"brush.asset_activate {library_name}"
                    ),
                )
            )
    return tuple(actions)


def _legacy_brush_actions(entries: tuple) -> tuple[BrowserAction, ...]:
    actions = []
    for enum_property, identifier, brush_name, description in entries:
        display_name = brush_name.strip() or brush_name
        group = legacy_brush_group(enum_property, identifier)
        tool_id = legacy_brush_tool_id(brush_name)
        actions.append(
            BrowserAction(
                token=f"BRUSH_TOOL:{enum_property}:{identifier}",
                kind="BRUSH_TOOL",
                item_id=f"brush_tool:{enum_property}:{identifier}",
                group=group,
                label=display_name,
                description=description or f"Blender brush tool: {display_name}",
                command=format_operator_command(
                    "wm.tool_set_by_id",
                    {"name": tool_id},
                ),
                icon="BRUSH_DATA",
                slot_type="OPERATOR",
                operator_context="EXEC_DEFAULT",
                search_terms=(
                    "brush brushes кисть кисти "
                    f"{group_label(group, 'EN')} {group_label(group, 'RU')} "
                    f"{identifier} {enum_property} {tool_id}"
                ),
            )
        )
    return tuple(actions)


@lru_cache(maxsize=4)
def _discover_operator_actions(
    _addon_signature: tuple[str, ...],
) -> tuple[BrowserAction, ...]:
    try:
        import bpy
    except ModuleNotFoundError:
        return ()

    actions = []
    for module_name in sorted(name for name in dir(bpy.ops) if not name.startswith("_")):
        module = getattr(bpy.ops, module_name, None)
        if module is None:
            continue
        for operator_name in sorted(name for name in dir(module) if not name.startswith("_")):
            operator = getattr(module, operator_name, None)
            if operator is None or not hasattr(operator, "get_rna_type"):
                continue
            operator_id = f"{module_name}.{operator_name}"
            if not operator_is_catalog_safe(operator_id, operator):
                continue
            rna = None
            try:
                rna = operator.get_rna_type()
                label = rna.name or operator_name.replace("_", " ").title()
                description = rna.description or operator_id
                search_terms = _operator_enum_search_terms(rna)
            except Exception:
                label = operator_name.replace("_", " ").title()
                description = operator_id
                search_terms = ""

            if operator_id == "object.modifier_add" and rna is not None:
                modifier_actions = _modifier_actions_from_rna(rna)
                if modifier_actions:
                    actions.extend(modifier_actions)
                    continue

            actions.append(
                BrowserAction(
                    token=f"OPERATOR:{operator_id}",
                    kind="OPERATOR",
                    item_id=operator_id,
                    group=module_name,
                    label=label,
                    description=description,
                    command=format_operator_command(operator_id),
                    icon=operator_icon(operator_id),
                    slot_type="OPERATOR",
                    search_terms=search_terms,
                )
            )
    return tuple(actions)


def _modifier_actions_from_rna(rna) -> tuple[BrowserAction, ...]:
    try:
        modifier_type = rna.properties.get("type")
        enum_items = modifier_type.enum_items_static if modifier_type else ()
    except (AttributeError, RuntimeError, TypeError):
        return ()
    return _modifier_actions_from_enum_items(enum_items)


def _modifier_actions_from_enum_items(enum_items) -> tuple[BrowserAction, ...]:
    actions = []
    for item in enum_items:
        identifier = getattr(item, "identifier", "")
        if not identifier:
            continue

        name = getattr(item, "name", "") or identifier.replace("_", " ").title()
        description = getattr(item, "description", "") or f"Add {name} modifier"
        if identifier.startswith("GREASE_PENCIL_") or identifier == "LINEART":
            group = "grease_pencil_modifiers"
            label = f"Grease Pencil: {name}"
        elif identifier in PHYSICS_MODIFIER_IDS:
            group = "physics_modifiers"
            label = name
        else:
            group = "object_modifiers"
            label = name

        actions.append(
            BrowserAction(
                token=f"OPERATOR_VARIANT:object.modifier_add:{identifier}",
                kind="OPERATOR",
                item_id=f"object.modifier_add.{identifier.casefold()}",
                group=group,
                label=label,
                description=description,
                command=format_operator_command(
                    "object.modifier_add",
                    {"type": identifier},
                ),
                icon=group_icon(group),
                slot_type="OPERATOR",
                operator_context="EXEC_DEFAULT",
                search_terms=(
                    "modifier modifiers модификатор модификаторы "
                    f"{identifier} {name} {description} "
                    f"{group_label(group, 'EN')} {group_label(group, 'RU')}"
                ),
            )
        )
    return tuple(actions)


def _operator_enum_search_terms(rna) -> str:
    terms = []
    for prop in rna.properties:
        if prop.type != "ENUM":
            continue
        terms.extend((prop.identifier, prop.name))
        # Dynamic enum items depend on the current editor and can emit invalid
        # default warnings when queried from Preferences. Static items are safe
        # and cover the searchable variants that can be assigned directly.
        for item in prop.enum_items_static:
            if not item.identifier:
                continue
            terms.extend((item.identifier, item.name, item.description))
    return " ".join(term for term in terms if term)


def _all_subclasses(base_class):
    seen = set()
    stack = list(base_class.__subclasses__())
    while stack:
        subclass = stack.pop()
        if subclass in seen:
            continue
        seen.add(subclass)
        yield subclass
        stack.extend(subclass.__subclasses__())


@lru_cache(maxsize=1)
def discover_menu_actions() -> tuple[BrowserAction, ...]:
    try:
        import bpy
    except ModuleNotFoundError:
        return ()

    by_id = {}
    for menu_class in _all_subclasses(bpy.types.Menu):
        menu_id = getattr(menu_class, "bl_idname", "") or getattr(menu_class, "__name__", "")
        if not menu_id or not hasattr(bpy.types, menu_id):
            continue
        label = getattr(menu_class, "bl_label", "") or menu_id
        by_id[menu_id] = BrowserAction(
            token=f"MENU:{menu_id}",
            kind="MENU",
            item_id=menu_id,
            group="menu",
            label=label,
            description=menu_id,
            command=menu_id,
            icon="MENU_PANEL",
            slot_type="MENU",
        )
    return tuple(sorted(by_id.values(), key=lambda action: action.label.casefold()))


def filter_actions(
    actions: Iterable[BrowserAction],
    query: str = "",
    group: str = "ALL",
    rank_matches: bool = False,
    context_mode: str = "",
    favorite_tokens: Iterable[str] = (),
    recent_item_ids: Iterable[str] = (),
    fuzzy_fallback: bool = False,
    fuzzy_min_results: int = CATALOG_PAGE_SIZE,
) -> tuple[BrowserAction, ...]:
    normalized_query = _normalize_search_text(query)
    words = tuple(normalized_query.split())
    favorite_token_set = frozenset(favorite_tokens)
    recent_item_id_set = frozenset(recent_item_ids)
    direct_matches = []
    fuzzy_candidates = []
    selected_group = canonical_operator_group(group)
    for index, action in enumerate(actions):
        if selected_group != "ALL" and canonical_operator_group(action.group) != selected_group:
            continue
        match_rank = _direct_match_rank(action, normalized_query, words)
        if words and match_rank is None:
            fuzzy_candidates.append((index, action))
            continue
        score = (
            _search_score(
                action,
                match_rank or 0,
                context_mode,
                favorite_token_set,
                recent_item_id_set,
            )
            if rank_matches and words
            else ()
        )
        direct_matches.append((score, index, action))

    if rank_matches and words:
        direct_matches.sort(key=lambda item: (item[0], item[1]))

    if (
        rank_matches
        and fuzzy_fallback
        and len(direct_matches) < fuzzy_min_results
        and len(_compact_search_text(normalized_query)) >= 3
    ):
        fuzzy_matches = []
        for index, action in fuzzy_candidates:
            fuzzy_score = _fuzzy_match_score(action, normalized_query)
            if fuzzy_score is None:
                continue
            ranking = _search_score(
                action,
                7,
                context_mode,
                favorite_token_set,
                recent_item_id_set,
            )
            fuzzy_matches.append(((fuzzy_score, ranking), index, action))
        fuzzy_matches.sort(key=lambda item: (item[0], item[1]))
        missing = max(0, fuzzy_min_results - len(direct_matches))
        direct_matches.extend(fuzzy_matches[:missing])

    return tuple(item[2] for item in direct_matches)


def _normalize_search_text(value: str) -> str:
    return " ".join(re.sub(r"[_./:-]+", " ", value.casefold()).split())


def _compact_search_text(value: str) -> str:
    return "".join(character for character in value if character.isalnum())


def _direct_match_rank(
    action: BrowserAction,
    query: str,
    words: tuple[str, ...],
) -> int | None:
    if not words:
        return 0

    label = _normalize_search_text(action.label)
    item_id = _normalize_search_text(action.item_id)
    operator_name = _normalize_search_text(action.item_id.rsplit(".", 1)[-1])
    metadata = _normalize_search_text(f"{action.description} {action.search_terms}")

    if label == query:
        return 0
    if label.startswith(query):
        return 1
    if all(word in label for word in words):
        return 2
    if operator_name == query:
        return 3
    if operator_name.startswith(query):
        return 4
    if all(word in item_id for word in words):
        return 5
    if all(word in f"{label} {item_id} {metadata}" for word in words):
        return 6
    return None


def _search_score(
    action: BrowserAction,
    match_rank: int,
    context_mode: str,
    favorite_tokens: frozenset[str],
    recent_item_ids: frozenset[str],
) -> tuple[int, int, int, int, int, int, str]:
    label = action.label.casefold()
    context_priority = _context_priority(action, context_mode)
    if action.token in favorite_tokens:
        usage_priority = 0
    elif action.item_id in recent_item_ids:
        usage_priority = 1
    else:
        usage_priority = 2
    featured = 0 if action.token.startswith("CURATED:") or action.item_id in _CURATED_BY_OPERATOR_ID else 1
    group_priority = COMMON_GROUP_PRIORITY.get(action.group, 50)
    return (
        match_rank,
        context_priority,
        usage_priority,
        featured,
        group_priority,
        len(label),
        label,
    )


def _context_priority(action: BrowserAction, context_mode: str) -> int:
    priorities = CONTEXT_CATEGORY_PRIORITY.get(context_mode, ())
    category = broad_category_for_action(action)
    try:
        return priorities.index(category)
    except ValueError:
        return len(priorities) + 1


def _fuzzy_match_score(
    action: BrowserAction,
    query: str,
) -> tuple[int, int, int] | None:
    compact_query = _compact_search_text(query)
    best = None
    for field_priority, value in enumerate(
        (action.label, action.item_id.rsplit(".", 1)[-1])
    ):
        normalized = _normalize_search_text(value)
        tokens = normalized.split()
        initials = "".join(token[0] for token in tokens if token)
        compact_value = _compact_search_text(normalized)

        initials_metrics = _subsequence_metrics(compact_query, initials)
        if initials_metrics is not None:
            candidate = (0, initials_metrics[0], field_priority)
            best = candidate if best is None or candidate < best else best

        value_metrics = _subsequence_metrics(compact_query, compact_value)
        if value_metrics is not None:
            candidate = (1, value_metrics[0], field_priority)
            best = candidate if best is None or candidate < best else best
    return best


def _subsequence_metrics(needle: str, haystack: str) -> tuple[int, int] | None:
    positions = []
    cursor = 0
    for character in needle:
        found = haystack.find(character, cursor)
        if found < 0:
            return None
        positions.append(found)
        cursor = found + 1
    if not positions:
        return None
    span = positions[-1] - positions[0] + 1
    return span - len(needle), len(haystack) - len(needle)


def broad_category_for_action(action: BrowserAction) -> str:
    curated_category = _CURATED_CATEGORY_BY_ID.get(action.item_id)
    if curated_category:
        return curated_category
    if action.group in SCULPT_BRUSH_ASSET_GROUPS:
        return "SCULPT"
    if action.group in PAINT_BRUSH_ASSET_GROUPS:
        return "PAINT"
    operator_id = action.item_id.casefold()
    if "." not in operator_id:
        return "OTHER"
    group, name = operator_id.split(".", 1)

    if (
        group in SCULPT_GROUPS
        or group == "paint" and name.startswith(SCULPT_PAINT_OPERATOR_PREFIXES)
        or group == "object" and name in SCULPT_OBJECT_OPERATOR_NAMES
    ):
        return "SCULPT"
    if group in PAINT_GROUPS:
        return "PAINT"
    if group in ANIMATION_GROUPS:
        return "ANIMATION"
    if group in NODE_GROUPS:
        return "NODES"
    if (
        name == "add"
        or name.startswith(("add_", "primitive_"))
        or name.endswith("_add")
    ):
        return "ADD"
    if "select" in name or name.startswith(("pick", "lasso")):
        return "SELECT"
    if group == "transform" or name.startswith(
        ("align", "mirror", "move", "resize", "rotate", "scale", "translate", "transform")
    ):
        return "TRANSFORM"
    if any(
        keyword in name
        for keyword in ("animation", "bake", "frame", "fcurve", "keyframe")
    ):
        return "ANIMATION"
    if group in EDITOR_GROUPS | {"screen", "view3d", "workspace"} or name.startswith(
        ("localview", "orbit", "pan", "view_", "zoom")
    ):
        return "VIEW"
    if group in MESH_GROUPS:
        return "MESH"
    if group in OBJECT_GROUPS:
        return "OBJECT"
    return "OTHER"


def filter_broad_category(
    actions: Iterable[BrowserAction],
    category: str,
) -> tuple[BrowserAction, ...]:
    return tuple(
        action
        for action in actions
        if broad_category_for_action(action) == category
    )


def recent_operator_actions(context, limit: int = 40) -> tuple[BrowserAction, ...]:
    operators = getattr(getattr(context, "window_manager", None), "operators", ())
    actions = []
    seen = set()
    for operator in reversed(list(operators)):
        identifier = getattr(operator, "bl_idname", "") or getattr(operator.bl_rna, "identifier", "")
        operator_id = operator_identifier_to_id(identifier)
        if not operator_id or operator_id.startswith("pie_customizer."):
            continue
        kwargs = _operator_instance_kwargs(operator)
        command = format_operator_command(operator_id, kwargs)
        if command in seen:
            continue
        seen.add(command)
        label = getattr(operator, "bl_label", "") or getattr(operator.bl_rna, "name", "") or operator_id
        description = getattr(operator.bl_rna, "description", "") or operator_id
        group = operator_id.split(".", 1)[0]
        actions.append(
            BrowserAction(
                token=f"RECENT:{command}",
                kind="OPERATOR",
                item_id=operator_id,
                group=group,
                label=label,
                description=description,
                command=command,
                icon=operator_icon(operator_id),
                slot_type="OPERATOR",
            )
        )
        if len(actions) >= limit:
            break
    return tuple(actions)


def _operator_instance_kwargs(operator) -> dict:
    result = {}
    for prop in getattr(operator.bl_rna, "properties", ()):
        identifier = prop.identifier
        if identifier == "rna_type" or getattr(prop, "is_readonly", False):
            continue
        try:
            if not operator.is_property_set(identifier):
                continue
            value = getattr(operator, identifier)
            converted = _literal_value(value)
            if converted is not _UNSUPPORTED:
                result[identifier] = converted
        except Exception:
            continue
    return result


_UNSUPPORTED = object()


def _literal_value(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, set):
        converted = [_literal_value(item) for item in value]
        if any(item is _UNSUPPORTED for item in converted):
            return _UNSUPPORTED
        return set(converted)
    if isinstance(value, (list, tuple)) or type(value).__module__ == "mathutils":
        converted = [_literal_value(item) for item in value]
        if any(item is _UNSUPPORTED for item in converted):
            return _UNSUPPORTED
        return tuple(converted)
    return _UNSUPPORTED


def refresh_discovery() -> None:
    _discover_operator_actions.cache_clear()
    _discover_brush_asset_actions.cache_clear()
    discover_menu_actions.cache_clear()
