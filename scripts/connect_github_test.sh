#!/usr/bin/env bash
set -euo pipefail
# Isolated GitHub auth for FLOP account01. Token is read from stdin and never printed.
SECURE_DIR="/opt/data/secure/flop-one-agent/account01"
export GH_CONFIG_DIR="$SECURE_DIR/gh"
mkdir -p "$GH_CONFIG_DIR"
chmod 700 "$SECURE_DIR" "$GH_CONFIG_DIR"
if [[ -t 0 ]]; then
  echo "Paste GitHub PAT on stdin, e.g.: printf '%s' '$TOKEN' | $0" >&2
  exit 2
fi
umask 077
gh auth login --hostname github.com --with-token >/dev/null
gh auth setup-git --hostname github.com >/dev/null
user_json=$(gh api user)
login=$(python3 - <<'PY' "$user_json"
import json,sys
print(json.loads(sys.argv[1]).get('login','unknown'))
PY
)
echo "GitHub test auth OK: ${login}"
