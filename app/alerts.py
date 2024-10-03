import logging

def perform_alert_checks(data_history, current_time, alert_threshold=2.0):
    """Check for price or volume changes exceeding the threshold from the previous average."""
    for symbol, records in data_history.items():
        if not records:
            logging.warning(f'No data available for {symbol} to perform alert checks.')
            continue

        # Calculate averages
        average_price = sum(record[1] for record in records) / len(records)
        average_volume = sum(record[2] for record in records) / len(records)

        # Get the latest record
        latest_price = records[-1][1]
        latest_volume = records[-1][2]

        # Calculate percentage changes
        price_change = abs(latest_price - average_price) / average_price * 100
        volume_change = abs(latest_volume - average_volume) / average_volume * 100

        # Generate alerts if thresholds are exceeded
        if price_change > alert_threshold:
            alert_message = f"Price Alert: {symbol} price changed by {price_change:.2f}% from the previous average."
            logging.warning(alert_message)
            with open('/app/alerts/alerts.txt', 'a') as f:
                f.write(f"{current_time} UTC: {alert_message}\n")

        if volume_change > alert_threshold:
            alert_message = f"Volume Alert: {symbol} volume changed by {volume_change:.2f}% from the previous average."
            logging.warning(alert_message)
            with open('/app/alerts/alerts.txt', 'a') as f:
                f.write(f"{current_time} UTC: {alert_message}\n")
