FROM ghcr.io/astral-sh/uv:0.8-python3.13-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy application source
COPY src ./src

# Install the project itself
RUN uv sync --frozen

# Expose the FastAPI port (default 8000, can be overridden via APP_PORT env var)
EXPOSE 8000

# Run the FastAPI application with uvicorn
# Port will be read from APP_PORT environment variable in the app
CMD ["uv", "run", "python", "-m", "oddstracker.app"]
