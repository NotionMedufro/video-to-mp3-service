FROM python:3.9-slim

# Install system dependencies (ffmpeg is required for audio conversion)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render/Heroku usually use environment variable PORT, default to 8000)
ENV PORT=8000
EXPOSE $PORT

# Command to run the application using the PORT environment variable
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port \${PORT:-8000}"
