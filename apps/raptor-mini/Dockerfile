# Dockerfile
# Builder stage (optional if you have wheels; kept for future native deps)
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /build/
RUN pip install --upgrade pip wheel setuptools
RUN pip wheel --no-deps --wheel-dir /wheels -r requirements.txt

# Final runtime stage
FROM python:3.11-slim
WORKDIR /app

# Minimum runtime libs (add libpq or others if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheels (if any) and install
COPY --from=builder /wheels /wheels
COPY requirements.txt /app/
RUN if [ -d /wheels ]; then pip install --no-deps --no-index --find-links=/wheels -r /app/requirements.txt; else pip install --no-cache-dir -r /app/requirements.txt; fi

# Copy server code
COPY ./server /app/server
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENV MODEL_PATH=/models/raptor-mini
ENV PORT=8080
EXPOSE 8080

CMD ["/app/start.sh"]
