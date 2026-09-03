FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY . .
EXPOSE 80
CMD ["uv", "run", "gunicorn", "--workers", "1", "--bind", "0.0.0.0:80", "app:app"]