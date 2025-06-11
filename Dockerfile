# Use official Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BOT_TOKEN="your_bot_token_here"  # Replace or pass during docker run
ENV PORT=8443
ENV MODE="webhook"  # or "webhook"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files (adjust if you have other files to exclude)
COPY . .

# Verify files were copied (debugging)
RUN ls -la /app

# Run the bot (make sure filename matches exactly)
CMD ["python", "bot.py"]
