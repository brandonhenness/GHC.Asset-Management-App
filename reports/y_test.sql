-- This report runs a random testing-related query.

--- INSERT INTO assets (
---         asset_id,
---         asset_type,
---         asset_cost,
---         asset_status
--- )
--- VALUES
--- (
---         'EDU0680',
---         'CALCULATOR',
---         24.99,  'IN_SERVICE'
--- )
-- ON CONFLICT (asset_id) DO UPDATE
-- SET
-- ---	   asset_id = EXCLUDED.asset_id,
	-- asset_id                          = 'EDU0680',
	-- asset_type = 'CALCULATOR',
    -- asset_cost = 24.99,
    -- asset_status = 'IN_SERVICE'
-- RETURNING asset_id;

--- SELECT COUNT(*)
--- FROM assets;

-- SELECT
--     assets.asset_id, assets.asset_type, assets.asset_cost,
--     assets.asset_status, laptops.laptop_model,
-- 	laptops.laptop_serial_number, laptops.laptop_manufacturer,
-- 	laptops.laptop_drive_serial_number, laptops.laptop_ram,
-- 	laptops.laptop_cpu, laptops.laptop_storage,
-- 	laptops.laptop_bios_version
-- FROM
--     assets, laptops
-- WHERE
--     asset_cost > 700 AND assets.asset_id = laptops.asset_id
-- ORDER BY
--     asset_id DESC;


-- UPDATE assets
-- SET asset_status = 'MISSING'
-- WHERE asset_id = 'EDU3785'
-- RETURNING asset_id;

-- SELECT * FROM book_assets WHERE book_isbn = '9780357717189' ORDER BY book_number ASC

-- SELECT * from assets WHERE asset_status not in ( 'IN_SERVICE', 'DECOMMISSIONED' )

-- SELECT incarcerated.doc_number
-- FROM incarcerated, users
-- WHERE users.last_name = 'ZHANG' AND users.entity_id = incarcerated.entity_id

SELECT
    *
FROM book_assets
WHERE
    book_assets.book_isbn = '9780495902867'
ORDER BY
    book_assets.asset_id ASC
---	,
---	book_assets.book_isbn ASC,
---	assets.asset_id ASC