# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by OpenCV or other libraries
# These are common ones; you might need to adjust if build errors occur
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir can reduce image size
# Consider adding --default-timeout=100 to pip install if downloads are slow
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 8080 available to the world outside this container (Cloud Run default)
EXPOSE 8080

# Define environment variable for the port (Cloud Run will set this)
ENV PORT=8080

# Run app.py when the container launches using Gunicorn
# Gunicorn is recommended for production over Flask's built-in server.
# --workers 1: Start with 1 worker for the free tier, you can adjust.
# --threads 4: Number of threads per worker.
# --timeout 0: Allows longer request processing (EasyOCR can take time).
#                Cloud Run itself has a max request timeout (default 5 min, max 60 min).
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "0", "app:app"]