import flet as ft
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import AsyncSessionLocal
from database.models import Transaction, IssuedAsset, Asset, Entity, User


def main(page: ft.Page):
    # ... [previous code and functions like on_error] ...

    async def issue_asset_to_entity(event):
        # Implement logic to issue an asset to the selected entity
        # This function should handle the asset issuance process
        pass

    async def search_incarcerated(event):
        # Implement logic to search for an incarcerated entity
        # This function should handle displaying the selected entity details in entity_details_container
        print("Search button clicked")
        selected_entity_id = "123456"  # Example entity ID
        await event.page.go_async(f"/issue_assets/entity_assets/{selected_entity_id}")

    async def search_employee(event):
        # Implement logic to search for an employee entity
        # This function should handle displaying the selected entity details in entity_details_container
        print("Search button clicked")
        await event.page.go_async("/issue_assets/entity_assets")

    async def search_location(event):
        # Implement logic to search for a location entity
        # This function should handle displaying the selected entity details in entity_details_container
        print("Search button clicked")
        await event.page.go_async("/issue_assets/entity_assets")

    # Custom AppBar using Container with the app's primary theme color
    custom_appbar = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Issue Assets",
                    size=18,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
        bgcolor=ft.colors.INVERSE_PRIMARY,
        height=40,  # Set the height of the AppBar
    )

    # TextField for entering asset number to be issued
    asset_id_input = ft.TextField(
        label="Enter asset number to issue:",
        autofocus=False,
        expand=True,
    )

    # Card for issuing assets
    issue_asset_row = ft.Row(
        [
            asset_id_input,
            ft.ElevatedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.ASSIGNMENT_TURNED_IN_OUTLINED),
                        ft.Text("Issue Asset", size=16),
                    ],
                    height=60,
                ),
                on_click=issue_asset_to_entity,
            ),
        ]
    )

    entity_details_row = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Entity details will appear here after one is selected."),
                ],
            ),
        ],
        expand=True,
    )

    icarcerated_input = ft.TextField(
        label="Enter DOC Number:",
        autofocus=True,
        expand=True,
        on_submit=search_incarcerated,
    )

    incarcerated_tab = ft.Tab(
        text="Incarcerated",
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            icarcerated_input,
                            ft.ElevatedButton(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.icons.SEARCH),
                                        ft.Text("Search", size=16),
                                    ],
                                    height=60,
                                ),
                                on_click=search_incarcerated,
                            ),
                        ],
                    ),
                ]
            ),
            padding=10,
        ),
        visible=True,
    )

    employee_input = ft.TextField(
        label="Enter Employee ID:",
        autofocus=True,
        expand=True,
        on_submit=search_employee,
    )

    employee_tab = ft.Tab(
        text="Employee",
        content=ft.Container(
            content=ft.Row(
                [
                    employee_input,
                    ft.ElevatedButton(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.SEARCH),
                                ft.Text("Search", size=16),
                            ],
                            height=60,
                        ),
                        on_click=search_employee,
                    ),
                ],
            ),
            padding=10,
        ),
        visible=True,
    )

    location_input = ft.TextField(
        label="Enter Location:",
        autofocus=True,
        expand=True,
        on_submit=search_location,
    )

    location_tab = ft.Tab(
        text="Location",
        content=ft.Container(
            content=ft.Row(
                [
                    location_input,
                    ft.ElevatedButton(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.SEARCH),
                                ft.Text("Search", size=16),
                            ],
                            height=60,
                        ),
                        on_click=search_location,
                    ),
                ],
            ),
            padding=10,
        ),
        visible=True,
    )

    # Tabs for selecting entity type
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        height=130,
        tabs=[
            incarcerated_tab,
            employee_tab,
            location_tab,
        ],
    )

    entity_search_card = ft.Card(
        content=ft.Row([tabs], expand=True),
        visible=True,
    )

    async def radiogroup_changed(event):
        # TODO Implement logic to change the entity search card based on the selected radio button
        pass

    search_type_selector = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="incarcerated", label="Incarcerated"),
                ft.Radio(value="employee", label="Employee"),
                ft.Radio(value="location", label="Location"),
            ]
        ),
        on_change=radiogroup_changed,
    )

    return ft.Column(
        [
            custom_appbar,
            # search_type_selector,
            entity_search_card,
        ],
        expand=True,
    )
