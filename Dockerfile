# Base Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for lxml, etc.)
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev libffi-dev python3-dev && \
    apt-get clean

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose port (for Render or Railway)
EXPOSE 10000

# Command to run the bot
CMD ["python", "main.py"]
