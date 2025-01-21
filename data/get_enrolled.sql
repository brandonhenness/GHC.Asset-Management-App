SELECT
	i.doc_number,
	i.entity_id
FROM incarcerated i
RIGHT JOIN enrollments e ON i.entity_id = e.entity_id
-- FROM enrollments e
-- LEFT JOIN incarcerated i ON e.entity_id = i.entity_id
-- LEFT JOIN transactions t ON e.entity_id = t.entity_id
-- LEFT JOIN issued_assets ia ON t.transaction_id = ia.transaction_id
-- WHERE ia.asset_id IS NULL and t.transaction_id IS NULL
ORDER BY i.doc_number