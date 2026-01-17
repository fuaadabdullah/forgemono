# Goblin Sandbox - Minimal Python execution environment
# This image provides isolated code execution with security restrictions

FROM python:3.11-slim-bookworm

# Security: Create non-root user
RUN useradd --create-home --shell /bin/false sandbox

# Security: Remove unnecessary packages
RUN apt-get update && \
    apt-get remove -y --purge --auto-remove \
    wget curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Install minimal Python packages for sandbox
# Using lighter packages to speed up build
RUN pip install --no-cache-dir \
    sympy==1.12 \
    && rm -rf /root/.cache/pip

# Security: Restrict filesystem
RUN chmod 755 /home/sandbox && \
    chown -R sandbox:sandbox /home/sandbox

# Set working directory
WORKDIR /home/sandbox

# Switch to non-root user
USER sandbox

# Default command (will be overridden)
CMD ["python3", "-c", "print('Sandbox ready')"]

# Labels
LABEL org.opencontainers.image.title="Goblin Sandbox"
LABEL org.opencontainers.image.description="Minimal Python execution environment for secure code sandbox"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="GoblinOS"
