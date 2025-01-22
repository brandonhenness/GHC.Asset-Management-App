CREATE DATABASE edu;

CREATE TYPE entity_type AS ENUM ('USER', 'LOCATION');

CREATE TABLE entities (
    entity_id SERIAL PRIMARY KEY,
    entity_type entity_type NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TYPE user_type AS ENUM ('INCARCERATED', 'EMPLOYEE');

CREATE TABLE users (
    entity_id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    ctclink_id VARCHAR(255) UNIQUE,
    last_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    middle_name VARCHAR(255),
    legacy_username VARCHAR(255) UNIQUE,
    legacy_last_login TIMESTAMP,
    osn_username VARCHAR(255) UNIQUE,
    osn_last_login TIMESTAMP,
    user_type user_type NOT NULL
);

CREATE TABLE incarcerated (
    entity_id INTEGER PRIMARY KEY REFERENCES users(entity_id),
    doc_number VARCHAR(255) NOT NULL UNIQUE,
    facility VARCHAR(255),
    housing_unit VARCHAR(255),
    housing_cell VARCHAR(255),
    estimated_release_date DATE,
    counselor VARCHAR(255),
    hs_diploma BOOLEAN
);

CREATE TYPE program_status AS ENUM ('ENROLLED', 'NOT_ENROLLED', 'GRADUATED', 'WITHDRAWN', 'SUSPENDED', 'EXPELLED');

CREATE TABLE students (
    entity_id INTEGER PRIMARY KEY REFERENCES incarcerated(entity_id),
    program VARCHAR(255),
    program_status program_status NOT NULL DEFAULT 'ENROLLED'
);

CREATE TABLE employees (
    entity_id INTEGER PRIMARY KEY REFERENCES users(entity_id),
    employee_id VARCHAR(255) UNIQUE
);

CREATE TABLE locations (
    entity_id INTEGER PRIMARY KEY REFERENCES entities(entity_id),
    building VARCHAR(255) NOT NULL,
    room_number VARCHAR(255) NOT NULL,
    room_name VARCHAR(255),
    UNIQUE (building, room_number)
);

CREATE TYPE asset_type AS ENUM ('LAPTOP', 'BOOK', 'CALCULATOR');

CREATE TABLE asset_types (
    asset_type asset_type PRIMARY KEY,
    charge_limit INTEGER
);

INSERT INTO asset_types (asset_type, charge_limit)
VALUES 
    ('LAPTOP', 1), 
    ('BOOK', NULL),
    ('CALCULATOR', 1);

CREATE TYPE asset_status AS ENUM ('IN_SERVICE', 'DECOMMISSIONED', 'OUT_FOR_REPAIR', 'MISSING', 'BROKEN');

CREATE TABLE assets (
    asset_id VARCHAR(255) PRIMARY KEY,
    asset_type asset_type NOT NULL REFERENCES asset_types(asset_type),
    asset_cost DECIMAL(10,2) DEFAULT 0.00,
    asset_status asset_status NOT NULL DEFAULT 'IN_SERVICE'
);

CREATE TYPE transaction_type AS ENUM ('ISSUED', 'RETURNED', 'MISSING', 'BROKEN', 'SHIPPED', 'RECEIVED', 'DECOMMISSIONED');

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES entities(entity_id),
    asset_id VARCHAR(255) NOT NULL REFERENCES assets(asset_id),
    transaction_type transaction_type NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_user VARCHAR(255) NOT NULL DEFAULT CURRENT_USER,
    transaction_notes TEXT
);

CREATE TABLE issued_assets (
    asset_id VARCHAR(255) PRIMARY KEY REFERENCES assets(asset_id),
    transaction_id INTEGER REFERENCES transactions(transaction_id)
);

CREATE TABLE issued_chargers (
    transaction_id INTEGER PRIMARY KEY REFERENCES transactions(transaction_id)
);

CREATE TYPE document_type AS ENUM ('AGREEMENT', 'LABELS');

CREATE TABLE documents (
    document_id SERIAL PRIMARY KEY,
    document_type document_type NOT NULL,
    document_printed_timestamp TIMESTAMP NULL,
    document_signed_timestamp TIMESTAMP NULL,
    document_file_name VARCHAR(255),
    document_notes TEXT,
    CHECK (document_type != 'AGREEMENT' OR document_file_name IS NOT NULL)
);

