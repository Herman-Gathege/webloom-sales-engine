FROM python:3.12-slim

# Runtime only; no build tools are needed by the pinned wheels in
# requirements*.txt. Tests run inside this image, so the dev requirements are
# installed alongside the runtime ones for now.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

COPY app ./app
COPY tests ./tests
COPY alembic ./alembic
COPY alembic.ini pyproject.toml docker-entrypoint.sh ./

RUN chmod +x /app/docker-entrypoint.sh

# Run as a non-root user. The migration and seed write to PostgreSQL, not to
# the filesystem, so nothing here needs root at runtime.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
