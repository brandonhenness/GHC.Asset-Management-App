-- Imports / updates incarcerated records from an OMNI data set

-- :defaults => { 'AMS_import': True, 'AMS_returning': 'entity_id' }
-- :defaults => { 'AMS_insert_tables': [ 'entities', 'users', 'incarcerated' ] }

--- These OMNI column names don't exist in the AMS database, so
--- we 'cast' them to appropriate column types for processing.
-- :defaults => { 'AMS_coltypes_overrides': { 'DOC_NUMBER': 'character varying', 'FacCode': 'character varying', 'UNIT': 'character varying', 'BED_ASSIGNMENT': 'character varying', 'textbox38': 'character varying', 'CC_CCO_NAME': 'character varying', 'OFFENDER_NAME': 'character varying' } }


--- This INSERT statement fires a trigger script in the database which
--- creates defaults-valued rows in the 'entities' and 'users' tables
INSERT INTO incarcerated 
(
	doc_number,
	facility,
	housing_unit,
	housing_cell,
	estimated_release_date,
	counselor
)
VALUES
(
	%(DOC_NUMBER)s,
	%(FacCode)s,
	%(UNIT)s,
	%(BED_ASSIGNMENT)s,
	cast_string_to_date_safe(%(textbox38)s),
	%(CC_CCO_NAME)s
)
ON CONFLICT (doc_number) DO UPDATE
SET
--- Use the default syntax for handling 'ON CONFLICT (...) DO UPDATE' columns:
	doc_number             = EXCLUDED.doc_number,
	facility               = EXCLUDED.facility,
	housing_unit           = EXCLUDED.housing_unit,
	housing_cell           = EXCLUDED.housing_cell,
	estimated_release_date = EXCLUDED.estimated_release_date,
	counselor              = EXCLUDED.counselor
RETURNING
    entity_id
;

INSERT INTO users (
	entity_id,
	last_name,
	first_name,
	middle_name,
	user_type
)
VALUES
(
--- incarcerated.entity_id,
	(	SELECT entity_id
		FROM  incarcerated
		WHERE doc_number = %(DOC_NUMBER)s
	),
	UPPER(SPLIT_PART(%(OFFENDER_NAME)s, ', ', 1)),
	UPPER(SPLIT_PART(SPLIT_PART(%(OFFENDER_NAME)s, ', ', 2), ' ', 1)),
	TRIM(TRAILING '.' FROM UPPER(SPLIT_PART(SPLIT_PART(%(OFFENDER_NAME)s, ', ', 2), ' ', 2))),
	'INCARCERATED'::user_type
)
---  This earlier version's clause is replaced with the above SELECT entity_id subquery:
---    JOIN incarcerated ON incarcerated.doc_number = %(DOC_NUMBER)s
--- The subquery is simpler and it doesn't produce this SQL error:
---     Execution failed on sql 'INSERT INTO incarcerated...': syntax error at or near "JOIN"
---     LINE 44: ) JOIN incarcerated ON incarcerated.doc_number = '437565'
ON CONFLICT (entity_id) DO UPDATE
SET
	entity_id   = EXCLUDED.entity_id,
	last_name   = EXCLUDED.last_name,
	first_name  = EXCLUDED.first_name,
	middle_name = EXCLUDED.middle_name,
	user_type   = EXCLUDED.user_type
RETURNING
    entity_id
;
