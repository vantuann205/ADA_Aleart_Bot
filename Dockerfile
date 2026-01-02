FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Make startup script executable
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Run bot with proper unbuffered output
ENV PYTHONUNBUFFERED=1

# Use startup script to ensure clean process
CMD ["/app/startup.sh"]