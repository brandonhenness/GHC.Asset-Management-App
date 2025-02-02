SELECT
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
-- 	COUNT(ia.asset_id) AS issued_entities_count,
	ia.asset_id,
	a.asset_type,
	t.transaction_id,
	t.transaction_notes
FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN users u ON t.entity_id = u.entity_id
LEFT JOIN incarcerated i ON u.entity_id = i.entity_id
LEFT JOIN enrollments e ON i.entity_id = e.entity_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
WHERE e.schedule_id IS NULL
-- GROUP BY doc_number, last_name, first_name, middle_name, transaction_id, transaction_notes
ORDER BY doc_number