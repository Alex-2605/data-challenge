# Use the official Python image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Install the required packages.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code into the container.
COPY . .

# Run the Python application.
CMD ["python", "main.py"]
