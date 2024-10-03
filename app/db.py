import os
import psycopg2
from psycopg2 import OperationalError
import logging

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'crypto_data')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logging.info('Database connection established.')
        return conn
    except OperationalError as e:
        logging.error(f'Unable to connect to the database. Error: {e}')
        exit(1)

def create_tables(cursor, conn):
    """Create the ticker_data table if it doesn't exist."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticker_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP,
        symbol VARCHAR(10),
        price_usd NUMERIC,
        volume NUMERIC
    )
    ''')
    conn.commit()
    logging.info('Ensured ticker_data table exists.')
