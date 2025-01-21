WITH ExclusiveInstructor AS (
	SELECT i.entity_id
	FROM enrollments e
	JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
	JOIN courses c ON cs.course_id = c.course_id
	JOIN incarcerated i ON e.entity_id = i.entity_id
	GROUP BY i.entity_id
	HAVING SUM(CASE WHEN cs.course_instructor = 'Burke, Donald' THEN 1 ELSE 0 END) = COUNT(*)
)

SELECT DISTINCT
    i.doc_number,
	CONCAT(u.last_name, ', ', u.first_name, ' ', u.middle_name) AS name,
	i.facility,
	i.housing_unit AS unit,
	i.housing_cell AS bed,
	i.counselor,
    ia.asset_id,
    a.asset_type,
    CASE 
        WHEN a.asset_type = 'BOOK' THEN CONCAT(b.book_title, ' (ISBN: ', b.book_isbn, ')')
        WHEN a.asset_type = 'CALCULATOR' THEN CONCAT(c.calculator_model, ' ', c.calculator_color)
        WHEN a.asset_type = 'LAPTOP' THEN d.laptop_model
        ELSE NULL
    END AS asset_name,
    CASE 
        WHEN a.asset_type = 'BOOK' THEN ba.book_number
        WHEN a.asset_type = 'CALCULATOR' THEN NULL
        WHEN a.asset_type = 'LAPTOP' THEN d.laptop_serial_number
        ELSE NULL
    END AS secondary_identifier,
	CONCAT(crs.course_prefix, crs.course_code) AS course_code,
	crs.course_name,
	cs.course_instructor
FROM issued_assets ia
LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
LEFT JOIN users u ON t.entity_id = u.entity_id
LEFT JOIN incarcerated i ON u.entity_id = i.entity_id
LEFT JOIN enrollments e ON i.entity_id = e.entity_id
LEFT JOIN assets a ON ia.asset_id = a.asset_id
LEFT JOIN book_assets ba ON a.asset_id = ba.asset_id
LEFT JOIN books b ON ba.book_isbn = b.book_isbn
LEFT JOIN calculators c ON a.asset_id = c.asset_id
LEFT JOIN laptops d ON a.asset_id = d.asset_id
LEFT JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
LEFT JOIN courses crs ON cs.course_id = crs.course_id
WHERE a.asset_type IN ('BOOK', 'CALCULATOR', 'LAPTOP')
	AND i.entity_id IN (SELECT entity_id FROM ExclusiveInstructor)
ORDER BY doc_number;
