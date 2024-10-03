# Data Challenge Test

This repository contains the solution for the Luxor Data Challenge, involving real-time cryptocurrency monitoring and alerting using the CoinGecko API, PostgreSQL, and Docker.

## Features

- **Real-Time Data Fetching:** Fetches data for Bitcoin (BTC), Ethereum (ETH), and Zcash (ZEC) every second.
- **Data Storage:** Stores fetched data in a PostgreSQL database.
- **Alert System:** Generates alerts if price or volume changes exceed 2% from the previous average every 5 seconds.
- **Dockerized Setup:** Easily deployable using Docker and Docker Compose.
- **Materialized View:** Maintains daily OHLCV (Open, High, Low, Close, Volume) data.

## Setup Instructions

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/Alex-2605/data-challenge.git
   cd luxor-challenge-test
=======
# data-challenge
Data Engineer Coding Challenge

