FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Install playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 3000 8000

# Default command
CMD ["poetry", "run", "python", "-m", "scrapinium.main"]