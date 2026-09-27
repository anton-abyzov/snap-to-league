#!/usr/bin/env bash
# Put the local app on https://snap.easychamp.com: start a Cloudflare quick tunnel (HTTP/2, which
# works on venue Wi-Fi that blocks QUIC), then point the edge Worker at the new tunnel address.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=data/tunnel.log
cloudflared tunnel --no-autoupdate --protocol http2 --url http://localhost:8077 >"$LOG" 2>&1 &
for _ in $(seq 1 30); do
  URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$LOG" | head -1 || true)
  [ -n "$URL" ] && break
  sleep 1
done
[ -n "${URL:-}" ] || { echo "tunnel did not start; see $LOG"; exit 1; }
sed -i '' "s|^ORIGIN = .*|ORIGIN = \"$URL\"|" edge/wrangler.toml
(cd edge && wrangler deploy >/dev/null)
echo "snap.easychamp.com -> $URL"
