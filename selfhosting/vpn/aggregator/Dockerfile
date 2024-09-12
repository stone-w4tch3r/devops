# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements and application code
COPY requirements.txt /app/requirements.txt
COPY aggregator.py /app/aggregator.py

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5000

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "aggregator:app", "--host", "0.0.0.0", "--port", "5000"]
