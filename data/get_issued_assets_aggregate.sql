WITH issued_assets AS (
	SELECT DISTINCT
		i.doc_number,
		CONCAT(u.last_name, ', ', u.first_name, ' ', u.middle_name) AS name,
		COALESCE(i.facility, '') AS facility,
		COALESCE(i.housing_unit, '') AS unit,
		COALESCE(i.housing_cell, '') AS bed,
		COALESCE(i.counselor, '') AS counselor,
		a.asset_status,
		ia.asset_id,
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
			ELSE ''
		END AS secondary_identifier,
		CONCAT(cr.course_prefix, cr.course_code) AS course,
		COALESCE(cs.course_instructor, '') AS course_instructor
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
	LEFT JOIN course_schedules cs ON cs.schedule_id = e.schedule_id
	LEFT JOIN courses cr ON cr.course_id = cs.course_id
),
issued_accessories AS (
	SELECT DISTINCT
		i.doc_number,
		CONCAT(u.last_name, ', ', u.first_name, ' ', u.middle_name) AS name,
		COALESCE(i.facility, '') AS facility,
		COALESCE(i.housing_unit, '') AS unit,
		COALESCE(i.housing_cell, '') AS bed,
		COALESCE(i.counselor, '') AS counselor,
		a.asset_status,
		ia.asset_id,
		a.asset_type,
		CASE 
			WHEN a.asset_type = 'CHARGER' THEN CONCAT(a.asset_type, ' (', a.asset_id, ')')
			WHEN a.asset_type = 'HEADPHONES' THEN CAST(a.asset_type AS VARCHAR)
			ELSE ''
		END AS asset_name,
		'' AS secondary_identifier,
		CONCAT(cr.course_prefix, cr.course_code) AS course,
		COALESCE(cs.course_instructor, '') AS course_instructor
	FROM issued_accessories ia
	LEFT JOIN transactions t ON ia.transaction_id = t.transaction_id
	LEFT JOIN users u ON ia.entity_id = u.entity_id
	LEFT JOIN incarcerated i ON ia.entity_id = i.entity_id
	LEFT JOIN enrollments e ON ia.entity_id = e.entity_id
	LEFT JOIN assets a ON ia.asset_id = a.asset_id
	LEFT JOIN course_schedules cs ON cs.schedule_id = e.schedule_id
	LEFT JOIN courses cr ON cr.course_id = cs.course_id
	WHERE a.asset_type != 'HEADPHONES'
),
combined_issued AS (
	SELECT 
		doc_number,
		name,
		facility,
		unit,
		bed,
		counselor,
		asset_status,
		asset_id,
		asset_type,
		asset_name,
		secondary_identifier,
		STRING_AGG(DISTINCT course, ', ') AS courses,
		STRING_AGG(DISTINCT course_instructor, ', ') AS course_instructors
	FROM (
		SELECT * FROM issued_assets
		UNION ALL
		SELECT * FROM issued_accessories
	) AS combined
	GROUP BY 
		doc_number,
		name,
		facility,
		unit,
		bed,
		counselor,
		asset_status,
		asset_id,
		asset_type,
		asset_name,
		secondary_identifier
)
SELECT *
FROM combined_issued
ORDER BY course_instructors, doc_number;
