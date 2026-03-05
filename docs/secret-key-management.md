# シークレット管理: DOTENV_PRIVATE_KEY の安全な保管方法

## 前提

`.env.keys` には dotenvx の復号用秘密鍵 (`DOTENV_PRIVATE_KEY`) が平文で保存されている。`.gitignore` で git 管理外にはなっているが、ディスク上に平文ファイルとして存在するため、AI ツール（Claude Code, Copilot 等）やマルウェアに読み取られるリスクがある。

**重要な前提**: dotenvx は `.env.keys` ファイルを直接読むのではなく、**環境変数 `DOTENV_PRIVATE_KEY`** を参照する。つまり、シェルに環境変数さえセットできれば `.env.keys` ファイルは不要。`docker-compose.yml` も `${DOTENV_PRIVATE_KEY}` を参照しており、ファイルに依存していない。

## 代替アプローチ一覧

### 1. macOS Keychain（`security` コマンド）

**保存先**: macOS のシステムキーチェーン（暗号化 DB）

```bash
# 格納
security add-generic-password \
  -a "$USER" \
  -s "dotenvx-sample-private-key" \
  -w "$(grep '^DOTENV_PRIVATE_KEY=' .env.keys | cut -d'=' -f2)"
rm .env.keys

# 取得
export DOTENV_PRIVATE_KEY=$(security find-generic-password \
  -a "$USER" -s "dotenvx-sample-private-key" -w)
```

| 項目 | 評価 |
|------|------|
| セットアップ | 追加ツール不要、最も手軽 |
| 日常利用 | Touch ID / パスワードでアクセス制御 |
| クロスプラットフォーム | macOS 限定 |
| コスト | 無料 |
| チーム共有 | 不向き |
| CI 統合 | 不可（GitHub Secrets 等を別途使用） |

### 2. 1Password CLI（`op`）

**保存先**: 1Password Vault（クラウド + ローカル暗号化キャッシュ）

```bash
# インストール & 格納
brew install 1password-cli
eval $(op signin)
op item create --category=password \
  --title="dotenvx-sample DOTENV_PRIVATE_KEY" \
  --vault="Development" \
  "password=$(grep '^DOTENV_PRIVATE_KEY=' .env.keys | cut -d'=' -f2)"
rm .env.keys

# 取得
export DOTENV_PRIVATE_KEY=$(op read "op://Development/dotenvx-sample DOTENV_PRIVATE_KEY/password")
```

| 項目 | 評価 |
|------|------|
| セットアップ | brew で簡単 |
| 日常利用 | Touch ID 連携あり、UX が良い |
| クロスプラットフォーム | macOS / Linux / Windows |
| コスト | 有料（$2.99/月〜） |
| チーム共有 | Vault 経由で容易 |
| CI 統合 | Service Account + 公式 GitHub Action あり |

### 3. Bitwarden CLI（`bw`）

**保存先**: Bitwarden Vault

```bash
brew install bitwarden-cli
bw login && export BW_SESSION="$(bw unlock --raw)"
# Secure Note として保存
export DOTENV_PRIVATE_KEY=$(bw get notes "dotenvx-sample-private-key")
```

| 項目 | 評価 |
|------|------|
| セットアップ | やや複雑（JSON ベース操作） |
| 日常利用 | セッション管理が面倒 |
| クロスプラットフォーム | macOS / Linux / Windows |
| コスト | 無料プランあり |
| チーム共有 | 可能 |
| CI 統合 | Bitwarden Secrets Manager で対応 |

### 4. AWS Secrets Manager / SSM Parameter Store

**保存先**: AWS マネージドサービス

```bash
aws secretsmanager create-secret \
  --name "dotenvx-sample/DOTENV_PRIVATE_KEY" \
  --secret-string "$(grep '^DOTENV_PRIVATE_KEY=' .env.keys | cut -d'=' -f2)"

export DOTENV_PRIVATE_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "dotenvx-sample/DOTENV_PRIVATE_KEY" \
  --query SecretString --output text)
```

| 項目 | 評価 |
|------|------|
| セットアップ | AWS アカウント必要 |
| 日常利用 | ネットワーク必須、レイテンシあり |
| クロスプラットフォーム | どこからでも |
| コスト | 従量課金 |
| チーム共有 | IAM で細かく制御可能 |
| CI 統合 | ECS/EKS 直接統合、GitHub Actions 対応 |

### 5. GPG 暗号化ファイル

**保存先**: `.env.keys.gpg`（暗号化済みファイル、git 管理可能）

```bash
gpg --encrypt --recipient your@email.com .env.keys
rm .env.keys
git add .env.keys.gpg

# 取得
export DOTENV_PRIVATE_KEY=$(gpg --decrypt --quiet .env.keys.gpg 2>/dev/null \
  | grep '^DOTENV_PRIVATE_KEY=' | cut -d'=' -f2)
```

| 項目 | 評価 |
|------|------|
| セットアップ | GPG 鍵管理が複雑 |
| 日常利用 | パスフレーズ入力（GPG Agent でキャッシュ可能） |
| クロスプラットフォーム | どこでも |
| コスト | 無料 |
| チーム共有 | 暗号化ファイルを git コミット可能（メンバー追加時に再暗号化必要） |
| CI 統合 | GPG 秘密鍵を GitHub Secrets に格納する方式 |

## 推奨

| ユースケース | 推奨アプローチ |
|-------------|---------------|
| **個人のローカル開発**（本プロジェクト） | macOS Keychain — 追加ツール不要、最も手軽 |
| **チーム開発** | 1Password CLI — 鍵共有 + CI 統合が充実 |
| **AWS 本番環境と統一したい** | AWS Secrets Manager |

## 共通の実装ステップ（どの方式でも）

1. 現在の `.env.keys` から鍵を選択先のストアに移行
2. `.env.keys` をディスクから削除
3. `.zshrc` 等にヘルパー関数/alias を追加して取得を自動化
4. `docker-compose.yml` は変更不要（既に `${DOTENV_PRIVATE_KEY}` を参照）
5. CI では GitHub Secrets 等の専用機構を使い、ローカルのストアとは別管理
6. CLAUDE.md の「ローカル開発の手順」セクションを更新

## 対象ファイルへの影響

| ファイル | 対応 |
|---------|------|
| `docker-compose.yml` | 変更不要（確認済み） |
| `Dockerfile` | 変更不要 |
| `.gitignore` | GPG 方式の場合のみ `.env.keys.gpg` を追加 |
| `CLAUDE.md` | 鍵取得手順の記述を更新 |
| `README.md` | 必要に応じて手順を更新 |
