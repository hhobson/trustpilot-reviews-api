# syntax=docker.io/docker/dockerfile:1.7-labs

ARG PYTHON_VERSION="3.12"

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS builder

# - Silence uv complaining about not being able to use hard links
# - Tell uv to byte-compile packages for faster application startups
# - Prevent uv from accidentally downloading isolated Python builds
# - Set Python version
# - Declare `/app` as the target for `uv sync`.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python${PYTHON_VERSION} \
    UV_PROJECT_ENVIRONMENT=/app

# Install SQLite, SQLCipher and dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        gcc \
        libsqlcipher0 \
        libsqlcipher-dev \
        sqlcipher \
        sqlite3

# Install dependencies without application and cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=./uv.lock,target=uv.lock \
    --mount=type=bind,source=./pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

WORKDIR /app
COPY . /app

# Install application
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PATH=/app/bin:$PATH
ENV PYTHONPATH=/app

RUN groupadd -r app && \
    useradd -r -d /app -g app -N app

COPY --from=builder --exclude=uv.lock --chown=app:app /app /app
COPY --from=builder --chown=app:app /usr/bin/sqlite3 /app/bin
COPY --from=builder --chown=app:app /usr/bin/sqlcipher /app/bin
COPY --from=builder --chown=app:app /usr/lib/x86_64-linux-gnu/libsqlcipher.so.0 /usr/lib/x86_64-linux-gnu/libsqlcipher.so.0
COPY --chown=app:app ./data /app/data

WORKDIR /app
USER app

CMD ["fastapi", "run", "--host", "0.0.0.0", "src/api.py"]
