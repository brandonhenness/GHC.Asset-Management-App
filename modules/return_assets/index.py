import flet as ft
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.database import AsyncSessionLocal
from database.models import Transaction, IssuedAsset, Asset, Entity, User

# TODO add logging


def main(page: ft.Page):
    async def return_asset(event):
        asset_id = asset_id_input.value
        if not asset_id:
            await on_error(event, message="Please enter an asset number.")
            # Clear the input field and set focus
            asset_id_input.value = ""
            await asset_id_input.focus_async()
            await event.control.page.update_async()
            return

        async with AsyncSessionLocal() as session:  # Use AsyncSession for async operations
            try:
                asset_status = await check_asset_status(asset_id, session)

                # Ensure that asset is issued before proceeding
                if asset_status["status"] != "Asset is issued":
                    raise ValueError(asset_status["status"])

                return_transaction = Transaction(
                    asset_id=asset_status["asset"].asset_id,
                    entity_id=asset_status["issued_to"].entity_id,
                    transaction_type="RETURNED",
                )
                session.add(return_transaction)

                await session.commit()  # Commit using await
                await on_success(event, asset_status=asset_status)
            except Exception as e:
                await session.rollback()  # Rollback using await
                error_message = str(e)
                await on_error(event, message=error_message)
            finally:
                # Clear the input field and set focus
                asset_id_input.value = ""
                await asset_id_input.focus_async()
                await event.control.page.update_async()

    async def check_asset_status(asset_id: str, session: AsyncSession):
        # Async query for IssuedAsset
        result = await session.execute(
            select(IssuedAsset).filter(IssuedAsset.asset_id == asset_id)
        )
        issued_asset = result.scalars().first()

        if issued_asset:
            # Async query for the last transaction
            result = await session.execute(
                select(Transaction)
                .filter(Transaction.asset_id == asset_id)
                .order_by(Transaction.transaction_timestamp.desc())
            )
            last_transaction = result.scalars().first()

            # Fetch the entity with its specific type
            entity = None
            if last_transaction:
                result = await session.execute(
                    select(Entity).filter(
                        Entity.entity_id == last_transaction.entity_id
                    )
                )
                entity = result.scalars().first()

                if isinstance(entity, User):
                    result = await session.execute(
                        select(User).filter(User.entity_id == entity.entity_id)
                    )
                    entity = result.scalars().first()

            return {
                "status": "Asset is issued",
                "asset": issued_asset,
                "last_transaction": last_transaction,
                "issued_to": entity,
            }

        # Async query for Asset
        result = await session.execute(select(Asset).filter(Asset.asset_id == asset_id))
        asset = result.scalars().first()

        if asset:
            return {"status": "Asset exists but is not issued", "asset": asset}
        else:
            return {"status": "Asset does not exist"}

    async def on_success(event, asset_status=None):
        if asset_status:
            asset_details_content = ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Asset Details", size=24, weight=ft.FontWeight.BOLD
                            ),
                            ft.Divider(),
                            ft.Row(
                                [
                                    ft.Text("Asset ID:", weight=ft.FontWeight.BOLD),
                                    ft.Text(asset_status["asset"].asset_id),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Text("Asset Type:", weight=ft.FontWeight.BOLD),
                                    ft.Text(asset_status["asset"].asset_type.name),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        "Last Transaction ID:",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        str(
                                            asset_status[
                                                "last_transaction"
                                            ].transaction_id
                                        )
                                    ),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        "Issued To Entity ID:",
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(str(asset_status["issued_to"].entity_id)),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        "Issued To Name:", weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Text(
                                        f"{asset_status['issued_to'].first_name} {asset_status['issued_to'].last_name}"
                                    ),
                                ]
                            ),
                            # Add more details as needed
                        ],
                        spacing=5,
                    )
                ],
                expand=True,
            )
            asset_details_card.content = asset_details_content
            asset_details_card.visible = True

        event.control.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Text(
                        f"Successfully returned asset!",
                        color=ft.colors.WHITE,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.GREEN,
        )
        event.control.page.snack_bar.open = True
        await event.control.page.update_async()

    async def on_error(event, message):
        print(f"Error: {message}")
        event.control.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Text(
                        f"Error during asset return: {message}",
                        color=ft.colors.WHITE,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.RED,
        )
        event.control.page.snack_bar.open = True
        await event.control.page.update_async()

    # Custom AppBar using Container with the app's primary theme color
    custom_appbar = ft.Container(
        content=ft.Row(
            [
                ft.Text(
                    "Return Assets",
                    size=18,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
        bgcolor=ft.colors.INVERSE_PRIMARY,
        height=40,  # Set the height of the AppBar
    )

    # UI Elements
    asset_id_input = ft.TextField(
        label="Enter asset number:",
        autofocus=True,
        expand=True,
        on_submit=return_asset,
    )
    return_button = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.ASSIGNMENT_RETURN_OUTLINED),
                ft.Text("Return Asset", size=16),
            ],
            height=60,
        ),
        on_click=return_asset,
    )

    # Card content with asset_id_input and return_button in the same row
    card_content = ft.Row(
        [
            asset_id_input,
            ft.Container(width=20),
            return_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        expand=True,
    )

    search_card = ft.Card(
        content=ft.Container(
            content=card_content,
            padding=20,
        )
    )

    asset_details_content = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Asset details will appear here after successful return."),
                ],
            ),
        ],
        expand=True,
    )

    # Additional card to display asset details
    asset_details_card = ft.Card(
        content=ft.Container(
            content=asset_details_content,
            padding=20,
        ),
        visible=False,  # Initially hidden
    )

    return ft.Column([custom_appbar, search_card, asset_details_card], expand=True)
