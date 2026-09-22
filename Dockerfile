FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY bot/ /app/bot/
COPY main.py /app/main.py

# Create directory for persistent SQLite database
RUN mkdir -p /app/data

# Run the Telegram bot
CMD ["python", "main.py"]
