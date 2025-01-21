INSERT INTO incarcerated (doc_number, facility, housing_unit, housing_cell, estimated_release_date, counselor)
SELECT 
    oi."DOC_NUMBER", 
    oi."FacCode", 
    oi."UNIT", 
    oi."BED_ASSIGNMENT", 
    cast_string_to_date_safe(oi.textbox38), 
    oi."CC_CCO_NAME"
FROM 
    omni_import oi
ON CONFLICT (doc_number) DO UPDATE SET
    facility = EXCLUDED.facility,
    housing_unit = EXCLUDED.housing_unit,
    housing_cell = EXCLUDED.housing_cell,
    estimated_release_date = EXCLUDED.estimated_release_date,
    counselor = EXCLUDED.counselor;

INSERT INTO users (entity_id, last_name, first_name, middle_name, user_type)
SELECT 
    i.entity_id, 
    UPPER(SPLIT_PART(oi."OFFENDER_NAME", ', ', 1)), 
    UPPER(SPLIT_PART(SPLIT_PART(oi."OFFENDER_NAME", ', ', 2), ' ', 1)), 
    TRIM(TRAILING '.' FROM UPPER(SPLIT_PART(SPLIT_PART(oi."OFFENDER_NAME", ', ', 2), ' ', 2))), 
    'INCARCERATED'::user_type
FROM 
    omni_import oi
JOIN
    incarcerated i ON oi."DOC_NUMBER" = i.doc_number
ON CONFLICT (entity_id) DO UPDATE SET
    last_name = EXCLUDED.last_name,
    first_name = EXCLUDED.first_name,
    middle_name = EXCLUDED.middle_name,
    user_type = EXCLUDED.user_type;
