INSERT INTO assets (asset_id, asset_type, asset_cost, asset_status)
SELECT 
    ai.asset_id, 
    ai.asset_type, 
    ai.asset_cost, 
    ai.asset_status
FROM 
    asset_import ai
ON CONFLICT (asset_id) DO UPDATE SET
    asset_type = EXCLUDED.asset_type,
    asset_cost = EXCLUDED.asset_cost,
    asset_status = EXCLUDED.asset_status;

INSERT INTO calculators (entity_id, last_name, first_name, middle_name, user_type)
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
