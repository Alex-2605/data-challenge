# CryptoMonitor

## Overview

**CryptoMonitor** is a streamlined tool designed to provide real-time monitoring and alerting for three major cryptocurrencies: Bitcoin (BTC), Ethereum (ETH), and Zcash (ZEC). Leveraging CoinGecko's API, CryptoMonitor fetches data every second, ensuring up-to-date insights into market movements. This data is meticulously stored in a PostgreSQL database, facilitating both immediate and historical analysis through well-structured tables and materialized views.

### Key Features

- **Real-Time Data Ingestion:**
  - **Frequent Updates:** Retrieves the latest price and volume data for BTC, ETH, and ZEC every second from CoinGecko's API.
  - **Resilient Fetching:** Utilizes retry mechanisms to handle transient API failures, ensuring continuous data collection without manual intervention.

- **Data Storage and Management:**
  - **PostgreSQL Integration:** Stores incoming data in a dedicated `ticker_data` table, capturing essential metrics like timestamp, symbol, price in USD, and trading volume.
  - **Historical Analysis:** Maintains a materialized view `daily_ohlcv` that aggregates data into daily Open, High, Low, Close, and Volume (OHLCV) metrics for each cryptocurrency, enabling efficient historical data analysis.

- **Alerting System:**
  - **Threshold-Based Alerts:** Monitors price and volume changes, triggering alerts when deviations exceed 2% from the previous five-minute average.
  - **Persistent Logging:** Logs all triggered alerts to a designated `alerts.txt` file, ensuring alerts are recorded and accessible for review.
  - **Scalable Alerting:** Designed to accommodate additional metrics and cryptocurrencies with minimal adjustments, allowing for flexible expansion based on evolving requirements.

- **Scalability and Performance:**
  - **Optimized Data Handling:** Implements efficient data aggregation and indexing strategies to manage large volumes of incoming data without compromising retrieval speeds.
  - **Dockerized Deployment:** Utilizes Docker and Docker Compose for seamless deployment, ensuring consistency across different environments and simplifying scalability efforts.

- **Comprehensive Monitoring:**
  - **Health Checks:** Incorporates health checks for database connectivity, ensuring the system remains operational and can recover from potential disruptions.
  - **Logging:** Employs structured logging to facilitate easy monitoring and debugging of the application's operations and alerting mechanisms.

### Design & Architecture

```mermaid
graph TD
    A[CoinGecko API] -->|Fetch Data Every Second| B[fetcher.py]
    B -->|Process Data| C[alerts.py]
    B -->|Insert Data| D[db.py]
    D --> E[ticker_data Table]
    D --> F[daily_ohlcv Materialized View]
    F -->|Aggregate Data| E
    C -->|Log Alerts| G[alerts/alerts.txt]
    F -->|Refresh Every 60s| F
    subgraph Docker Container
        B
        C
        D
        F
    end
    G -->|Persistent Storage| H[Host Machine]
    ```


CryptoMonitor is thoughtfully architected to prioritize reliability and maintainability. The application is divided into modular components, each handling specific responsibilities:

- **Data Ingestion (`fetcher.py`):** Handles the continuous retrieval of data from CoinGecko's API, ensuring that the database is consistently updated with the latest information.
- **Alert Processing (`alerts.py`):** Evaluates recent data to identify significant changes and logs corresponding alerts.
- **Database Management (`db.py`):** Manages the creation and maintenance of the PostgreSQL database and its tables.
- **View Handling (`views.py`):** Manages the creation and refreshing of the materialized view for historical data analysis.
- **Orchestration (`main.py`):** Serves as the entry point, coordinating the various modules to ensure smooth and efficient operation.

## Tools Used for Each Stage of the Stack

### 1. Sources

- **CoinGecko API**
  - **Purpose:** Provides real-time cryptocurrency market data for Bitcoin (BTC), Ethereum (ETH), and Zcash (ZEC).
  - **Integration:** Accessed via HTTP GET requests using the `requests` library in the `fetcher.py` module.

### 2. Ingestion & Transformation

- **Python `requests` Library**
  - **Purpose:** Facilitates HTTP requests to the CoinGecko API for data retrieval.
  - **Usage:** Implemented in the `fetcher.py` module to fetch data every second.

- **Python `retry` Library**
  - **Purpose:** Implements retry mechanisms to handle transient API and database failures.
  - **Usage:** Decorates functions in `fetcher.py` and `db.py` to ensure robust data fetching and insertion.

- **Data Processing in `fetcher.py`**
  - **Purpose:** Transforms raw API responses into structured data points (`symbol`, `price_usd`, `volume`) for storage and analysis.
  - **Mechanism:** Parses JSON responses and maintains a rolling window of data history for each cryptocurrency to facilitate alert evaluations.

