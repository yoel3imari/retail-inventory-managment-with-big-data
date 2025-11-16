# Use a base image for Python and slim footprint
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Set the Python path
ENV PYTHONPATH=/app

# First copy only project metadata (for better Docker caching)
COPY requirements.txt pyproject.toml uv.lock* README.md ./

# Install dependencies using uv (frozen lockfile)
RUN uv sync --frozen --no-editable

# Now copy the rest of the app
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "python scripts/create_sample_data.py --stores 10 --products 100 --categories 10 && echo 'Sample data created successfully' && python scripts/data_generator.py --duration 60 --rate 10"]
