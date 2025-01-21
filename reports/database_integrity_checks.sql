-- This report looks for assets that are missing from their child tables.
--
-- TODO: This query looks for books sharing an ISBN with different asset_cost values
--

SELECT 'BOOK' AS label, assets.asset_id
FROM   assets
WHERE  assets.asset_type = 'BOOK'
       AND assets.asset_id NOT IN( SELECT asset_id FROM book_assets )
UNION ALL
SELECT 'CALCULATOR' AS label, assets.asset_id
FROM   assets
WHERE  assets.asset_type = 'CALCULATOR'
       AND assets.asset_id NOT IN( SELECT asset_id FROM calculators )
UNION ALL
SELECT 'LAPTOP' AS label, assets.asset_id
FROM   assets
WHERE  assets.asset_type = 'LAPTOP'
       AND assets.asset_id NOT IN( SELECT asset_id FROM laptops );
