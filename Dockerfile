# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system dependencies (e.g., for RHVoice or mic access if needed)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libasound2 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: expose a port (if you're using a web interface later)
# EXPOSE 5000

# Set entrypoint
CMD ["python", "main.py"]
