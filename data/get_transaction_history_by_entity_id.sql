SELECT
	t.transaction_timestamp,
	t.transaction_id,
	t.transaction_type,
	a.asset_id,
	a.asset_type,
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name
FROM transactions t
LEFT JOIN assets a ON t.asset_id = a.asset_id
LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
LEFT JOIN users u ON t.entity_id = u.entity_id
WHERE t.entity_id = '555'
ORDER BY t.transaction_id ASC