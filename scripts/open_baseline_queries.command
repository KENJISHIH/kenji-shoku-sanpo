#!/bin/bash
# 一鍵開 baseline 查詢頁面（6 查詢 × 3 平台 = 18 個 URL）
# 用法：在 Finder 雙擊本檔（已 chmod +x）
#
# 開啟順序：每個查詢開 3 個分頁（Perplexity、ChatGPT search、Claude.ai）
# 看完後手動填 TRACKING.md 的表格

set -u

# 6 查詢（與 TRACKING.md 表格一致）
QUERIES=(
    "台中 Le Four 法式料理 評價"
    "台中 大和牧場 南港店"
    "台中 開飯 文心"
    "台中 二樓 文心"
    "新竹 天樂里冰室"
    "Kenji 食散步"
)

echo "=== Baseline AI 引用查詢（2026-05-18）==="
echo ""
echo "每個查詢會在 3 個平台各開一個分頁。看完後："
echo "  - 在 TRACKING.md 表格填：引用/未引用 + 引用到第幾條 source"
echo "  - 如有引用，貼一張 screenshot 到 reports/baseline_2026-05-18_screenshots/"
echo ""
echo "請保持瀏覽器登入 ChatGPT、Claude.ai（沒登入會卡在 login wall）"
echo ""
read -p "按 Enter 開始開分頁..." _

mkdir -p ~/Documents/KJ-agent/food-album-site/reports/baseline_2026-05-18_screenshots

for q in "${QUERIES[@]}"; do
    # URL encode（簡單版）
    encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$q'))")
    echo ""
    echo "→ 查詢：$q"
    # Perplexity
    open -a "Microsoft Edge" "https://www.perplexity.ai/search?q=$encoded"
    sleep 0.5
    # ChatGPT
    open -a "Microsoft Edge" "https://chatgpt.com/?q=$encoded&hints=search"
    sleep 0.5
    # Claude.ai（沒有公開 search URL，開首頁讓你貼）
    open -a "Microsoft Edge" "https://claude.ai/new?q=$encoded"
    sleep 1
done

echo ""
echo "=== 全部 18 個分頁已開 ==="
echo ""
echo "下一步："
echo "  1. 在每個分頁看 sources，記是否引用 kenji-shoku-sanpo.vercel.app"
echo "  2. 填 ~/Documents/KJ-agent/food-album-site/TRACKING.md 的表格"
echo "  3. （可選）截圖存 reports/baseline_2026-05-18_screenshots/"
echo "  4. 表格填完後 git commit + push 當 baseline"
echo ""
echo "按任意鍵關閉本視窗..."
read -n 1
