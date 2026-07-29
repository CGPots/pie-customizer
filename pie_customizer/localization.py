"""Small UI localization helper for Pie Customizer."""

from __future__ import annotations


STRINGS = {
    "RU": {
        "apply": "Применить",
        "apply_help": "Нажмите «Применить» после изменений, чтобы обновить меню и горячие клавиши.",
        "import": "Импорт",
        "export": "Экспорт",
        "advanced": "Дополнительно",
        "empty_state": "Добавьте pie menu, чтобы начать.",
        "menus_title": "Круговые меню",
        "capture_shortcut_prompt": "Нажмите клавишу или сочетание. Esc - отмена.",
        "capture_shortcut_cancelled": "Назначение клавиши отменено",
        "capture_shortcut_set": "Назначена горячая клавиша",
        "capture_shortcut_background": "Назначение клавиши доступно только в обычном окне Blender",
        "slots": "Кнопки выбранного меню",
        "empty_slot": "Пусто",
        "nested_menu_empty": "Создайте или включите второе круговое меню",
        "nested_menu_description": "Открыть вложенное круговое меню",
        "nested_menu_no_actions": "В этом меню нет кнопок",
        "command_category": "Источник команд",
        "all_sources": "Все источники",
        "empty_position": "Выберите команду из каталога.",
        "catalog_action_assigned": "Назначено действие",
        "catalog_empty": "Ничего не найдено",
        "catalog_search_hint": "Введите название команды или operator id.",
        "favorite_added": "Добавлено в избранное",
        "favorite_removed": "Удалено из избранного",
        "operator_parameters": "Параметры",
        "no_operator_parameters": "У этой команды нет доступных параметров",
        "operator_parameters_saved": "Параметры команды сохранены",
        "slot_cleared": "Позиция очищена",
        "slot_type": "Тип слота",
        "label": "Подпись",
        "command": "Команда",
        "run_mode": "Режим запуска",
        "no_key": "Нет клавиши",
        "operator_help": "Введите operator id. Например: object.delete() или mesh.primitive_cube_add(size=2)",
        "property_help": "Введите путь через context или bpy.context. Например: context.space_data.overlay.show_overlays",
        "menu_help": "Введите идентификатор меню Blender. Например: VIEW3D_MT_view",
        "registered": "Pie Customizer: меню и горячие клавиши зарегистрированы",
        "no_active_menu": "Нет выбранного pie menu",
        "export_failed": "Экспорт не удался",
        "exported": "Экспортировано pie menu",
        "import_failed": "Импорт не удался",
        "imported": "Импортировано pie menu",
        "missing_menus": "В файле нет списка pie_menus",
        "custom_pie": "Пользовательское меню",
        "pie_not_found": "Pie menu не найдено",
        "unknown_operator_module": "Неизвестный модуль оператора",
        "unknown_operator": "Неизвестный оператор",
        "invalid_key": "Укажите клавишу",
        "keymap_failed": "не удалось зарегистрировать горячую клавишу",
        "bool_property_required": "Переключение без '= значение' работает только с bool-свойствами",
        "context_property_required": "Путь свойства должен начинаться с context или bpy.context",
        "operator_arguments_runner": "Аргументы оператора выполняются через runner",
        "proportional_falloff_wrapper": "Замените эту кнопку на готовый вариант «Спад» из каталога Pie Customizer",
        "origin_set_wrapper": "Замените эту кнопку на готовый вариант Origin из каталога Pie Customizer",
    },
    "EN": {
        "apply": "Apply",
        "apply_help": "Click Apply after making changes to update menus and shortcuts.",
        "import": "Import",
        "export": "Export",
        "advanced": "Advanced",
        "empty_state": "Add a pie menu to start.",
        "menus_title": "Pie Menus",
        "capture_shortcut_prompt": "Press a key or key combination. Esc cancels.",
        "capture_shortcut_cancelled": "Shortcut capture cancelled",
        "capture_shortcut_set": "Shortcut assigned",
        "capture_shortcut_background": "Shortcut capture is only available in the regular Blender UI",
        "slots": "Buttons in Selected Menu",
        "empty_slot": "Empty",
        "nested_menu_empty": "Create or enable a second pie menu",
        "nested_menu_description": "Open nested pie menu",
        "nested_menu_no_actions": "This menu has no buttons",
        "command_category": "Command Source",
        "all_sources": "All Sources",
        "empty_position": "Choose a command from the catalog.",
        "catalog_action_assigned": "Assigned action",
        "catalog_empty": "Nothing found",
        "catalog_search_hint": "Enter a command name or operator id.",
        "favorite_added": "Added to favorites",
        "favorite_removed": "Removed from favorites",
        "operator_parameters": "Parameters",
        "no_operator_parameters": "This command has no editable parameters",
        "operator_parameters_saved": "Command parameters saved",
        "slot_cleared": "Position cleared",
        "slot_type": "Slot Type",
        "label": "Label",
        "command": "Command",
        "run_mode": "Run Mode",
        "no_key": "No key",
        "operator_help": "Enter an operator id. Example: object.delete() or mesh.primitive_cube_add(size=2)",
        "property_help": "Enter a path through context or bpy.context. Example: context.space_data.overlay.show_overlays",
        "menu_help": "Enter a Blender menu identifier. Example: VIEW3D_MT_view",
        "registered": "Pie Customizer menus and shortcuts registered",
        "no_active_menu": "No selected pie menu",
        "export_failed": "Export failed",
        "exported": "Exported pie menu",
        "import_failed": "Import failed",
        "imported": "Imported pie menu",
        "missing_menus": "Missing pie_menus list",
        "custom_pie": "Custom Pie",
        "pie_not_found": "Pie menu not found",
        "unknown_operator_module": "Unknown operator module",
        "unknown_operator": "Unknown operator",
        "invalid_key": "Set a key",
        "keymap_failed": "failed to register shortcut",
        "bool_property_required": "Property toggle without '= value' only works for booleans",
        "context_property_required": "Property path must start with context or bpy.context",
        "operator_arguments_runner": "Operator arguments are handled by the runner",
        "proportional_falloff_wrapper": "Replace this button with a ready-made Falloff option from the Pie Customizer catalog",
        "origin_set_wrapper": "Replace this button with a ready-made Origin option from the Pie Customizer catalog",
    },
}


