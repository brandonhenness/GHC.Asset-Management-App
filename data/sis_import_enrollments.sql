WITH course_data AS (
    SELECT DISTINCT
		CASE 
			WHEN c.course_prefix || c.course_code IN ('TRANS000', 'GED000', 'HS+000', 'ABE&GED000', 'ABE&GED001', 'ABE&GED002', 'ABE&GED003', 'ABE&GED004', 'ABE&GED005')
			THEN v.new_course_id
			ELSE CONCAT(
				cs.scheduled_year,
				CASE
					WHEN cs.scheduled_quarter ILIKE '%Summer%' THEN 'SMR'
					WHEN cs.scheduled_quarter ILIKE '%Winter%' THEN 'WIN'
					WHEN cs.scheduled_quarter ILIKE '%Spring%' THEN 'SPR'
					WHEN cs.scheduled_quarter ILIKE '%Fall%' THEN 'FAL'
				END,
				'_', c.course_prefix, c.course_code
			)
		END AS course_id,
        cs.course_instructor,
        cs.scheduled_quarter,
        au.username AS student_user_id,
        (c.course_prefix || c.course_code IN ('TRANS000', 'GED000', 'HS+000', 'ABE&GED000', 'ABE&GED001', 'ABE&GED002', 'ABE&GED003', 'ABE&GED004', 'ABE&GED005')) AS is_special_course,
		i.doc_number
    FROM incarcerated i
    RIGHT JOIN enrollments e ON i.entity_id = e.entity_id
    LEFT JOIN course_schedules cs ON e.schedule_id = cs.schedule_id
    LEFT JOIN courses c ON cs.course_id = c.course_id
    LEFT JOIN db_student_info si ON i.doc_number = si.user_id
    LEFT JOIN db_auth_user au ON si.account_id = au.id
    LEFT JOIN LATERAL (
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','C&CR_1A')),
				(CONCAT('HS+_','ENGLISH_1A')),
				(CONCAT('HS+_','ENGLISH_2A')),
				(CONCAT('HS+_','GEOGRAPHY_1A')),
				(CONCAT('HS+_','HISTORY_1A')),
				(CONCAT('HS+_','MATH_1A')),
				(CONCAT('HS+_','MATH_2A')),
				(CONCAT('HS+_','SOC_A')),
				(CONCAT('HS+_','LIFE_SCIENCE_A')),
				(CONCAT('HS+_','OED_A')),
				(CONCAT('HS+_','PORT_A')),
				(CONCAT('HS+_','H&F_A')),
				(CONCAT('HS+_','US_HIST_ART_A')),
				(CONCAT('HS+_','WA_HIST_ART_A')),
				(CONCAT('HS+_','ALG_I_A')),
				(CONCAT('HS+_','ALG_II_A')),
				(CONCAT('HS+_','ART_A')),
				(CONCAT('HS+_','CW_A')),
				(CONCAT('HS+_','EMP_SKILS_A')),
				(CONCAT('HS+_','ENGL_A')),
				(CONCAT('HS+_','GEN_SCI_A')),
				(CONCAT('HS+_','GEOM_A')),
				(CONCAT('HS+_','ANATOMY_A')),
				(CONCAT('HS+_','IS_ART_A')),
				(CONCAT('HS+_','LAB_SCI_A')),
				(CONCAT('HS+_','MED_BI_A')),
				(CONCAT('HS+_','PYS_ED_A')),
				(CONCAT('HS+_','ANG_MGMT_A'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED000'
		UNION ALL
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','C&CR_1A')),
				(CONCAT('HS+_','ENGLISH_1A')),
				(CONCAT('HS+_','ENGLISH_2A')),
				(CONCAT('HS+_','GEOGRAPHY_1A')),
				(CONCAT('HS+_','HISTORY_1A')),
				(CONCAT('HS+_','MATH_1A')),
				(CONCAT('HS+_','MATH_2A')),
				(CONCAT('HS+_','SOC_A')),
				(CONCAT('HS+_','LIFE_SCIENCE_A')),
				(CONCAT('HS+_','OED_A')),
				(CONCAT('HS+_','PORT_A')),
				(CONCAT('HS+_','H&F_A')),
				(CONCAT('HS+_','US_HIST_ART_A')),
				(CONCAT('HS+_','WA_HIST_ART_A')),
				(CONCAT('HS+_','ALG_I_A')),
				(CONCAT('HS+_','ALG_II_A')),
				(CONCAT('HS+_','ART_A')),
				(CONCAT('HS+_','CW_A')),
				(CONCAT('HS+_','EMP_SKILS_A')),
				(CONCAT('HS+_','ENGL_A')),
				(CONCAT('HS+_','GEN_SCI_A')),
				(CONCAT('HS+_','GEOM_A')),
				(CONCAT('HS+_','ANATOMY_A')),
				(CONCAT('HS+_','IS_ART_A')),
				(CONCAT('HS+_','LAB_SCI_A')),
				(CONCAT('HS+_','MED_BI_A')),
				(CONCAT('HS+_','PYS_ED_A')),
				(CONCAT('HS+_','ANG_MGMT_A'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED001'
		UNION ALL
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','SOC_B')),
				(CONCAT('HS+_','LIFE_SCIENCE_B')),
				(CONCAT('HS+_','OED_B')),
				(CONCAT('HS+_','PORT_B')),
				(CONCAT('HS+_','H&F_B')),
				(CONCAT('HS+_','US_HIST_ART_B')),
				(CONCAT('HS+_','WA_HIST_ART_B')),
				(CONCAT('HS+_','ALG_I_B')),
				(CONCAT('HS+_','ALG_II_B')),
				(CONCAT('HS+_','ART_B')),
				(CONCAT('HS+_','CW_B')),
				(CONCAT('HS+_','EMP_SKILS_B')),
				(CONCAT('HS+_','ENGL_B')),
				(CONCAT('HS+_','GEN_SCI_B')),
				(CONCAT('HS+_','GEOM_B')),
				(CONCAT('HS+_','ANATOMY_B')),
				(CONCAT('HS+_','IS_ART_B')),
				(CONCAT('HS+_','LAB_SCI_B')),
				(CONCAT('HS+_','MED_BI_B')),
				(CONCAT('HS+_','PYS_ED_B')),
				(CONCAT('HS+_','ANG_MGMT_B'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED002'
		UNION ALL
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','SOC_B')),
				(CONCAT('HS+_','LIFE_SCIENCE_B')),
				(CONCAT('HS+_','OED_B')),
				(CONCAT('HS+_','PORT_B')),
				(CONCAT('HS+_','H&F_B')),
				(CONCAT('HS+_','US_HIST_ART_B')),
				(CONCAT('HS+_','WA_HIST_ART_B')),
				(CONCAT('HS+_','ALG_I_B')),
				(CONCAT('HS+_','ALG_II_B')),
				(CONCAT('HS+_','ART_B')),
				(CONCAT('HS+_','CW_B')),
				(CONCAT('HS+_','EMP_SKILS_B')),
				(CONCAT('HS+_','ENGL_B')),
				(CONCAT('HS+_','GEN_SCI_B')),
				(CONCAT('HS+_','GEOM_B')),
				(CONCAT('HS+_','ANATOMY_B')),
				(CONCAT('HS+_','IS_ART_B')),
				(CONCAT('HS+_','LAB_SCI_B')),
				(CONCAT('HS+_','MED_BI_B')),
				(CONCAT('HS+_','PYS_ED_B')),
				(CONCAT('HS+_','ANG_MGMT_B'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED003'
		UNION ALL
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','SOC_C')),
				(CONCAT('HS+_','LIFE_SCIENCE_C')),
				(CONCAT('HS+_','OED_C')),
				(CONCAT('HS+_','PORT_C')),
				(CONCAT('HS+_','H&F_C')),
				(CONCAT('HS+_','US_HIST_ART_C')),
				(CONCAT('HS+_','WA_HIST_ART_C')),
				(CONCAT('HS+_','ALG_I_C')),
				(CONCAT('HS+_','ALG_II_C')),
				(CONCAT('HS+_','ART_C')),
				(CONCAT('HS+_','CW_C')),
				(CONCAT('HS+_','EMP_SKILS_C')),
				(CONCAT('HS+_','ENGL_C')),
				(CONCAT('HS+_','GEN_SCI_C')),
				(CONCAT('HS+_','GEOM_C')),
				(CONCAT('HS+_','ANATOMY_C')),
				(CONCAT('HS+_','IS_ART_C')),
				(CONCAT('HS+_','LAB_SCI_C')),
				(CONCAT('HS+_','MED_BI_C')),
				(CONCAT('HS+_','PYS_ED_C')),
				(CONCAT('HS+_','ANG_MGMT_C'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED004'
		UNION ALL
		SELECT new_course_id
		FROM (
			VALUES
				(CONCAT('HS+_','SOC_C')),
				(CONCAT('HS+_','LIFE_SCIENCE_C')),
				(CONCAT('HS+_','OED_C')),
				(CONCAT('HS+_','PORT_C')),
				(CONCAT('HS+_','H&F_C')),
				(CONCAT('HS+_','US_HIST_ART_C')),
				(CONCAT('HS+_','WA_HIST_ART_C')),
				(CONCAT('HS+_','ALG_I_C')),
				(CONCAT('HS+_','ALG_II_C')),
				(CONCAT('HS+_','ART_C')),
				(CONCAT('HS+_','CW_C')),
				(CONCAT('HS+_','EMP_SKILS_C')),
				(CONCAT('HS+_','ENGL_C')),
				(CONCAT('HS+_','GEN_SCI_C')),
				(CONCAT('HS+_','GEOM_C')),
				(CONCAT('HS+_','ANATOMY_C')),
				(CONCAT('HS+_','IS_ART_C')),
				(CONCAT('HS+_','LAB_SCI_C')),
				(CONCAT('HS+_','MED_BI_C')),
				(CONCAT('HS+_','PYS_ED_C')),
				(CONCAT('HS+_','ANG_MGMT_C'))
		) AS trans_courses(new_course_id)
		WHERE c.course_prefix || c.course_code = 'ABE&GED005'
    ) v(new_course_id) ON true
    WHERE cs.scheduled_quarter = 'Winter (2251)'  -- Filter for the current term
),
main_data AS (
SELECT 
    course_id,
    student_user_id AS user_id,
    'student' AS role,
    CASE 
        WHEN is_special_course THEN 'inactive'
        ELSE 'active'
    END AS status
FROM course_data

UNION ALL

SELECT DISTINCT
	'LAPTOP' AS course_id,
	student_user_id AS user_id,
    'student' AS role,
	'active' AS status
FROM course_data

UNION ALL

SELECT DISTINCT
    course_id,
    au.username AS user_id,
    'teacher' AS role,
    'active' AS status
FROM course_data
JOIN db_auth_user au ON au.username LIKE '%' || split_part(UPPER(course_data.course_instructor), ',', 1)
ORDER BY role DESC, user_id ASC
)
SELECT *
FROM main_data
-- WHERE user_id IS NULL