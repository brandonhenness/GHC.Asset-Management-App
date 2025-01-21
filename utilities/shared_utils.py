# shared_utils.py
import flet as ft


def create_custom_appbar(title, theme_color=ft.colors.INVERSE_PRIMARY):
    return ft.Container(
        content=ft.Row(
            [ft.Text(title, size=18)],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
        bgcolor=theme_color,
        height=40,
    )
