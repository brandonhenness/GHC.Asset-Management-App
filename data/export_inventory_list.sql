SELECT DISTINCT
	a.asset_id,
	a.asset_type,
	CASE 
		WHEN a.asset_type = 'BOOK' THEN CONCAT(b.book_title, ' (ISBN: ', b.book_isbn, ')')
		WHEN a.asset_type = 'CALCULATOR' THEN CONCAT(c.calculator_model, ' ', c.calculator_color)
		WHEN a.asset_type = 'LAPTOP' THEN d.laptop_model
		ELSE ''
	END AS asset_name,
	CASE 
		WHEN a.asset_type = 'BOOK' THEN ba.book_number
		WHEN a.asset_type = 'LAPTOP' THEN d.laptop_serial_number
		WHEN a.asset_type = 'CALCULATOR' THEN c.calculator_manufacturer_date_code
		ELSE ''
	END AS secondary_identifier,
	a.asset_status
FROM assets a
LEFT JOIN book_assets ba ON a.asset_id = ba.asset_id
LEFT JOIN books b ON ba.book_isbn = b.book_isbn
LEFT JOIN calculators c ON a.asset_id = c.asset_id
LEFT JOIN laptops d ON a.asset_id = d.asset_id
WHERE
	NOT asset_status::text = 'DECOMMISSIONED'
	AND NOT a.asset_type IN ('HEADPHONES', 'CHARGER')
ORDER BY asset_status, asset_type, asset_id;

