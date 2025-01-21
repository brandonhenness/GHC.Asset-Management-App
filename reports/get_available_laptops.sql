WITH enrolled_transactions AS (
	SELECT
		t.entity_id,
		a.asset_id,
		t.transaction_type,
		t.transaction_timestamp,
		ROW_NUMBER() OVER (PARTITION BY t.entity_id ORDER BY t.transaction_timestamp DESC) AS rn
	FROM enrollments e
	LEFT JOIN transactions t ON t.entity_id = e.entity_id
	JOIN assets a ON t.asset_id = a.asset_id
	WHERE a.asset_type = 'LAPTOP' AND a.asset_status = 'IN_SERVICE'
),
available_laptops AS (
	SELECT
		a.asset_id
	FROM assets a
	LEFT JOIN enrolled_transactions et ON et.asset_id = a.asset_id AND et.rn = 1
	WHERE a.asset_type = 'LAPTOP'
		AND a.asset_status = 'IN_SERVICE'
		AND et.entity_id IS NULL
		AND a.asset_id NOT IN (SELECT asset_id FROM issued_assets)
)
SELECT DISTINCT
	asset_id
FROM available_laptops