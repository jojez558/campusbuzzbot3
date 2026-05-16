FROM python:3.14.3-slim

# Set working directory
WORKDIR /app

# Install system + build dependencies
# Python 3.14 is new — many packages compile from source (no wheels yet)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libwebp-dev \
    cargo \
    rustc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first (important for 3.14 compatibility)
RUN pip install --upgrade pip setuptools wheel

# Install Python dependencies
# Some packages compile from source on 3.14 — this may take a few minutes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 campusbuzz && chown -R campusbuzz:campusbuzz /app
USER campusbuzz

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import asyncio, aiohttp; asyncio.run(aiohttp.ClientSession().get('http://localhost:8080/health'))" || exit 1

# Run the bot
CMD ["python", "main.py"]
