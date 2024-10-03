import logging
import time  # Imported to use time.sleep()

def create_materialized_view(cursor, conn):
    """Create the materialized view for daily OHLCV data if it doesn't exist."""
    cursor.execute('''
    CREATE MATERIALIZED VIEW IF NOT EXISTS daily_ohlcv AS
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
    ''')

    # Create a unique index if it doesn't exist
    cursor.execute('''
    CREATE UNIQUE INDEX IF NOT EXISTS daily_ohlcv_idx ON daily_ohlcv (symbol, day);
    ''')
    conn.commit()
    logging.info('Materialized view daily_ohlcv ensured with unique index.')

def refresh_materialized_view_periodically(conn, interval_seconds=60):
    """Refresh the materialized view at regular intervals."""
    import threading

    def refresh():
        while True:
            try:
                with conn.cursor() as cursor:
                    cursor.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY daily_ohlcv;')
                    conn.commit()
                    logging.info('Materialized view daily_ohlcv refreshed concurrently.')
            except Exception as e:
                logging.error(f'Error refreshing materialized view: {e}')
            time.sleep(interval_seconds)  # Uses the imported time module

    # Run the refresh in a separate daemon thread
    threading.Thread(target=refresh, daemon=True).start()
    logging.info(f'Started materialized view refresh thread (every {interval_seconds} seconds).')
