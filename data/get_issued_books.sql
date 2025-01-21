SELECT DISTINCT
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	ia.asset_id,
	a.asset_type,
	b.book_isbn,
	ba.book_number,
	b.book_title
FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN users u ON t.entity_id = u.entity_id
LEFT JOIN incarcerated i ON u.entity_id = i.entity_id
LEFT JOIN enrollments e ON i.entity_id = e.entity_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
LEFT JOIN book_assets ba ON a.asset_id = ba.asset_id
LEFT JOIN books b ON ba.book_isbn = b.book_isbn
WHERE a.asset_type = 'BOOK'
ORDER BY book_isbn, doc_number;