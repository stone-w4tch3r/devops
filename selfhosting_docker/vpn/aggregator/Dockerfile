# syntax=docker/dockerfile:1

# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install dependencies using BuildKit's cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY aggregator.py /app/aggregator.py

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "aggregator:app", "--host", "0.0.0.0", "--port", "5000"]