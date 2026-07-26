FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for compiling some Python packages and connecting to PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements list
COPY backend/requirements.txt /app/requirements.txt

# Install python requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy backend app files
COPY backend /app

# Ensure python path includes /app
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
