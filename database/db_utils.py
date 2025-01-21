from database.models import Transaction


def get_transaction_by_asset_id(asset_id, session):
    # Return the latest transaction for the given asset_id
    return (
        session.query(Transaction)
        .filter(Transaction.asset_id == asset_id)
        .order_by(Transaction.transaction_timestamp.desc())
        .first()
    )
