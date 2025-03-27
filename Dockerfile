# https://docs.astral.sh/uv/guides/integration/docker/#using-uv-in-docker
# https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
FROM ghcr.io/astral-sh/uv:python3.13-alpine
LABEL maintainer="eimeredelin@sberbank.ru"

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project into `/code`
WORKDIR /code

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/code/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# FastAPI requirement: write CMD in exec form, do not use shell form
# https://fastapi.tiangolo.com/deployment/docker/#use-cmd-exec-form
CMD ["python", "app/main.py"]
