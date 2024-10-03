import os
import time
import requests
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime, timedelta
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def create_materialized_view(cursor, conn):
    """Create or replace the materialized view for daily OHLCV data."""
    cursor.execute('''
    DROP MATERIALIZED VIEW IF EXISTS daily_ohlcv CASCADE;
    CREATE MATERIALIZED VIEW daily_ohlcv AS
    SELECT
        symbol,
        date_trunc('day', timestamp) AS day,
        (ARRAY_AGG(price_usd ORDER BY timestamp ASC))[1] AS open,
        MAX(price_usd) AS high,
        MIN(price_usd) AS low,
        (ARRAY_AGG(price_usd ORDER BY timestamp DESC))[1] AS close,
        SUM(volume) AS volume
    FROM
        ticker_data
    GROUP BY
        symbol, date_trunc('day', timestamp);
    CREATE UNIQUE INDEX daily_ohlcv_idx ON daily_ohlcv (symbol, day);
    ''')
    conn.commit()
    logging.info('Materialized view daily_ohlcv created or refreshed.')

def refresh_materialized_view_periodically(conn, interval_seconds=60):
    """Refresh the materialized view at regular intervals."""
    def refresh():
        while True:
            try:
                with conn.cursor() as cursor:
                    create_materialized_view(cursor, conn)
            except Exception as e:
                logging.error(f'Error refreshing materialized view: {e}')
            time.sleep(interval_seconds)
    # Run the refresh in a separate daemon thread
    threading.Thread(target=refresh, daemon=True).start()
    logging.info(f'Started materialized view refresh thread (every {interval_seconds} seconds).')

def fetch_and_store_data():
    """Fetch data from the API, store it in the database, and check for alerts."""
    # Define the coins to monitor
    coins = [
        {'id': 'bitcoin', 'symbol': 'BTC'},
        {'id': 'ethereum', 'symbol': 'ETH'},
        {'id': 'zcash', 'symbol': 'ZEC'}
    ]
    coin_ids = ','.join([coin['id'] for coin in coins])  # 'bitcoin,ethereum,zcash'

    # Initialize data structures for storing recent prices and volumes
    # Each symbol maps to a list of (timestamp, price, volume) tuples
    data_history = {
        coin['symbol']: [] for coin in coins
    }

    # Determine the next alert check time aligned to the clock
    def get_next_alert_time():
        now = datetime.utcnow()
        # Calculate the next time that is a multiple of 5 minutes
        next_minute = (now.minute // 5 + 1) * 5
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
        return next_time

    next_alert_time = get_next_alert_time()
    logging.info(f'Next alert check scheduled at {next_alert_time} UTC.')

    while True:
        loop_start_time = time.time()
        try:
            # Fetch data for all coins in a single API call
            response = requests.get(
                'https://api.coingecko.com/api/v3/coins/markets',
                params={
                    'vs_currency': 'usd',
                    'ids': coin_ids,
                    'order': 'market_cap_desc',
                    'per_page': 100,
                    'page': 1,
                    'sparkline': 'false'
                }
            )
            response.raise_for_status()
            data = response.json()

            current_time = datetime.utcnow()

            for coin_data in data:
                symbol = coin_data['symbol'].upper()
                price = float(coin_data['current_price'])
                volume = float(coin_data['total_volume'])

                # Insert data into the database
                cursor.execute(
                    'INSERT INTO ticker_data (timestamp, symbol, price_usd, volume) VALUES (%s, %s, %s, %s)',
                    (current_time, symbol, price, volume)
                )
                conn.commit()

                logging.info(f'Inserted data for {symbol} at {current_time} UTC.')

                # Append data to history
                data_history[symbol].append((current_time, price, volume))

                # Remove data older than 5 minutes
                five_minutes_ago = current_time - timedelta(minutes=5)
                data_history[symbol] = [
                    record for record in data_history[symbol] if record[0] >= five_minutes_ago
                ]

            # Check if it's time to perform alert checks
            if current_time >= next_alert_time:
                logging.info(f'Performing alert checks at {current_time} UTC.')
                perform_alert_checks(data_history, current_time)
                # Schedule the next alert check
                next_alert_time += timedelta(minutes=5)
                logging.info(f'Next alert check scheduled at {next_alert_time} UTC.')

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logging.error(f'HTTP error occurred: {e}')
            if status_code == 429:
                # Handle rate limiting by waiting before retrying
                logging.warning('Rate limit exceeded. Waiting for 60 seconds.')
                time.sleep(60)
                continue  # Skip the sleep at the end and retry immediately
            else:
                # For other HTTP errors, wait for a short period before retrying
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            logging.error(f'HTTP request failed: {e}')
            time.sleep(5)
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            time.sleep(5)

        # Calculate elapsed time and sleep to maintain 1 call per second
        loop_end_time = time.time()
        elapsed_time = loop_end_time - loop_start_time
        sleep_time = max(1 - elapsed_time, 0)
        time.sleep(sleep_time)

def perform_alert_checks(data_history, current_time):
    """Check for price or volume changes exceeding 2% from the previous 5-minute average."""
    alert_threshold = 2.0  # Percentage

    for symbol, records in data_history.items():
        if len(records) == 0:
            logging.warning(f'No data available for {symbol} to perform alert checks.')
            continue

        # Calculate averages
        average_price = sum(record[1] for record in records) / len(records)
        average_volume = sum(record[2] for record in records) / len(records)

        # Get the latest record
        latest_record = records[-1]
        latest_price = latest_record[1]
        latest_volume = latest_record[2]

        # Calculate percentage changes
        price_change = abs(latest_price - average_price) / average_price * 100
        volume_change = abs(latest_volume - average_volume) / average_volume * 100

        # Check if changes exceed the threshold
        if price_change > alert_threshold:
            alert_message = (f"Price Alert: {symbol} price changed by {price_change:.2f}% "
                             f"from the previous 5-minute average.")
            logging.warning(alert_message)
            # Output alert to a file
            with open('/app/alerts/alerts.txt', 'a') as f:
                f.write(f"{current_time} UTC: {alert_message}\n")

        if volume_change > alert_threshold:
            alert_message = (f"Volume Alert: {symbol} volume changed by {volume_change:.2f}% "
                             f"from the previous 5-minute average.")
            logging.warning(alert_message)
            # Output alert to a file
            with open('/app/alerts/alerts.txt', 'a') as f:
                f.write(f"{current_time} UTC: {alert_message}\n")

if __name__ == '__main__':
    # Establish database connection
    conn = connect_to_db()
    cursor = conn.cursor()

    # Create necessary tables
    create_tables(cursor, conn)

    # Create or replace the materialized view
    create_materialized_view(cursor, conn)

    # Start the materialized view refresh thread
    refresh_materialized_view_periodically(conn, interval_seconds=60)  # Refresh every 60 seconds

    # Start fetching, storing data, and monitoring for alerts
    fetch_and_store_data()
