SELECT 
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	d.document_id,
	COUNT(ia.asset_id) AS asset_count

FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
LEFT JOIN users u ON i.entity_id = u.entity_id
LEFT JOIN transaction_documents td ON t.transaction_id = td.transaction_id
LEFT JOIN documents d ON td.document_id = d.document_id
WHERE d.document_printed_timestamp is null
GROUP BY i.doc_number, u.last_name, u.first_name, u.middle_name, d.document_printed_timestamp, d.document_id
ORDER BY u.last_name ASC