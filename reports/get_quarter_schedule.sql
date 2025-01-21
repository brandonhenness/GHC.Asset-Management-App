-- Returns course information, including class days and times, for a specific quarter
--
-- :scheduled_quarter => ["Spring", "Winter", "Fall", "Summer"]
--
-- [ 2025, 2024 ]
-- :scheduled_year => Enter a four-digit year
--
-- Doc for :scheduled_quarter
--     LIKE '%:scheduled_quarter%' matches around the quarter number embedded in "Winter (2241)".
--     This multi-data column is something to refactor at some future point in time.
--
-- Doc for :scheduled_year
--     The options for this parameter could be queried out of the database with:
--         SELECT DISTINCT(scheduled_year) FROM course_schedules ORDER BY scheduled_year DESC
-- 

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
	cs.scheduled_quarter LIKE '%:scheduled_quarter%'
	AND cs.scheduled_year = :scheduled_year