CREATE TABLE transaction_documents (
    transaction_id INTEGER NOT NULL REFERENCES transactions(transaction_id),
    document_id INTEGER NOT NULL REFERENCES documents(document_id),
    PRIMARY KEY (transaction_id, document_id)
);

-- CREATE TABLE images (
--     image_id SERIAL PRIMARY KEY,
--     image_name VARCHAR(255) NOT NULL,
--     image_version VARCHAR(255) NOT NULL,
--     image_os_type VARCHAR(255) NOT NULL,
--     image_os_version VARCHAR(255) NOT NULL,
--     image_os_build VARCHAR(255)
-- );

-- CREATE TABLE software (
--     software_id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL,
--     version VARCHAR(255) NOT NULL
-- );

-- CREATE TABLE images_software (
--     image_id INTEGER NOT NULL REFERENCES images(image_id),
--     software_id INTEGER NOT NULL REFERENCES software(software_id),
--     PRIMARY KEY (image_id, software_id)
-- );

CREATE TABLE laptops (
    asset_id VARCHAR(255) PRIMARY KEY REFERENCES assets(asset_id),
    laptop_model VARCHAR(255) NOT NULL,
    laptop_serial_number VARCHAR(255) UNIQUE NOT NULL,
    laptop_manufacturer VARCHAR(255) NOT NULL,
    laptop_drive_serial_number VARCHAR(255) UNIQUE,
    laptop_ram INTEGER,
    laptop_cpu VARCHAR(255),
    laptop_storage INTEGER,
    laptop_bios_version VARCHAR(255)
    -- image_id INTEGER REFERENCES images(image_id)
);

CREATE TABLE books (
    book_isbn VARCHAR(255) PRIMARY KEY,
    book_title VARCHAR(255) NOT NULL,
    book_author VARCHAR(255) NOT NULL,
    book_publisher VARCHAR(255),
    book_edition INTEGER,
    book_year INTEGER
);

CREATE TABLE book_assets (
    asset_id VARCHAR(255) PRIMARY KEY REFERENCES assets(asset_id),
    book_isbn VARCHAR(255) NOT NULL REFERENCES books(book_isbn),
    book_number VARCHAR(255),
    UNIQUE (book_isbn, book_number)
);

CREATE TABLE calculators (
    asset_id VARCHAR(255) PRIMARY KEY REFERENCES assets(asset_id),
    calculator_model VARCHAR(255) NOT NULL,
    calculator_serial_number VARCHAR(255) UNIQUE,
    calculator_manufacturer VARCHAR(255),
    calculator_manufacturer_date_code VARCHAR(255),
    calculator_color VARCHAR(255)
);

CREATE TABLE signatures (
    signature_id SERIAL PRIMARY KEY,
    entity_id INTEGER NOT NULL REFERENCES entities(entity_id),
    signature_data BYTEA NOT NULL
);

CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_prefix VARCHAR(255) NOT NULL,
    course_code VARCHAR(255) NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    course_credits INTEGER,
    course_description TEXT,
    course_outcomes TEXT,
    UNIQUE (course_prefix, course_code)
);

CREATE TABLE prerequisites (
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    prerequisite_id INTEGER NOT NULL REFERENCES courses(course_id),
    PRIMARY KEY (course_id, prerequisite_id)
);

CREATE TABLE course_schedules (
    schedule_id SERIAL PRIMARY KEY,
    course_id INT NOT NULL REFERENCES courses(course_id),
    course_start_date DATE NOT NULL,
    course_end_date DATE NOT NULL CHECK (course_end_date > course_start_date),
    course_days VARCHAR(255) NOT NULL,
    course_start_time TIME NOT NULL,
    course_end_time TIME NOT NULL,
    course_location VARCHAR(255) NOT NULL,
    course_instructor VARCHAR(255) NOT NULL,
    scheduled_quarter VARCHAR(255) NOT NULL,
    scheduled_year INTEGER NOT NULL
);

CREATE TABLE enrollments (
    entity_id INTEGER NOT NULL REFERENCES entities(entity_id),
    schedule_id INTEGER NOT NULL REFERENCES course_schedules(schedule_id),
    PRIMARY KEY (entity_id, schedule_id)
);
