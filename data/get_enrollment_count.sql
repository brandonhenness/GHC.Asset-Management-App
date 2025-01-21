DROP FUNCTION IF EXISTS GetStudentEnrollments();
DROP TYPE IF EXISTS student_enrollments_results_set;
CREATE TYPE student_enrollments_results_set AS (
	doc_number VARCHAR(255),
	last_name VARCHAR(255),
	first_name VARCHAR(255),
	middle_name VARCHAR(255),
	course_prefix VARCHAR(255),
	course_code VARCHAR(255),
	course_name VARCHAR(255),
	course_instructor VARCHAR(255),
	course_count BIGINT
);

CREATE OR REPLACE FUNCTION GetStudentEnrollments()
RETURNS SETOF student_enrollments_results_set AS $$
BEGIN
	CREATE TEMP TABLE tmp_enrollment_count AS
	SELECT
		entity_id,
		COUNT(schedule_id) AS course_count
	FROM enrollments
	GROUP BY entity_id;

	RETURN QUERY
	SELECT
		i.doc_number,
		u.last_name,
		u.first_name,
		u.middle_name,
		c.course_prefix,
		c.course_code,
		c.course_name,
		cs.course_instructor,
		tec.course_count
	FROM incarcerated i
	RIGHT JOIN enrollments e ON i.entity_id = e.entity_id
	LEFT JOIN users u ON e.entity_id = u.entity_id
	LEFT JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
	LEFT JOIN courses c ON cs.course_id = c.course_id
	LEFT JOIN tmp_enrollment_count tec ON e.entity_id = tec.entity_id
	ORDER BY i.doc_number, c.course_prefix, c.course_code, cs.course_instructor;

	DROP TABLE tmp_enrollment_count;
END;
$$ LANGUAGE plpgsql;