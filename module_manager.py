import importlib.util
import os
import sys
from pathlib import Path

import flet as ft


class NavigationItem:
    def __init__(self, name, label, icon, selected_icon):
        self.name = name
        self.label = label
        self.icon = icon
        self.selected_icon = selected_icon
        self.modules = []  # Modules related to this ControlGroup


class ModuleManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.modules = {}
        self.import_modules("modules")

    destinations_list = [
        NavigationItem(
            name="issue_assets",
            label="Issue Assets",
            icon=ft.icons.ASSIGNMENT_TURNED_IN_OUTLINED,
            selected_icon=ft.icons.ASSIGNMENT_TURNED_IN,
        ),
        NavigationItem(
            name="return_assets",
            label="Return Assets",
            icon=ft.icons.ASSIGNMENT_RETURNED_OUTLINED,
            selected_icon=ft.icons.ASSIGNMENT_RETURNED,
        ),
    ]

    def find_navigation_item(self, navigation_item_name):
        for navigation_item in self.destinations_list:
            if navigation_item.name == navigation_item_name:
                return navigation_item
        return None

    def list_module_dirs(self):
        modules_path = os.path.join(str(Path(__file__).parent), "modules")
        module_dirs = [
            d
            for d in os.listdir(modules_path)
            if os.path.isdir(os.path.join(modules_path, d))
        ]
        return module_dirs

    def get_module_main(self, route_name):
        """
        Returns the 'main' function of the module corresponding to the given route name.
        """
        return self.modules.get(route_name)

    def import_modules(self, path, parent_module=""):
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                # If it's a directory, recursively call import_modules
                new_parent_module = f"{parent_module}/{item}" if parent_module else item
                self.import_modules(full_path, new_parent_module)
            elif item == "index.py":
                module_name = (
                    full_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                )
                print(f"Importing module: {module_name}")  # Debugging statement
                self.load_module(module_name, full_path, parent_module)

    def load_module(self, module_name, file_path, parent_module):
        if module_name not in sys.modules:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            print(
                f"Loaded module: {module_name}, main: {getattr(module, 'main', None)}"
            )

            # Store a lambda function that will call the module's main function with the page argument
            route_name = parent_module if parent_module else module_name.split(".")[-1]
            self.modules[route_name] = lambda page: getattr(
                module, "main", lambda p: None
            )(page)
