-- This report runs an ad hoc query, most likely related to reverse-engineering SQLAlchemy.

--- SELECT * from book_assets
--- WHERE book_assets.book_isbn = '9780495902867';

SELECT * from book_assets
WHERE asset_id = 'EDU4759';

--- -- A quick query of all calculators, for inventory use ...

-- SELECT assets.*, '>> CALCULATOR INFORMATION >>' as calculator_A, calculators.*
-- FROM assets, calculators
-- WHERE
-- 	calculators.asset_id  = assets.asset_id
-- ORDER BY
--     assets.asset_id ASC
-- ;



-- SELECT assets.*, '>> BOOKS ASSET >>' as book_assets_A, book_assets.*, '>> BOOKS INFO >>' as books_B, books.*
-- FROM assets, book_assets, books
-- WHERE
-- 	    book_assets.asset_id  = assets.asset_id
-- 	AND book_assets.book_isbn = books.book_isbn
---	AND assets.asset_cost IS NOT NULL
-- ORDER BY
--     books.book_title ASC
--- ,
---	book_assets.book_isbn ASC,
---	assets.asset_id ASC



--- THIS IS USEFUL FOR CHECKING types_and_tables.txt IS NOT MISSING ANY TYPES / TABLES / COLUMNS


--- Queries the information_schema for all available column properties
--- Decided to use 'is_nullable' and 'data_type', for SQL 'NULL' columns 
--- and dynamically quoting / not quoting INSERT-ed strings and numbers/NULL
---

--- SELECT *
--- FROM   information_schema.columns
--- WHERE  table_name = 'laptops' 
--- ORDER BY
---     table_schema ASC,
---     table_name ASC
--- ;



--- THIS WAS USED TO FIX UP 'document_file_name' ERRORS CAUSED BY A TEMPORARY BUG
--- WHERE A FEW ROWS INCLUDED DIRECTORY + FILE, INSTEAD OF JUST THE FILE NAME

--- SELECT
--- 	document_id,
--- 	document_file_name
--- FROM
--- 	documents
--- ORDER BY
---  document_file_name ASC;


--- A bit of Python code to generate the UPDATE statements to fix the affected records:

--- broken_data = {
--- # 'ID': 'corrected_file_name',
--- '2124': '320017_20241004092106.pdf',
--- '2578': '320017_20241004092106.pdf',
--- '1705': '320017_20241004092106.pdf',
--- '313':  '320017_20241004092106.pdf',
--- '1228': '320017_20241004092106.pdf',
--- '923':  '340027_20241004090931.pdf',
--- '2579': '426692_20241007095619.pdf',
--- '1933': '426692_20241007095619.pdf',
--- '2526': '426692_20241007095619.pdf',
--- '2261': '426692_20241007095619.pdf',
--- '2580': '426692_20241007095619.pdf',
--- '1336': '426692_20241007095619.pdf',
--- '2021': '440994_20241004091333.pdf',
--- '2576': '440994_20241004091333.pdf'
--- }
--- 
--- for doc_id in broken_data: print( f"UPDATE documents SET document_file_name = '{broken_data[doc_id]}' WHERE document_id = {doc_id} RETURNING document_id;" )
