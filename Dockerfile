FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y libpq5 curl && rm -rf /var/lib/apt/lists/*

# Create non-root runtime user
RUN groupadd -r finveritas && useradd -r -g finveritas -d /app finveritas

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/finveritas/.local
ENV PATH=/home/finveritas/.local/bin:$PATH

COPY --chown=finveritas:finveritas . .

USER finveritas

# Default to Streamlit; override in compose for API
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1