_RU_NATIVE_TRANSLATIONS = {
    # Preferences and properties.
    "Catalog": "Каталог",
    "Action source for the pie menu": "Источник действий для pie menu",
    "Command Browser": "Просмотр команд",
    "Technical Filter": "Технический фильтр",
    "Filter commands by their internal bpy.ops module": "Фильтровать команды по внутреннему модулю bpy.ops",
    "Blender Section": "Раздел Blender",
    "Search by name, description, or operator id": "Искать по названию, описанию или operator id",
    "Use": "Использовать",
    "Enabled": "Включить",
    "Show this slot in the pie menu": "Показывать этот слот в pie menu",
    "Label": "Подпись",
    "Button text in the pie menu": "Текст кнопки в pie menu",
    "Icon": "Иконка",
    "Built-in Blender icon name, such as MESH_CUBE": "Имя встроенной иконки Blender, например MESH_CUBE",
    "Type": "Тип",
    "Action type for this slot": "Тип действия в слоте",
    "Command": "Команда",
    "Operator, property, or menu identifier": "Оператор, свойство или идентификатор меню",
    "Run Mode": "Режим запуска",
    "How to run the Blender operator": "Как запускать оператор Blender",
    "Register this pie menu and its shortcut": "Регистрировать это pie menu и его горячую клавишу",
    "Name": "Название",
    "Pie menu name": "Название pie menu",
    "Custom Pie": "Пользовательское меню",
    "Shortcut Context": "Контекст клавиш",
    "Blender keymap where the shortcut will be created": "Keymap Blender, в котором будет создана горячая клавиша",
    "Keymap Name": "Название keymap",
    "Keymap name for custom mode": "Имя keymap для ручного режима",
    "Space type for a custom keymap": "Space type для ручного keymap",
    "Region type for a custom keymap": "Region type для ручного keymap",
    "Key": "Клавиша",
    "Blender event type, such as Q, SPACE, or F5": "Клавиша Blender event type, например Q, SPACE, F5",
    "Event": "Событие",
    "Shortcut event type": "Тип события для горячей клавиши",
    "Position": "Позиция",
    "Position of the slot inside the pie menu": "Позиция слота внутри pie menu",
    # Static enum items.
    "Left": "Слева",
    "Right": "Справа",
    "Bottom": "Снизу",
    "Top": "Сверху",
    "Top Left": "Сверху слева",
    "Top Right": "Сверху справа",
    "Bottom Left": "Снизу слева",
    "Bottom Right": "Снизу справа",
    "3D Viewport window": "Окно 3D Viewport",
    "Object Mode shortcuts": "Горячие клавиши Object Mode",
    "Mesh Edit Mode shortcuts": "Горячие клавиши режима редактирования Mesh",
    "Global Blender window shortcuts": "Глобальные горячие клавиши окна Blender",
    "Image Editor shortcuts": "Горячие клавиши Image Editor",
    "Node Editor shortcuts": "Горячие клавиши Node Editor",
    "Custom": "Свой",
    "Set a custom keymap name, space type, and region type": "Задать имя keymap, space type и region type вручную",
    "Press": "Нажатие",
    "Release": "Отпускание",
    "Click": "Клик",
    "Double Click": "Двойной клик",
    "Open the operator interface when available": "Открыть интерфейс оператора, если он есть",
    "Run the operator immediately": "Выполнить оператор сразу",
    # Operators and their tooltips.
    "Add Pie Menu": "Добавить pie menu",
    "Create a new custom pie menu": "Создать новое пользовательское pie menu",
    "Remove Pie Menu": "Удалить pie menu",
    "Remove the selected custom pie menu": "Удалить выбранное пользовательское pie menu",
    "Duplicate Pie Menu": "Дублировать pie menu",
    "Create a copy of the selected pie menu": "Создать копию выбранного pie menu",
    "Apply Pie Menus": "Применить pie menu",
    "Register custom pie menus and shortcuts": "Зарегистрировать пользовательские pie menu и горячие клавиши",
    "Assign Shortcut": "Назначить горячую клавишу",
    "Press a key to assign it to the selected pie menu": "Нажмите реальную клавишу, чтобы назначить её выбранному pie menu",
    "Add Action to Pie Menu": "Добавить действие в pie menu",
    "Assign an action to the selected pie position": "Назначить действие выбранной позиции pie menu",
    "Add or Remove Favorite": "Добавить или удалить из избранного",
    "Save this action in catalog favorites": "Сохранить действие в избранном каталога",
    "Change Catalog Page": "Переключить страницу каталога",
    "Open Command Section": "Открыть раздел команд",
    "Show commands in the selected section": "Показать команды выбранного раздела",
    "Open Command Group": "Открыть группу команд",
    "Show operators in the selected group": "Показать операторы выбранной группы",
    "Select Command Source": "Выбрать источник команд",
    "Search and select a Blender operator source": "Найти и выбрать источник операторов Blender",
    "Command Parameters": "Параметры команды",
    "Configure Blender operator parameters": "Настроить параметры оператора Blender",
    "Clear Position": "Очистить позицию",
    "Remove the action from the selected pie position": "Удалить действие из выбранной позиции pie menu",
    "Select Position": "Выбрать позицию",
    "Select a disabled position for editing": "Выбрать отключённую позицию для редактирования",
    "Run Pie Menu Action": "Выполнить действие pie menu",
    "Operator": "Оператор",
    "Property": "Свойство",
    "Export Pie Menus": "Экспорт pie menu",
    "Export custom pie menus to a JSON file": "Экспортировать пользовательские pie menu в JSON-файл",
    "Import Pie Menus": "Импорт pie menu",
    "Import custom pie menus from a JSON file": "Импортировать пользовательские pie menu из JSON-файла",
    "Import Mode": "Режим импорта",
    "Append": "Добавить",
    "Append imported menus to the existing menus": "Добавить импортированные меню к существующим",
    "Replace": "Заменить",
    "Remove existing menus and load the imported menus": "Удалить существующие меню и загрузить импортированные",
}

BLENDER_TRANSLATIONS = {
    "ru_RU": {
        ("*", source): translation
        for source, translation in _RU_NATIVE_TRANSLATIONS.items()
    },
}


def resolve_language(
    blender_language: str = "en_US",
    translate_interface: bool = True,
) -> str:
    if not translate_interface:
        return "EN"
    normalized = (blender_language or "").lower().replace("-", "_")
    return "RU" if normalized.startswith("ru") else "EN"


def effective_language(context=None) -> str:
    try:
        if context is None:
            import bpy

            context = bpy.context
        view = context.preferences.view
        return resolve_language(
            view.language,
            view.use_translate_interface,
        )
    except (AttributeError, ImportError, RuntimeError):
        return "EN"


def t(prefs, key: str) -> str:
    language = effective_language()
    strings = STRINGS.get(language, STRINGS["EN"])
    return strings.get(key, STRINGS["EN"].get(key, key))


def tr(language: str, key: str) -> str:
    strings = STRINGS.get(language, STRINGS["EN"])
    return strings.get(key, STRINGS["EN"].get(key, key))
