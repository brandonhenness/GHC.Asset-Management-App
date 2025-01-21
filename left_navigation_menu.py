import flet as ft
from popup_color_item import PopupColorItem
from module_manager import ModuleManager


class LeftNavigationMenu(ft.Column):
    def __init__(self, page, module_manager: ModuleManager):
        super().__init__()
        self.page = page
        self.module_manager = module_manager
        self.rail = ft.NavigationRail(
            extended=True,
            expand=True,
            selected_index=0,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=self.get_destinations(),
            on_change=self.navigation_item_selected,
        )

        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.dark_light_text = ft.Text("Light theme")
        elif self.page.theme_mode == ft.ThemeMode.DARK:
            self.dark_light_text = ft.Text("Dark theme")
        else:
            self.dark_light_text = ft.Text("System theme")

        self.controls = [
            self.rail,
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.BRIGHTNESS_2_OUTLINED,
                                tooltip="Toggle brightness",
                                on_click=self.theme_changed,
                            ),
                            self.dark_light_text,
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.PopupMenuButton(
                                icon=ft.icons.COLOR_LENS_OUTLINED,
                                items=[
                                    PopupColorItem(
                                        color="deeppurple", name="Deep purple"
                                    ),
                                    PopupColorItem(color="indigo", name="Indigo"),
                                    PopupColorItem(color="blue", name="Blue"),
                                    PopupColorItem(color="teal", name="Teal"),
                                    PopupColorItem(color="green", name="Green"),
                                    PopupColorItem(color="yellow", name="Yellow"),
                                    PopupColorItem(color="orange", name="Orange"),
                                    PopupColorItem(
                                        color="deeporange", name="Deep orange"
                                    ),
                                    PopupColorItem(color="pink", name="Pink"),
                                ],
                            ),
                            ft.Text("Seed color"),
                        ]
                    ),
                ]
            ),
        ]

    def get_destinations(self):
        destinations = []
        for destination in self.module_manager.destinations_list:
            destinations.append(
                ft.NavigationRailDestination(
                    icon=destination.icon,
                    selected_icon=destination.selected_icon,
                    label=destination.label,
                )
            )
        return destinations

    async def navigation_item_selected(self, e):
        navigation_item_name = self.module_manager.destinations_list[
            e.control.selected_index
        ].name
        await self.page.go_async(f"/{navigation_item_name}")

    async def theme_changed(self, e):
        # TODO save theme mode in local storage
        if self.page.theme_mode == ft.ThemeMode.SYSTEM:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.dark_light_text.value = "Light theme"
        elif self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.dark_light_text.value = "Dark theme"
        else:
            self.page.theme_mode = ft.ThemeMode.SYSTEM
            self.dark_light_text.value = "System theme"
        await self.page.update_async()
