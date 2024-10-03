import time
from datetime import datetime, timedelta
import logging
from retry import retry
import requests  # Ensure this is imported

from .alerts import perform_alert_checks

@retry(tries=3, delay=5, backoff=2, jitter=(1,3))
def fetch_data():
    """Fetch data from the CoinGecko API."""
    response = requests.get(
        'https://api.coingecko.com/api/v3/coins/markets',
        params={
            'vs_currency': 'usd',
            'ids': 'bitcoin,ethereum,zcash',
            'order': 'market_cap_desc',
            'per_page': 100,
            'page': 1,
            'sparkline': 'false'
        }
    )
    response.raise_for_status()
    return response.json()

@retry(tries=3, delay=5, backoff=2, jitter=(1,3))
def insert_data(cursor, conn, current_time, symbol, price, volume):
    """Insert fetched data into the database."""
    cursor.execute(
        'INSERT INTO ticker_data (timestamp, symbol, price_usd, volume) VALUES (%s, %s, %s, %s)',
        (current_time, symbol, price, volume)
    )
    conn.commit()

def maintain_history(data_history, symbol, current_time, price, volume, window_minutes=5):
    """Maintain a rolling window of data history."""
    data_history[symbol].append((current_time, price, volume))
    five_minutes_ago = current_time - timedelta(minutes=window_minutes)
    data_history[symbol] = [
        record for record in data_history[symbol] if record[0] >= five_minutes_ago
    ]

def fetch_and_store_data(conn, alert_interval=300):
    """Fetch data, store it, maintain history, and perform alerts."""
    data_history = {
        'BTC': [],
        'ETH': [],
        'ZEC': []
    }

    next_alert_time = datetime.utcnow() + timedelta(seconds=alert_interval)

    cursor = conn.cursor()

    while True:
        loop_start_time = time.time()
        try:
            # Fetch data
            data = fetch_data()
            current_time = datetime.utcnow()

            for coin in data:
                symbol = coin['symbol'].upper()
                price = float(coin['current_price'])
                volume = float(coin['total_volume'])

                # Insert into DB
                insert_data(cursor, conn, current_time, symbol, price, volume)
                logging.info(f'Inserted data for {symbol} at {current_time} UTC.')

                # Maintain history
                maintain_history(data_history, symbol, current_time, price, volume)

            # Perform alert checks every `alert_interval` seconds
            if current_time >= next_alert_time:
                logging.info(f'Performing alert checks at {current_time} UTC.')
                perform_alert_checks(data_history, current_time)
                next_alert_time = current_time + timedelta(seconds=alert_interval)
                logging.info(f'Next alert check scheduled at {next_alert_time} UTC.')

        except Exception as e:
            logging.error(f'An error occurred in fetch_and_store_data: {e}')

        # Calculate elapsed time and sleep to maintain 1 call per second
        loop_end_time = time.time()
        elapsed_time = loop_end_time - loop_start_time
        sleep_time = max(1 - elapsed_time, 0)
        time.sleep(sleep_time)
