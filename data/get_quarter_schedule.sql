SELECT
	CONCAT(c.course_prefix, c.course_code) AS course_code,
	c.course_name,
	cs.course_instructor,
	cs.course_location,
	cs.course_days,
	cs.course_start_time,
	cs.course_end_time,
	cs.course_start_date,
	cs.course_end_date,
	c.course_credits,
	c.course_description,
	c.course_outcomes
FROM
	course_schedules AS cs
	JOIN courses AS c ON cs.course_id = c.course_id
WHERE
	cs.scheduled_quarter LIKE '%Summer%'
	AND cs.scheduled_year = 2024
	