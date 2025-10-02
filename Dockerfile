FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Let the runtime (Railway, others) override the port with $PORT
ENV PORT=8000
EXPOSE ${PORT}

# Use sh -c so environment substitution works in exec form
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
