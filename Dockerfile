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

# Expose FastAPI
EXPOSE 8000

CMD ["uv", "run", "python", "-m", "oddstracker.app"]
