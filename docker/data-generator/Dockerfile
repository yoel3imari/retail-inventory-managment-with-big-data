# Use a base image for Python and slim footprint
FROM python:3.9-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Set the Python path
ENV PYTHONPATH=/app

# First copy only project metadata (for better Docker caching)
COPY requirements.txt ./

# Install dependencies using uv (no cache, frozen lockfile)
RUN uv pip install --system -r requirements.txt

# Now copy the rest of the app
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "scripts/create_sample_data.py", "&&", "python", "scripts/data_generator.py"]
