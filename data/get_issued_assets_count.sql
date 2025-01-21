SELECT DISTINCT
	i.entity_id,
	i.doc_number,
	COUNT(ia.asset_id)

FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN incarcerated i ON t.entity_id = i.entity_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
GROUP BY i.entity_id, i.doc_number
ORDER BY i.entity_id ASC