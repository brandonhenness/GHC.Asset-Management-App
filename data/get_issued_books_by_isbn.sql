SELECT DISTINCT
	b.book_isbn,
	b.book_title,
	ba.book_number,
	a.asset_id,
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	t.transaction_timestamp
FROM books b
LEFT JOIN book_assets ba ON b.book_isbn = ba.book_isbn
LEFT JOIN assets a ON ba.asset_id = a.asset_id
LEFT JOIN issued_assets ia ON a.asset_id = ia.asset_id
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN users u ON t.entity_id = u.entity_id
LEFT JOIN incarcerated i ON u.entity_id = i.entity_id
LEFT JOIN enrollments e ON i.entity_id = e.entity_id
WHERE b.book_isbn = '9781305871809' --AND t.transaction_id IS NOT NULL
ORDER BY book_isbn, book_number;