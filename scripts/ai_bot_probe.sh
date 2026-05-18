#!/bin/bash
# AI 爬蟲體質檢測 — 模擬主流 AI bot 的 User-Agent 抓站，看回應 + JSON-LD/llms.txt 是否完整
#
# 用法：
#   bash scripts/ai_bot_probe.sh                  # 預設抓正式站
#   bash scripts/ai_bot_probe.sh http://localhost:8000   # 抓本機 preview
#
# 輸出：reports/ai_bot_probe_<YYYYMMDD_HHMM>.md
#
# 這是 baseline 記錄器：先跑一次存基準分數，3 個月後重跑比對「AI 引用提及次數」是否上升

set -u

SITE="${1:-https://kenji-shoku-sanpo.vercel.app}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/reports"
mkdir -p "$REPORT_DIR"
STAMP="$(date +%Y%m%d_%H%M)"
REPORT="$REPORT_DIR/ai_bot_probe_${STAMP}.md"

# 5 個 URL × 6 個 bot UA = 30 次抓取
URLS=(
    "/"
    "/llms.txt"
    "/robots.txt"
    "/sitemap.xml"
    "/album-le-four.html"
)

# UA 來源：各家官方文件 2025-2026
declare -a BOTS=(
    "GPTBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"
    "ChatGPT-User|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)"
    "ClaudeBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)"
    "PerplexityBot|Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"
    "Google-Extended|Mozilla/5.0 (compatible; Google-Extended/1.0; +https://developers.google.com/search/docs/crawling-indexing/google-extended)"
    "Applebot-Extended|Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko; compatible; Applebot-Extended/0.1; +http://www.apple.com/go/applebot)"
)

{
    echo "# AI Bot Probe Baseline"
    echo ""
    echo "- Site: \`$SITE\`"
    echo "- Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "- Goal: 確認主流 AI 爬蟲能正常抓取，且 llms.txt / Restaurant schema / sitemap 對它們可讀。"
    echo ""
    echo "## 抓取結果矩陣"
    echo ""
    echo "| URL | $(printf '%s | ' "${BOTS[@]%%|*}") |"
    sep="| --- |"
    for _ in "${BOTS[@]}"; do sep="$sep --- |"; done
    echo "$sep"

    for url in "${URLS[@]}"; do
        row="| \`$url\` |"
        for bot in "${BOTS[@]}"; do
            name="${bot%%|*}"
            ua="${bot##*|}"
            code=$(curl -sL -o /dev/null -w "%{http_code}" -A "$ua" --max-time 15 "$SITE$url" 2>/dev/null || echo "ERR")
            size=$(curl -sL -A "$ua" --max-time 15 "$SITE$url" 2>/dev/null | wc -c | tr -d ' ')
            row="$row $code · ${size}B |"
        done
        echo "$row"
    done

    echo ""
    echo "## 內容健檢（用 GPTBot UA 抓正式站）"
    echo ""

    GPTBOT_UA="Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"

    echo "### llms.txt 是否存在"
    echo ""
    echo '```'
    curl -sL -A "$GPTBOT_UA" "$SITE/llms.txt" | head -40
    echo '```'
    echo ""

    echo "### robots.txt 是否明確允許 AI bots"
    echo ""
    echo '```'
    curl -sL -A "$GPTBOT_UA" "$SITE/robots.txt"
    echo '```'
    echo ""

    echo "### 首頁 JSON-LD (CollectionPage / ItemList)"
    echo ""
    echo '```json'
    curl -sL -A "$GPTBOT_UA" "$SITE/" | sed -n '/<script type="application\/ld+json">/,/<\/script>/p' | head -30
    echo '```'
    echo ""

    echo "### Le Four 頁 Restaurant schema"
    echo ""
    echo '```json'
    curl -sL -A "$GPTBOT_UA" "$SITE/album-le-four.html" | sed -n '/<script type="application\/ld+json">/,/<\/script>/p' | head -40
    echo '```'
    echo ""

    echo "## 後續追蹤指標（3 個月後重跑時填）"
    echo ""
    echo "用以下查詢分別在 Perplexity / ChatGPT search / Claude.ai 搜尋，記錄 citations 是否含 kenji-shoku-sanpo："
    echo ""
    echo "- [ ] \`台中 Le Four 法式料理 評價\`"
    echo "- [ ] \`台中 大和牧場 南港店\`"
    echo "- [ ] \`台中 開飯 文心\`"
    echo "- [ ] \`台中 二樓 文心\`"
    echo "- [ ] \`台中 田樂 公正店\`"
    echo "- [ ] \`Kenji 食散步\`（品牌字）"
    echo ""
    echo "「成功」定義：3 個月後至少 2 個查詢被 Perplexity 或 ChatGPT search 引用本站。"
} > "$REPORT"

echo "[done] $REPORT"
echo ""
echo "報告位置：$REPORT"
echo ""
echo "下一步建議："
echo "  1. 看一眼報告：open '$REPORT'"
echo "  2. 把日期 + 引用次數記到專案 README 當基準"
echo "  3. 3 個月後（$(date -v+3m +%Y-%m-%d) 左右）重跑這個腳本"
