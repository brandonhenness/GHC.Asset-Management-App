from database.models import *
import flet as ft
from flet import (
    app,
    Page,
    ElevatedButton,
    AppBar,
    View,
    Text,
    colors,
    IconButton,
    icons,
)

# Initialize the database
from database.database import Session, init_db

init_db()


class BaseRoute:
    def __init__(self, page: Page):
        self.page = page

    def create_view(self):
        raise NotImplementedError("create_view must be implemented in subclasses")


class MainRoute(BaseRoute):
    def create_view(self):
        return View(
            "/",
            [
                AppBar(
                    title=Text("Asset Management App"),
                    bgcolor=colors.SURFACE_VARIANT,
                ),
                ElevatedButton(
                    "Issue Assets", on_click=lambda _: self.page.go("/issue")
                ),
                ElevatedButton(
                    "Return Assets", on_click=lambda _: self.page.go("/return")
                ),
            ],
        )


class IssueRoute(BaseRoute):
    def create_view(self):
        return View(
            "/issue",
            [
                AppBar(
                    leading=IconButton(
                        icon=icons.ARROW_BACK, on_click=lambda _: self.page.go("/")
                    ),
                    title=Text("Issue Assets"),
                    bgcolor=colors.SURFACE_VARIANT,
                ),
                ElevatedButton("Go to Root", on_click=lambda _: self.page.go("/")),
            ],
        )


class ReturnRoute(BaseRoute):
    def create_view(self):
        return View(
            "/return",
            [
                AppBar(
                    leading=IconButton(
                        icon=icons.ARROW_BACK, on_click=lambda _: self.page.go("/")
                    ),
                    title=Text("Return Assets"),
                    bgcolor=colors.SURFACE_VARIANT,
                ),
                ElevatedButton("Go to Root", on_click=lambda _: self.page.go("/")),
            ],
        )


def main(page: Page):
    page.title = "Asset Management App"

    routes = {
        "/": MainRoute(page),
        "/issue": IssueRoute(page),
        "/return": ReturnRoute(page),
    }

    def route_change(event):
        page.views.clear()
        route_path = event.route
        if route_path in routes:
            view = routes[route_path].create_view()
            page.views.append(view)
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    app(target=main)
