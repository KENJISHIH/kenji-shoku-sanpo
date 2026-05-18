# 追蹤事項

> 食散步當 AI 友善優化實驗田的長期追蹤清單。每次重要動作後更新此檔。

## 為什麼有這個檔

食散步在 portfolio 三站（食散步 / biocamao / tccia）裡被定位為**個人沙盒**：
驗證「AI agent 時代網站該長怎樣」的理論在這裡先試，3 個月後比對引用次數，
成果若正向再套到 biocamao（公司）與 tccia（公會）。

關聯文件：
- 達文西數位拜訪會議：`~/Documents/KJ-agent/davinci-website-eval/`
- 三站對比分析：對話 2026-05-18 與 Claude 的討論

---

## 時間軸

### 2026-05-18 — AI 友善優化 v1 上線

- ✅ `build.py` 加 `write_llms_txt()`（產雙語 `dist/llms.txt`，llmstxt.org 規格）
- ✅ `robots.txt` 加 13 隻 AI bot 明確 Allow（GPTBot / ClaudeBot / PerplexityBot / Google-Extended / Applebot-Extended / ChatGPT-User / CCBot / Bytespider / Amazonbot / anthropic-ai / Claude-Web / Perplexity-User）
- ✅ `templates/album.html` Restaurant schema 補：`description` / `openingHours` / `acceptsReservations` / `paymentAccepted` / `sameAs`（Google Maps）
- ✅ 新工具 `scripts/ai_bot_probe.sh`：6 AI bot UA × 5 URL = 30 次抓取，輸出 markdown baseline
- ✅ baseline 報告：`reports/ai_bot_probe_20260518_1522.md`（線上版，部署後）
- ✅ Vercel auto-deploy 驗證可運作（push 即 deploy）

線上連結驗證：
- https://kenji-shoku-sanpo.vercel.app/llms.txt → 200 · 2695B
- https://kenji-shoku-sanpo.vercel.app/ja/llms.txt → 200 · 4124B
- https://kenji-shoku-sanpo.vercel.app/robots.txt → 200 · 491B

---

## 待追蹤（按時間排序）

### 🔵 立刻（本週內）：建立 AI 引用 baseline

用以下 6 個查詢分別到 **Perplexity / ChatGPT search / Claude.ai** 試一次，看 citations 有沒有列 kenji-shoku-sanpo.vercel.app。記到下表當基準：

| 查詢 | Perplexity | ChatGPT search | Claude.ai | 日期 |
|------|------------|----------------|-----------|------|
| 台中 Le Four 法式料理 評價 | ?/已查 | ?/已查 | ?/已查 | |
| 台中 大和牧場 南港店 | | | | |
| 台中 開飯 文心 | | | | |
| 台中 二樓 文心 | | | | |
| 新竹 天樂里冰室 | | | | |
| Kenji 食散步（品牌字） | | | | |

> 填法：`引用/未引用` + 引用到第幾條 source

### 🟡 2026-08-18（3 個月後）：重測比對

```bash
cd ~/Documents/KJ-agent/food-album-site
bash scripts/ai_bot_probe.sh     # 同樣 6 bot × 5 URL，存到 reports/
```

然後同樣 6 個查詢再跑一次，與本週 baseline 對比。**成功定義**：至少 2 個查詢在 Perplexity 或 ChatGPT search 引用本站。

### 🟢 2026-06-30 — 工研院化粧品產業演講

地點：台中集思，50–60 分鐘 multi-role 主題（執行長 × 公會副理事長 × 法規主委 × 三寶爸 × 非工程師）

**這個專案值得進演講 demo**：
- 個人專案 → 用 AI agent 把網站做到 AI agent 友善
- 對比 biocamao（公司）+ tccia（公會）三站策略
- 對比達文西外包方案的差異與互補
- 6/30 之前要先有引用次數的初步觀察（即便 8/18 才正式比對，6 月底也能看趨勢）

關聯記憶：`project_talk_itri_2026_06_30.md`

### 🟡 推到姐妹專案（決策後啟動）

如果食散步驗證有效，套到：
- **biocamao.com**（WordPress + biocamao-wp 工具）：llms.txt + robots AI Allow + Product schema（取代 Restaurant）
- **tccia.com.tw**（OpenCart）：llms.txt + robots AI Allow + Organization/EducationalOrganization + 會員 ItemList
- 同一份 `ai_bot_probe.sh` 改 URL 即可（5 行 config）

關聯記憶：
- `project_biocamao_wp.md`
- 達文西網站評估專案：`~/Documents/KJ-agent/davinci-website-eval/`

---

## 工具速查

| 動作 | 指令 |
|------|------|
| 重 build | `python build.py` |
| 跑 probe（正式站） | `bash scripts/ai_bot_probe.sh` |
| 跑 probe（本機 dist） | `python3 -m http.server 8765 --directory dist & bash scripts/ai_bot_probe.sh http://localhost:8765` |
| 部署 | `git push origin main`（auto-deploy）或 `vercel --prod` |
| 看 baseline 報告 | `open reports/ai_bot_probe_*.md` |

## 提醒

- **每加一家餐廳**：跑 build 後 llms.txt 會自動納入該餐廳一行
- **每改一次 schema**：跑 probe 對比前後 album page size 變化（schema 加大 → 內容更豐富）
- **不要刪 reports/**：每次 probe 都當歷史記錄，未來才能畫出「AI 引用次數成長曲線」
