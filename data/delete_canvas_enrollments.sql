DELETE
FROM public.enrollments e
	USING public.courses c
WHERE e.course_id = c.id AND
	c.name LIKE '%HS+%' AND
	c.workflow_state = 'deleted' AND
	e.workflow_state = 'deleted';