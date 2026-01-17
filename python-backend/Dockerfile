FROM --platform=linux/amd64 python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd --create-home --shell /bin/bash noah

# Create app dir and fix ownership
RUN mkdir -p /app && chown -R noah:noah /app

# Switch to noah
USER noah
WORKDIR /home/noah

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/noah/.local/bin:${PATH}"

# Work in app directory
WORKDIR /app

# Copy dependency files
COPY --chown=noah:noah pyproject.toml uv.lock* ./

# Install deps
RUN uv sync --frozen --no-cache

# Copy rest of app
COPY --chown=noah:noah . .

CMD ["uv", "run", "python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
