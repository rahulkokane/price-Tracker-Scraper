FROM python:3.11-slim

# -----------------------------
# 1) Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    unzip \
    # Playwright Chromium dependencies
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpangocairo-1.0-0 \
    libcups2 \
    libdrm2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# 2) Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# 3) Clone your GitHub repo
# -----------------------------
RUN git clone https://github.com/rahulkokane/price-Tracker-Scraper.git

# -----------------------------
# 4) Go inside scraper folder
# -----------------------------
WORKDIR /app/price-Tracker-Scraper/scraper

# -----------------------------
# 5) Install Python dependencies
# -----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# 6) Install Playwright + Chromium
# -----------------------------
RUN pip install --no-cache-dir playwright
RUN playwright install chromium

# -----------------------------
# 7) Default command
# -----------------------------
CMD ["python", "scrape_single_product.py"]
