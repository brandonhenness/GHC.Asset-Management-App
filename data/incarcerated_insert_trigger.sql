CREATE OR REPLACE FUNCTION fn_ensure_entity_for_incarcerated()
RETURNS TRIGGER AS $$
DECLARE
    v_entity_id INTEGER;
BEGIN
    SELECT e.entity_id INTO v_entity_id
    FROM incarcerated i
    JOIN entities e ON i.entity_id = e.entity_id
    WHERE i.doc_number = NEW.doc_number;

    IF NOT FOUND THEN
        INSERT INTO entities (entity_type, enabled)
        VALUES ('USER'::entity_type, TRUE)
        RETURNING entity_id INTO NEW.entity_id;
		
		INSERT INTO users(entity_id, last_name, first_name, middle_name, user_type)
		VALUES (v_entity_id, 'UNKNOWN', 'UNKNOWN', NULL, 'INCARCERATED');
    END IF;
	
	NEW.entity_id := v_entity_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_before_incarcerated_insert
BEFORE INSERT ON incarcerated
FOR EACH ROW
EXECUTE FUNCTION fn_ensure_entity_for_incarcerated();