SELECT DISTINCT
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	ia.asset_id

FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
LEFT JOIN users u ON i.entity_id = u.entity_id
LEFT JOIN transaction_documents td ON t.transaction_id = td.transaction_id
LEFT JOIN documents d ON td.document_id = d.document_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
WHERE a.asset_type = 'LAPTOP'
ORDER BY u.last_name ASC