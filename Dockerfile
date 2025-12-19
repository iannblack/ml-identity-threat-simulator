# Multi-stage Dockerfile for ML Identity Threat Simulator
# Optimized for production use with minimal image size

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY pyproject.toml ./

# Install dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir build && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.11-slim

# Set metadata
LABEL maintainer="ImNotKilian"
LABEL description="IAM Threat Simulator for ML pipelines on GCP"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    IAM_SIMULATOR_LOGGING_LEVEL=INFO

# Create non-root user for security
RUN groupadd -r iamsim && useradd -r -g iamsim iamsim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=iamsim:iamsim . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories for data and output
RUN mkdir -p /app/data /app/output && \
    chown -R iamsim:iamsim /app

# Switch to non-root user
USER iamsim

# Expose port (if needed for future web interface)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.core.models; print('OK')" || exit 1

# Default command
ENTRYPOINT ["iam-simulator"]
CMD ["--help"]
