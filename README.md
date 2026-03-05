# dotenvx-sample

dotenvx のシークレット管理機能を技術検証するための FastAPI サンプルアプリ。

- GitHub REST API でプロフィールを取得・表示
- 閲覧履歴を PostgreSQL に保存
- `GITHUB_TOKEN` / `DATABASE_URL` / `POSTGRES_PASSWORD` を **dotenvx** で管理

## 動作フロー

```
.env (暗号化済み, git 管理 OK)
.env.keys → DOTENV_PRIVATE_KEY (gitignore, ホストで export)

docker-compose: DOTENV_PRIVATE_KEY=${DOTENV_PRIVATE_KEY} → app コンテナへ渡す
CMD: dotenvx run -- uvicorn ... → .env を復号して uvicorn プロセスに注入
```

> **注意**: dotenvx は `dotenvx run` で起動した子プロセスにのみ変数を注入する。
> コンテナのシェル環境全体には展開されないため、`docker compose exec app env` では値が見えない。
> これは意図した動作（プロセス外への漏洩防止）。

## クイックスタート

### 前提

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [dotenvx](https://dotenvx.com/) (`brew install dotenvx/brew/dotenvx` など)

### 1. .env を作成して暗号化

```bash
cp .env.example .env
# .env を編集して実際の値を設定
vi .env

# dotenvx で暗号化 (.env が暗号化され、.env.keys が生成される)
dotenvx encrypt
```

### 2. 秘密鍵と POSTGRES_PASSWORD をエクスポート

`.env.keys` の値はクォートなしで記録されているため `cut -d'=' -f2` を使う。

```bash
export DOTENV_PRIVATE_KEY=$(grep "^DOTENV_PRIVATE_KEY=" .env.keys | cut -d'=' -f2)
export POSTGRES_PASSWORD=<.env に設定したパスワード>
```

### 3. 起動

```bash
docker compose build
docker compose up -d
```

### 4. 動作確認

```bash
# dotenvx が復号・注入していることをログで確認
docker compose logs app
# 期待出力: "[dotenvx@x.x.x] injecting env (4) from .env"

# エンドポイント確認
curl http://localhost:8000/                      # ホーム画面
curl http://localhost:8000/profile/torvalds      # GitHub API + DB 書き込み
curl http://localhost:8000/history               # DB 読み取り
```

GitHub プロフィールが正常に取得できれば `GITHUB_TOKEN` の注入成功。

## シークレットを更新する

値を変えるときは `dotenvx set` を使う（自動で再暗号化される）。

```bash
# KEY と VALUE はスペース区切り（KEY=VALUE 形式は不可）
dotenvx set GITHUB_TOKEN <新しいトークン>
dotenvx set POSTGRES_PASSWORD <新しいパスワード>
```

変更後は Docker イメージを再ビルドして反映する（`.env` はイメージに COPY されているため）。

```bash
docker compose build
docker compose up -d
```

> **DB パスワードを変更した場合**: PostgreSQL は既存ボリュームがあると `POSTGRES_PASSWORD`
> を無視して再初期化しない。ボリュームを削除してから起動し直すこと。
>
> ```bash
> docker compose down -v   # ボリューム削除（データも消える）
> docker compose up -d
> ```

## ローカル開発

```bash
uv sync --extra dev
cp .env.example .env.local
# .env.local に平文で値を設定

dotenvx run --env-file=.env.local -- uvicorn app.main:app --reload
```

## テスト

```bash
uv run pytest
```

## エンドポイント

| Path | Description |
|------|-------------|
| `GET /` | 検索フォーム |
| `GET /profile/{username}` | GitHub API 呼び出し → DB 保存 → 表示 |
| `GET /history` | DB から閲覧履歴を取得して表示 |

## シークレット管理の仕組み

| ファイル | git 管理 | 内容 |
|---------|---------|------|
| `.env` | OK（暗号化済み） | 暗号化されたシークレット |
| `.env.keys` | **禁止** | 復号用秘密鍵 |
| `.env.example` | OK | 変数名のみ（値なし） |

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| `INVALID_PRIVATE_KEY` エラー | `DOTENV_PRIVATE_KEY` が正しく export されていない | `grep "^DOTENV_PRIVATE_KEY=" .env.keys \| cut -d'=' -f2` で再取得 |
| `password authentication failed` | DB ボリュームの初期化パスワードと `POSTGRES_PASSWORD` が不一致 | `docker compose down -v` でボリュームを削除して再起動 |
| `docker compose exec app env` で変数が見えない | dotenvx の仕様（子プロセス限定注入） | 正常。アプリの動作で確認する |
