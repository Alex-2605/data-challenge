import logging

from db import connect_to_db, create_tables
from views import create_materialized_view, refresh_materialized_view_periodically
from fetcher import fetch_and_store_data

def setup_logging():
    """Configure logging."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Main function to set up the database, views, and start data fetching."""
    setup_logging()

    # Establish database connection
    conn = connect_to_db()
    cursor = conn.cursor()

    # Create necessary tables
    create_tables(cursor, conn)

    # Create materialized view
    create_materialized_view(cursor, conn)

    # Start the materialized view refresh thread
    refresh_materialized_view_periodically(conn, interval_seconds=60)  # Refresh every 60 seconds

    # Start fetching, storing data, and monitoring for alerts
    fetch_and_store_data(conn, alert_interval=300)  # Alerts every 5 minutes

if __name__ == '__main__':
    main()
