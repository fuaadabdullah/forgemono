# Dockerfile
FROM python:3.11-slim

# Avoid Python buffering problems and ensure logs flush
ENV PYTHONUNBUFFERED=1

# Set working directory where app will live inside the container
WORKDIR /app

# Copy requirements file for dependency installation from backend
COPY backend/requirements.txt /app/requirements.txt

# Install system deps (if you need build tools, uncomment below)
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  gcc \
  git \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY the backend source into container (not frontend/UI files)
COPY backend/ /app/backend/
COPY config/ /app/config/
COPY start.sh /app/start.sh

# Ensure backend is importable: make sure /app on PYTHONPATH and workdir is /app
ENV PYTHONPATH=/app

# Make sure backend is a package (helpful if missing __init__.py)
RUN if [ ! -f /app/backend/__init__.py ]; then touch /app/backend/__init__.py; fi

# Remove any pycache/mypy_cache that might have been copied
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Expose the app port
ENV PORT=8001
EXPOSE 8001

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
