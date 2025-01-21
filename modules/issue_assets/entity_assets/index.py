import flet as ft
import re
import repath


def main(page: ft.Page):
    print(f"Displaying navigation item for route: {page.route}")
    # Define the route pattern for dynamic routes
    pattern = repath.pattern("/issue_assets/entity_assets/:entity_id")
    match = re.match(pattern, page.route)

    entity_id = None
    if match:
        params = match.groupdict()
        # Extract the entity_id parameter for a dynamic route
        entity_id = params["entity_id"]
    return ft.Container(content=ft.Text(f"Incarcerated: {entity_id}", size=16))
