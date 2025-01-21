SELECT DISTINCT
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	ia.asset_id,
	a.asset_type,
	c.calculator_model,
	c.calculator_color
FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN users u ON t.entity_id = u.entity_id
LEFT JOIN incarcerated i ON u.entity_id = i.entity_id
LEFT JOIN enrollments e ON i.entity_id = e.entity_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
LEFT JOIN calculators c ON a.asset_id = c.asset_id
WHERE a.asset_type = 'CALCULATOR'
ORDER BY asset_id, doc_number;