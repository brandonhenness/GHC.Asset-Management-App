-- This search finds a user by first and/or last name.
-- :defaults => { 'AMS_blank': ['first_name', 'last_name'] }
-- :first_name => Enter the user's first name (ENTER to leave blank)
-- :last_name => Enter the user's last name (ENTER to leave blank)

SELECT 
    users.last_name, users.first_name, users.middle_name, incarcerated.doc_number, users.osn_username, users.osn_last_login, users.ctclink_id,
    incarcerated.facility, incarcerated.housing_unit, incarcerated.housing_cell, incarcerated.counselor, incarcerated.hs_diploma
FROM users, incarcerated
WHERE users.last_name LIKE '%:last_name%' AND users.first_name LIKE '%:first_name%'
    AND users.entity_id = incarcerated.entity_id
ORDER BY users.last_name ASC, users.first_name ASC

