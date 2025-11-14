FROM apache/spark:3.4.1

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Copy job submission script
COPY entrypoint.sh /opt/spark/entrypoint.sh
RUN chmod +x /opt/spark/entrypoint.sh

# Set working directory
WORKDIR /opt/spark

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

ENTRYPOINT ["/opt/spark/entrypoint.sh"]