### 3. Storage

- **PostgreSQL Database**
  - **Purpose:** Acts as the central repository for all ingested cryptocurrency data.
  - **Management:**
    - **`db.py` Module:** Handles database connections, table creation (`ticker_data`), and ensures data integrity.
    - **Schema Design:** 
      - **`ticker_data` Table:** Stores per-second data ingestion with fields for `timestamp`, `symbol`, `price_usd`, and `volume`.
      - **Materialized Views:** Managed by `views.py` to aggregate data into daily OHLCV (Open, High, Low, Close, Volume) metrics.

- **Dockerized PostgreSQL**
  - **Purpose:** Ensures a consistent and isolated database environment across different deployment setups.
  - **Configuration:** Defined in `docker-compose.yml` with environment variables for database credentials and persistent storage using Docker volumes.

### 4. Processing

- **`alerts.py` Module**
  - **Purpose:** Monitors price and volume data to trigger alerts when changes exceed a specified threshold, logging these alerts for review.
  - **Functionality:**
    - **Threshold-Based Alerts:** Triggers alerts when price or volume changes exceed a 2% deviation from the previous five-minute average.
    - **Logging:** Writes alert messages to `alerts.txt` for persistent record-keeping.

- **`views.py` Module**
  - **Purpose:** Creates and manages a materialized view for daily OHLCV data, enabling efficient historical data analysis.
  - **Features:**
    - **Aggregation:** Computes daily OHLCV metrics from raw `ticker_data`.
    - **Periodic Refresh:** Ensures the materialized views are up-to-date by refreshing them at regular intervals (e.g., every 60 seconds).

### 5. Output (Analysis)

- **`alerts.txt` File**
  - **Purpose:** Stores all triggered alerts, providing a historical log of significant market movements.
  - **Location:** Mapped to the host machine via Docker volumes, ensuring persistence beyond container lifecycles.

- **Materialized Views (`daily_ohlcv`)**
  - **Purpose:** Enables efficient querying and analysis of aggregated historical data for each cryptocurrency.
  - **Usage:** Supports trend analysis, reporting, and data-driven decision-making by providing quick access to daily OHLCV metrics.

### 6. Testing and Security

- **Testing Tools**
  - **Python `unittest` Framework**
    - **Purpose:** Facilitates the creation of unit tests to ensure individual components (functions and modules) behave as expected.
    - **Usage:** Can be implemented to test modules like `alerts.py`, `fetcher.py`, and `db.py` for correctness and reliability.

  - **Mocking Libraries (`unittest.mock`)**
    - **Purpose:** Simulates API responses and database interactions to test the application's resilience and alerting logic without relying on external systems.
    - **Usage:** Used in unit and integration tests to mock CoinGecko API responses and database operations.

- **Security Measures**
  - **Environment Variables**
    - **Purpose:** Stores sensitive information like database credentials securely, preventing hardcoding of secrets in the codebase.
    - **Management:** Utilizes `.env` files in conjunction with `docker-compose.yml` to inject environment variables into the application containers.

  - **Database Access Control**
    - **Purpose:** Restricts database access to authorized users and services only.
    - **Implementation:** Configures PostgreSQL roles and permissions to ensure that the application can only perform necessary operations (e.g., INSERT, SELECT).

  - **Secure API Communication**
    - **Purpose:** Ensures that data fetched from the CoinGecko API is transmitted securely.
    - **Implementation:** Utilizes HTTPS for all API requests to encrypt data in transit.

  - **Logging Security**
    - **Purpose:** Prevents sensitive data from being inadvertently logged.
    - **Implementation:** Configures logging to exclude sensitive information and restricts access to log files (`alerts.txt`).

- **Docker Security**
  - **Trusted Base Images**
    - **Purpose:** Minimizes vulnerabilities by using official and trusted Docker images (e.g., `postgres:13` for PostgreSQL).

  - **Least Privilege Principle**
    - **Purpose:** Runs containers with the minimum required permissions to perform their tasks, reducing the attack surface.

  - **Regular Updates**
    - **Purpose:** Keeps Docker images and containers up-to-date with the latest security patches and updates.

### Monitoring & Scalability

- **Alert System:** Implements a push-based approach to monitoring, where alerts are generated and logged in real-time as data is ingested.
- **Scalability Considerations:** Designed to handle increasing volumes of data by optimizing database indexing and utilizing Docker for scalable deployments.

### Future Enhancements

With additional time and resources, CryptoMonitor can be further enhanced to include features such as real-time dashboards, advanced notification systems (e.g., email or SMS alerts), and support for a broader range of cryptocurrencies and metrics.

---
