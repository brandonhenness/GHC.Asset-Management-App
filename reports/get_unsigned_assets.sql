SELECT

	incarcerated.doc_number,
	users.last_name,
	users.first_name,
	users.middle_name,
	COUNT(issued_assets.asset_id) AS asset_count

FROM

    incarcerated,
	users,
	transactions,
	issued_assets,
	transaction_documents,
	documents
	
WHERE

        incarcerated.entity_id               = users.entity_id
    AND incarcerated.entity_id               = transactions.entity_id
	AND transactions.asset_id                = issued_assets.asset_id
	AND transactions.transaction_id          = transaction_documents.transaction_id
	AND transaction_documents.document_id    = documents.document_id
	AND documents.document_printed_timestamp is null

GROUP BY

    incarcerated.doc_number,
	users.last_name,
	users.first_name,
	users.middle_name,
	documents.document_printed_timestamp

ORDER BY

    users.last_name   ASC,
	users.first_name  ASC,
	users.middle_name ASC