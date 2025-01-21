SELECT *
FROM
(SELECT DISTINCT
	a.asset_id,
 	CASE
 		WHEN a.asset_type = 'LAPTOP' THEN 'Laptop'
 		ELSE NULL
 	END AS asset_type,
 	l.laptop_manufacturer AS manufacturer,
	l.laptop_model AS model,
	l.laptop_serial_number AS serial_number,
 	CASE 
 		WHEN a.asset_status = 'DECOMMISSIONED' THEN 'Retired'
 		WHEN a.asset_status = 'MISSING' THEN 'Missing'
 		WHEN a.asset_status = 'BROKEN' THEN 'Broken'
 		WHEN a.asset_status = 'OUT_FOR_REPAIR' THEN 'In repair'
 		WHEN t_latest.transaction_type ='ISSUED' AND a.asset_status = 'IN_SERVICE' THEN 'In use'
		ELSE 'Available'
 	END AS status,
	a.asset_cost,
	'Clear' AS color,
	'SCCC' AS origin_site,
	'SCCC' AS current_site,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN t_latest.transaction_timestamp ELSE NULL END AS transaction_timestamp,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN i.doc_number ELSE NULL END AS doc_number,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN u.last_name ELSE NULL END AS last_name,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN u.first_name ELSE NULL END AS first_name,
	CASE
 		WHEN t_latest.transaction_type ='ISSUED' AND d.document_signed_timestamp IS NOT NULL THEN TRUE
 		WHEN t_latest.transaction_type ='ISSUED' AND d.document_signed_timestamp IS NOT NULL THEN FALSE
		ELSE NULL
 	END AS agreement_signed,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN i.housing_unit ELSE NULL END AS housing_unit,
	CASE WHEN t_latest.transaction_type ='ISSUED' THEN i.housing_cell ELSE NULL END AS housing_cell

FROM assets a
LEFT JOIN laptops l ON a.asset_id = l.asset_id
LEFT JOIN (
	SELECT
		t1.asset_id,
		t1,transaction_id,
		t1.transaction_type,
		t1.transaction_timestamp,
		t1.entity_id
	FROM transactions t1
	WHERE t1.transaction_timestamp = (
		SELECT MAX(t2.transaction_timestamp)
		FROM transactions t2
		WHERE t2.asset_id = t1.asset_id
	)
) t_latest ON t_latest.asset_id = a.asset_id
LEFT JOIN incarcerated i ON t_latest.entity_id = i.entity_id
LEFT JOIN users u ON i.entity_id = u.entity_id
LEFT JOIN transaction_documents td ON t_latest.transaction_id = td.transaction_id
LEFT JOIN documents d ON td.document_id = d.document_id
WHERE a.asset_type = 'LAPTOP'
AND a.asset_status != 'DECOMMISSIONED'
ORDER BY a.asset_id ASC
) AS inventory
-- WHERE inventory.status = 'Available'