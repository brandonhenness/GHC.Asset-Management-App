-- Prints the currently checked out books, with user's names and transaction data
	
SELECT
    users.last_name, users.first_name, book_assets.asset_id, book_assets.book_number, books.book_title,
    transactions.transaction_type, transactions.transaction_timestamp
FROM
    users, transactions, issued_assets, book_assets, books
WHERE
	-- User names are connected through the transactions tied to issued_assets
    users.entity_id = transactions.entity_id
    AND transactions.transaction_id = issued_assets.transaction_id
	-- Book asset_id, number, and title are shown for each currently issued book
    AND book_assets.asset_id = issued_assets.asset_id
	AND book_assets.book_isbn = books.book_isbn
	-- link issued_assets to transactions through transaction ID
	-- (using the primary key of the larger table should be slightly faster)
    AND issued_assets.transaction_id = transactions.transaction_id
ORDER BY
    transactions.asset_id, transactions.transaction_id;
	
