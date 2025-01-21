-- Imports book details (title, publisher, etc.) into the Asset Manangement System database.

--- Setting 'AMS_import' does three things:
---    A) It tells the Asset Management System the CSV file is input (not output)
---    B) Python-style parameters ( %(column)s ) are filled in from each CSV row
---    C) All " %(parameters)s " are quoted programmatically (not in this query)
---       (otherwise " NULL " would render as " 'NULL' " which doesn't work)

--- Setting 'AMS_insert_tables' to a list of tables does these two things:
---    A) AMS 'sniffs' these DB tables to replace '' in the CSV data with NULL
---    B) AMS 'sniffs' these DB tables to quote strings and text, but not numbers
---
--- We could parse " INSERT INTO assets ( " with a regular expression, but that
--- can get messy, especially if we are working with temporary tables.

-- :defaults => { 'AMS_import': True, 'AMS_returning': 'book_title', 'AMS_insert_tables': [ 'assets', 'book_assets', 'books' ] }
--- This lists 'assets' & 'book_assets', even though we only INSERT into the 'books' table

--- There are two kinds of parameter substitutions in this query:
--- >>> INSERT INTO assets ( asset_id, asset_type, asset_cost, asset_status )
---     VALUES ( %(asset_id)s, 'CALCULATOR', :asset_cost, 'IN_SERVICE' )
---
--- 		A) " :asset_cost  " is immediately replaced, so it stays static
--- 		B) " %(asset_id)s " is read from each CSV row, so it is UNIQUE
---
--- Queries should not mix the Python-legacy " %(parameter)s " (*) and
--- the '%' SQL wildcard character in the same line of query text; it can
--- easily throw a KeyError exception or confuse AMS parameter parsing.
---
--- (*) http://ghc.edu/docs/python/library/stdtypes.html#old-string-formatting

INSERT INTO books (
	book_isbn,
	book_title,
	book_author,
	book_publisher,
	book_edition,
	book_year
)
VALUES
(
	%(book_isbn)s,
	%(book_title)s,
	%(book_author)s,
	%(book_publisher)s,
	%(book_edition)s,
	%(book_year)s
)
ON CONFLICT (book_isbn) DO UPDATE
SET
--- This is the default syntax for handling 'ON CONFLICT (...) DO UPDATE' columns:
---	   asset_id = EXCLUDED.asset_id,
---
--- Since we always know these values, we can fill them in ourselves ...
	book_isbn      = %(book_isbn)s,
	book_title     = %(book_title)s,
	book_author    = %(book_author)s,
	book_publisher = %(book_publisher)s,
	book_edition   = %(book_edition)s,
	book_year      = %(book_year)s
RETURNING
	books.book_title
;