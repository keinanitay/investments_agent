# 1. Base Image: Explicitly lock to Python 3.11
FROM python:3.11-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy requirements first (Docker caches this layer to speed up builds)
COPY requirements.txt .

# 4. Install dependencies globally in the container (no need for venv here)
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Run the application
# We use '0.0.0.0' to allow external connections
# We use '${PORT:-8000}' to support GCP's dynamic port assignment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]