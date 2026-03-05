#!/usr/bin/env bash
# keychain-setup.sh — dotenvx 秘密鍵を macOS Keychain に格納するセットアップスクリプト
set -euo pipefail

SERVICE_NAME="dotenvx-sample-private-key"
ENV_KEYS_FILE=".env.keys"

# macOS チェック
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: このスクリプトは macOS 専用です。" >&2
  exit 1
fi

# .env.keys の存在確認
if [[ ! -f "${ENV_KEYS_FILE}" ]]; then
  echo "ERROR: ${ENV_KEYS_FILE} が見つかりません。" >&2
  echo "       dotenvx encrypt を実行して .env.keys を生成してください。" >&2
  exit 1
fi

# DOTENV_PRIVATE_KEY を抽出
PRIVATE_KEY=$(grep "^DOTENV_PRIVATE_KEY=" "${ENV_KEYS_FILE}" | cut -d'=' -f2)

if [[ -z "${PRIVATE_KEY}" ]]; then
  echo "ERROR: ${ENV_KEYS_FILE} に DOTENV_PRIVATE_KEY が見つかりません。" >&2
  exit 1
fi

# Keychain に格納（-U で既存エントリを上書き）
security add-generic-password \
  -a "${USER}" \
  -s "${SERVICE_NAME}" \
  -w "${PRIVATE_KEY}" \
  -U

echo "Keychain への登録が完了しました。"
echo "サービス名: ${SERVICE_NAME} / アカウント: ${USER}"
echo ""
echo "以下のコマンドで取得できることを確認してください:"
echo "  security find-generic-password -a \"\${USER}\" -s \"${SERVICE_NAME}\" -w"
echo ""
echo "確認後、.env.keys をファイルシステムから削除することを推奨します:"
echo "  rm ${ENV_KEYS_FILE}"
