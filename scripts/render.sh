#!/usr/bin/env bash
# Render a filled report HTML to print-ready A4 PDF + QA screenshots.
# Usage: bash render.sh report.html [output.pdf]
set -euo pipefail

HTML="${1:?usage: render.sh report.html [output.pdf]}"
PDF="${2:-report.pdf}"
BASE="$(basename "$HTML" .html)"
DIR="$(cd "$(dirname "$0")" && pwd)"

render_chrome() {  # $1 = browser binary
  "$1" --headless --disable-gpu --no-sandbox \
    --print-to-pdf="$PDF" --no-pdf-header-footer \
    "file://$(realpath "$HTML")"
  # QA contact sheet: every A4 page at 96 dpi is 794 x 1123 px
  PAGES=$(python3 - "$HTML" <<'EOF'
import re, sys
html = open(sys.argv[1], encoding="utf-8").read()
print(len(re.findall(r'<div class="runfoot">', html)) + 1)
EOF
)
  "$1" --headless --disable-gpu --no-sandbox \
    --screenshot="/tmp/${BASE}_qa.png" \
    --window-size=794,$((PAGES * 1123 + 40)) --hide-scrollbars \
    "file://$(realpath "$HTML")"
  echo "[render] PDF: $PDF"
  echo "[render] QA screenshot: /tmp/${BASE}_qa.png ($PAGES pages)"
}

for b in chromium chromium-browser google-chrome google-chrome-stable; do
  if command -v "$b" >/dev/null 2>&1; then
    render_chrome "$(command -v "$b")"
    exit 0
  fi
done

# Fallback: Playwright (macOS / no system chromium)
if command -v node >/dev/null 2>&1; then
  # locate the playwright module: local/global require, else npx cache
  PW_PATH=""
  if node -e "require.resolve('playwright')" >/dev/null 2>&1; then
    PW_PATH="keep"
  else
    for d in "$HOME"/.npm/_npx/*/node_modules "$HOME"/.hermes/node/lib/node_modules; do
      if [ -d "$d/playwright" ]; then PW_PATH="$d"; break; fi
    done
  fi
  if [ -n "$PW_PATH" ]; then
    if [ "$PW_PATH" = "keep" ]; then
      node "$DIR/render_pw.js" "$HTML" "$PDF" "/tmp/${BASE}_qa.png"
    else
      NODE_PATH="$PW_PATH" node "$DIR/render_pw.js" "$HTML" "$PDF" "/tmp/${BASE}_qa.png"
    fi
    echo "[render] PDF: $PDF"
    echo "[render] QA screenshot: /tmp/${BASE}_qa.png"
    exit 0
  fi
fi

echo "[render] ERROR: no chromium-compatible browser found (tried chromium," >&2
echo "[render]   chromium-browser, google-chrome*, and node module 'playwright')." >&2
exit 1
