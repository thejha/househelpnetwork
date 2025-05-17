import os
import psycopg2
import sys

# SQL script provided by the user
SQL_SCRIPT = """
-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS owner_to_owner_connects;
DROP TABLE IF EXISTS incident_reports;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS contracts;
DROP TABLE IF EXISTS task_list;
DROP TABLE IF EXISTS helper_documents;
DROP TABLE IF EXISTS helper_profiles;
DROP TABLE IF EXISTS owner_documents;
DROP TABLE IF EXISTS owner_profiles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS languages;
DROP TABLE IF EXISTS pincode_mapping;

-- Create tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'owner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE owner_profiles (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    state VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    society VARCHAR(100) NOT NULL,
    street VARCHAR(100) NOT NULL,
    apartment_number VARCHAR(20) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'Pending'
);

CREATE TABLE owner_documents (
    id SERIAL PRIMARY KEY,
    owner_profile_id INTEGER REFERENCES owner_profiles(id) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL
);

CREATE TABLE helper_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    helper_id VARCHAR(50) UNIQUE NOT NULL,
    helper_type VARCHAR(20) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    photo_url VARCHAR(255),
    state VARCHAR(50) NOT NULL,
    languages VARCHAR(255) NOT NULL,
    has_police_verification BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE helper_documents (
    id SERIAL PRIMARY KEY,
    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(255) NOT NULL
);

CREATE TABLE task_list (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    contract_id VARCHAR(50) UNIQUE NOT NULL,
    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    tasks VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_salary FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    review_id VARCHAR(50) UNIQUE NOT NULL,
    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    tasks_average FLOAT NOT NULL,
    punctuality FLOAT NOT NULL,
    attitude FLOAT NOT NULL,
    hygiene FLOAT NOT NULL,
    communication FLOAT NOT NULL,
    reliability FLOAT NOT NULL,
    comments TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE incident_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(50) UNIQUE NOT NULL,
    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
    owner_id INTEGER REFERENCES users(id) NOT NULL,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    fir_number VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE owner_to_owner_connects (
    id SERIAL PRIMARY KEY,
    form_id VARCHAR(50) UNIQUE NOT NULL,
    helper_profile_id INTEGER REFERENCES helper_profiles(id) NOT NULL,
    from_owner_id INTEGER REFERENCES users(id) NOT NULL,
    to_owner_contact VARCHAR(120) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stored_locally BOOLEAN DEFAULT TRUE
);

CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE pincode_mapping (
    id SERIAL PRIMARY KEY,
    pincode VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    society VARCHAR(100) NOT NULL
);

-- Insert seed data for languages
INSERT INTO languages (name) VALUES 
('Hindi'), ('Bengali'), ('Telugu'), ('Marathi'), ('Tamil'),
('Urdu'), ('Gujarati'), ('Kannada'), ('Odia'), ('Malayalam'),
('Punjabi'), ('Assamese'), ('Maithili'), ('Sanskrit'), ('English'),
('Kashmiri'), ('Nepali'), ('Sindhi'), ('Konkani'), ('Dogri'),
('Manipuri'), ('Bodo');

-- Insert seed data for pincode mapping
INSERT INTO pincode_mapping (pincode, city, state, society) VALUES
('400001', 'Mumbai', 'Maharashtra', 'Fort Area'),
('400051', 'Mumbai', 'Maharashtra', 'Bandra West'),
('400076', 'Mumbai', 'Maharashtra', 'Powai Lake Residency'),
('110001', 'New Delhi', 'Delhi', 'Connaught Place'),
('110016', 'New Delhi', 'Delhi', 'Hauz Khas Enclave'),
('110017', 'New Delhi', 'Delhi', 'Green Park Extension'),
('560001', 'Bangalore', 'Karnataka', 'MG Road Center'),
('560008', 'Bangalore', 'Karnataka', 'Shantinagar Housing'),
('560034', 'Bangalore', 'Karnataka', 'Koramangala Layout'),
('411004', 'Pune', 'Maharashtra', 'Koregaon Park'),
('411006', 'Pune', 'Maharashtra', 'Aundh Royal Residency'),
('411014', 'Pune', 'Maharashtra', 'Hadapsar IT Park Homes'),
('411021', 'Pune', 'Maharashtra', 'Hinjewadi Phase 2'),
('411045', 'Pune', 'Maharashtra', 'Baner Sus Road Villas'),
('380001', 'Ahmedabad', 'Gujarat', 'Lal Darwaza'),
('380006', 'Ahmedabad', 'Gujarat', 'Navrangpura Central'),
('380015', 'Ahmedabad', 'Gujarat', 'Satellite Residency'),
('380054', 'Ahmedabad', 'Gujarat', 'Bodakdev Heights'),
('380059', 'Ahmedabad', 'Gujarat', 'Science City Road Villas'),
('382424', 'Ahmedabad', 'Gujarat', 'GIFT City Towers'),
('302001', 'Jaipur', 'Rajasthan', 'Pink City Center'),
('302015', 'Jaipur', 'Rajasthan', 'Malviya Nagar Extension'),
('302017', 'Jaipur', 'Rajasthan', 'Mansarovar Gardens');
"""

def setup_db_direct():
    # Get database configuration from environment variables or use defaults
    postgres_user = os.environ.get("POSTGRES_USER", "postgres")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "rmivuxg")
    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = os.environ.get("POSTGRES_PORT", "5432")
    postgres_db = os.environ.get("POSTGRES_DB", "househelpnetwork")
    
    # Connect to the database
    try:
        print(f"Connecting to database '{postgres_db}' on {postgres_host}:{postgres_port}...")
        conn = psycopg2.connect(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_db
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Executing SQL script...")
        cursor.execute(SQL_SCRIPT)
        
        print("SQL script executed successfully!")
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        print(f"Error executing SQL script: {e}")
        return False

if __name__ == "__main__":
    print("Setting up database tables directly using SQL...")
    success = setup_db_direct()
    
    if success:
        print("Database tables created and seed data inserted successfully!")
    else:
        print("Failed to set up database tables.")
        sys.exit(1) 