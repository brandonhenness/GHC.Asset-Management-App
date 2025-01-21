WITH RankedTransactions AS (
	SELECT
		t.entity_id,
		a.asset_id,
		t.transaction_type,
		t.transaction_timestamp,
		l.laptop_serial_number,
		l.laptop_manufacturer,
		l.laptop_model,
		ROW_NUMBER() OVER (PARTITION BY t.entity_id ORDER BY t.transaction_timestamp DESC) AS rn
	FROM transactions t
	JOIN assets a ON t.asset_id = a.asset_id
	LEFT JOIN laptops l ON a.asset_id = l.asset_id
	WHERE a.asset_type = 'LAPTOP' AND a.asset_status = 'IN_SERVICE'
)
SELECT DISTINCT
	i.entity_id,
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	STRING_AGG(CONCAT(c.course_prefix, c.course_code), ', ' ORDER BY CONCAT(c.course_prefix, c.course_code)) AS enrolled_courses,
	a.asset_type,
	a.asset_status,
	a.asset_id,
	rt.laptop_serial_number,
	rt.laptop_manufacturer,
	rt.laptop_model,
	rt.transaction_type,
	rt.transaction_timestamp
FROM incarcerated i
LEFT JOIN users u ON i.entity_id = u.entity_id
RIGHT JOIN enrollments e ON i.entity_id = e.entity_id
LEFT JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
LEFT JOIN courses c ON cs.course_id = c.course_id
LEFT JOIN RankedTransactions rt ON i.entity_id = rt.entity_id AND rt.rn = 1
LEFT JOIN assets a ON rt.asset_id = a.asset_id
GROUP BY
	i.entity_id,
	i.doc_number,
	u.last_name,
	u.first_name,
	u.middle_name,
	a.asset_type,
	a.asset_status,
	a.asset_id,
	rt.laptop_serial_number,
	rt.laptop_manufacturer,
	rt.laptop_model,
	rt.transaction_type,
	rt.transaction_timestamp
ORDER BY i.doc_number ASC;