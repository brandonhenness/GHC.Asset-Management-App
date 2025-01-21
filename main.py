import logging
from pathlib import Path
import repath
import re

import flet as ft
from module_manager import ModuleManager
from left_navigation_menu import LeftNavigationMenu
from version import __version__
from database.database import init_db

logging.basicConfig(level=logging.INFO)


async def main(page: ft.Page):
    await init_db()
    module_manager = ModuleManager(page)

    page.title = "Asset Management App"

    page.fonts = {
        "Roboto Mono": "RobotoMono-VariableFont_wght.ttf",
    }

    def get_route_list(route):
        route_list = [item for item in route.split("/") if item != ""]
        return route_list

    async def route_change(e):
        route_list = get_route_list(page.route)
        if len(route_list) == 0:
            await page.go_async("/issue_assets")  # Default route
        else:
            # Construct the route name from the route list
            route_name = "/".join(route_list)
            await display_navigation_item(route_name)

    async def display_navigation_item(route):
        print(f"Displaying navigation item for route: {route}")

        # Define the route pattern for dynamic routes
        pattern = repath.pattern("issue_assets/entity_assets/:entity_id")
        match = re.match(pattern, route)

        if match:
            params = match.groupdict()
            # Extract the entity_id parameter for a dynamic route
            entity_id = params["entity_id"]
            print(f"Entity ID: {entity_id}")

            # Call the module's main function with the entity ID
            module_main = module_manager.get_module_main("issue_assets/entity_assets")
            if callable(module_main):
                module_widget = module_main(page)
        else:
            # Handle top-level and other static routes
            if route in module_manager.modules:
                module_main = module_manager.get_module_main(route)
                if callable(module_main):
                    module_widget = module_main(page)
            else:
                print("Error: No module found for the specified route")
                return

        # Display the module widget
        if module_widget:
            module_view.controls.clear()
            module_view.controls.append(module_widget)
            await page.update_async()
        else:
            print(
                "Error: Module widget is not a valid Flet control or a list of Flet controls."
            )

    print(f"Available modules: {module_manager.modules.keys()}")

    left_nav = LeftNavigationMenu(page, module_manager=module_manager)
    module_view = ft.Column(expand=True)

    page.appbar = ft.AppBar(
        leading=ft.Container(padding=5, content=ft.Image(src=f"logo.svg")),
        leading_width=40,
        title=ft.Text("Asset Management App"),
        center_title=True,
        bgcolor=ft.colors.INVERSE_PRIMARY,
        actions=[
            ft.Container(padding=10, content=ft.Text(f"App version: {__version__}"))
        ],
    )

    # TODO load the theme seed from local storage
    # TODO load theme mode from local storage
    # page.theme_mode = ft.ThemeMode.SYSTEM

    page.on_error = lambda e: print("Page error:", e.data)

    await page.add_async(
        ft.Row(
            [left_nav, ft.VerticalDivider(width=1), module_view],
            expand=True,
        )
    )

    page.on_route_change = route_change
    print(f"Initial route: {page.route}")
    await page.go_async(page.route)


if __name__ == "__main__":
    ft.app(main, assets_dir="assets")
