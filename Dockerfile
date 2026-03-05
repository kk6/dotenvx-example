FROM python:3.12-slim

# dotenvx インストール
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sfS https://dotenvx.sh/install.sh | sh && \
    apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV PYTHONPATH=/app/src \
    UV_NO_CACHE=1 \
    PATH="/app/.venv/bin:$PATH"

# 依存関係のインストール (ソースより先にコピーしてレイヤーキャッシュを活用)
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# アプリケーションコードをコピー
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY .env ./

# 非 root ユーザーで実行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["dotenvx", "run", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
