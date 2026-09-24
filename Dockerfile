# TDC Matcher — single container running the Streamlit app.
# Build:  docker build -t tdc-matcher .
# Run:    docker run -p 8501:8501 tdc-matcher
# The main development workflow remains uv (see README.md).

FROM python:3.11-slim

# uv binary, pinned to the version that generated uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /uvx /bin/

WORKDIR /app

# Install third-party dependencies first so this layer caches
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application and install the project itself
COPY README.md app.py ./
COPY src/ ./src/
COPY data/ ./data/
RUN uv sync --frozen --no-dev

EXPOSE 8501

CMD ["uv", "run", "--no-sync", "--no-dev", "streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
