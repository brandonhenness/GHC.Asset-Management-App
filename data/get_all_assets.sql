SELECT
	a.asset_type,
	a.asset_status,
	a.asset_id,
	l.laptop_serial_number,
	l.laptop_manufacturer,
	l.laptop_model,
	t.transaction_type,
	t.transaction_timestamp,
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name

FROM assets a
LEFT JOIN laptops l ON a.asset_id = l.asset_id
LEFT JOIN transactions t ON t.asset_id = a.asset_id
LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
LEFT JOIN users u ON i.entity_id = u.entity_id
WHERE a.asset_type = 'LAPTOP'
AND (t.transaction_id IS NULL OR 
	 t.transaction_timestamp = (
	SELECT MAX(transaction_timestamp)
	FROM transactions
	WHERE asset_id = a.asset_id
))
ORDER BY a.asset_id ASC;
