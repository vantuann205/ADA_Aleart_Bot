FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run bot with proper unbuffered output
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "bot.py"]