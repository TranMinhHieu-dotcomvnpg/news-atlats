FROM python:3.10

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=News_Atlats_AI.settings
ENV PYTHONPATH=/app

# Create necessary directories
RUN mkdir -p /app/media

# Run migrations and start server
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && gunicorn News_Atlats_AI.wsgi:application --bind 0.0.0.0:8000"]