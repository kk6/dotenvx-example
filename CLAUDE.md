# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

dotenvx のシークレット管理を技術検証するための FastAPI サンプルアプリ。GitHub REST API でプロフィールを取得し、閲覧履歴を PostgreSQL に保存する。`GITHUB_TOKEN` / `DATABASE_URL` / `POSTGRES_PASSWORD` を **dotenvx** で暗号化管理している。

## Commands

```bash
# 依存関係インストール（開発用）
uv sync --extra dev

# ローカル起動（dotenvx 経由で .env.local を読み込む）
dotenvx run --env-file=.env.local -- uvicorn app.main:app --reload

# テスト
uv run pytest

# 単一テストファイル実行
uv run pytest tests/test_github.py -v

# Lint / Format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Docker
docker compose build
docker compose up -d
docker compose logs app   # dotenvx の注入ログを確認
```

## Architecture

```
src/app/
├── main.py      # FastAPI ルート定義・lifespan (DB 初期化)
├── database.py  # SQLAlchemy async engine / セッション / init_db
├── github.py    # GitHub REST API クライアント (httpx)
└── models.py    # SQLAlchemy ORM モデル (ProfileHistory)

templates/       # Jinja2 テンプレート
static/          # 静的ファイル
```

- **エントリポイント**: `app.main:app`（`PYTHONPATH=/app/src` を前提）
- **DB 接続**: `os.environ["DATABASE_URL"]` — dotenvx が注入しなければ `KeyError` で即時失敗（意図的）
- **GitHub 認証**: `GITHUB_TOKEN` が未設定でも動作するが、未認証だと 60 req/hour 制限

## dotenvx シークレット管理

| ファイル | git 管理 | 用途 |
|---------|---------|------|
| `.env` | OK（暗号化済み） | 暗号化されたシークレット |
| `.env.keys` | **禁止**（gitignore 済み） | 復号用秘密鍵 |
| `.env.example` | OK | 変数名のみ（値なし） |

### 重要な動作仕様

- dotenvx は `dotenvx run` で起動した **子プロセスにのみ** 変数を注入する
- `docker compose exec app env` で変数が見えないのは**正常動作**
- 秘密鍵の取得: `grep "^DOTENV_PRIVATE_KEY=" .env.keys | cut -d'=' -f2`（クォートなしのため `cut` が必要）
- シークレット更新: `dotenvx set KEY value`（`KEY=value` 形式は不可）

### ローカル開発の手順

```bash
cp .env.example .env.local
# .env.local に平文で値を設定（git 管理しない）
export DOTENV_PRIVATE_KEY=$(grep "^DOTENV_PRIVATE_KEY=" .env.keys | cut -d'=' -f2)
```

## Testing Patterns

テストは `pytest-asyncio`（`asyncio_mode = "auto"`）+ `pytest-httpx` を使用。外部 HTTP 通信は `HTTPXMock` でモックする。DB を必要とするルートテストは現状存在しない（`github.py` の単体テストのみ）。
