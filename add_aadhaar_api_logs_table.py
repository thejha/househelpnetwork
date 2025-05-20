"""
Script to add aadhaar_api_logs table to the database
"""
import os
import sys
import logging
import datetime
from config import Config
import psycopg2
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_aadhaar_api_logs_table():
    # Get database configuration
    postgres_user = Config.POSTGRES_USER
    postgres_password = Config.POSTGRES_PASSWORD
    postgres_host = Config.POSTGRES_HOST
    postgres_port = Config.POSTGRES_PORT
    postgres_db = Config.POSTGRES_DB
    
    # Connect to PostgreSQL database
    try:
        logger.info(f"Connecting to PostgreSQL database at {postgres_host}:{postgres_port}...")
        conn = psycopg2.connect(
            user=postgres_user,
            password=postgres_password,
            host=postgres_host,
            port=postgres_port,
            database=postgres_db
        )
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'aadhaar_api_logs'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info("Table 'aadhaar_api_logs' already exists. Skipping creation.")
            return True
        
        # Create aadhaar_api_logs table
        logger.info("Creating 'aadhaar_api_logs' table...")
        cursor.execute("""
            CREATE TABLE aadhaar_api_logs (
                id SERIAL PRIMARY KEY,
                aadhaar_id VARCHAR(12),
                reference_id VARCHAR(100),
                request_type VARCHAR(50) NOT NULL,
                request_payload JSONB,
                response_payload JSONB,
                success BOOLEAN DEFAULT FALSE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                session_id VARCHAR(100)
            );
        """)
        
        # Create index on aadhaar_id and reference_id for faster lookups
        cursor.execute("""
            CREATE INDEX idx_aadhaar_api_logs_aadhaar_id ON aadhaar_api_logs(aadhaar_id);
        """)
        
        cursor.execute("""
            CREATE INDEX idx_aadhaar_api_logs_reference_id ON aadhaar_api_logs(reference_id);
        """)
        
        # Create index on request_type and success for filtering
        cursor.execute("""
            CREATE INDEX idx_aadhaar_api_logs_request_type_success ON aadhaar_api_logs(request_type, success);
        """)
        
        # Create index on created_at for time-based queries
        cursor.execute("""
            CREATE INDEX idx_aadhaar_api_logs_created_at ON aadhaar_api_logs(created_at);
        """)
        
        conn.commit()
        logger.info("Table 'aadhaar_api_logs' created successfully with indexes.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    add_aadhaar_api_logs_table() 