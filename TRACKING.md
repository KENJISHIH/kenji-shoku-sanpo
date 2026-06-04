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

### 2026-05-22 — GSC baseline + sitemap 重提

#### 索引狀態（產生索引 → 網頁）

- **已索引：3 / 12（25%）**
- 已收：`/` (5/15) · `/album-le-four.html` (5/16) · `/ja` (5/17)
- 未收 9 頁：4 家餐廳中文版 + 4 家餐廳日文版 + `/ja/album-le-four.html`

#### Sitemap 重提

- 5/16 首次提交狀態「無法擷取」（提交時點可能還沒部署完整）
- 5/22 重提 → **狀態：成功，系統探索到 12 頁** ✅
- 驗證 Googlebot UA `curl` 抓 sitemap.xml = HTTP 200 / 4015 B / 0.2s（網路層無阻擋）

#### 28 天搜尋成效 baseline（過去 3 個月 ≈ 站上線全期）

| 指標 | 值 |
|------|----|
| 總點擊 | 1 |
| 曝光總數 | 9 |
| 平均 CTR | 11.1% |
| 平均排名 | 9.7 |

熱門查詢前 3：

| 查詢 | 點擊 | 曝光 | 備註 |
|------|------|------|------|
| `le four 萊 法 小館` | 0 | 2 | 中英混搜 |
| `萊法小館` | 0 | 1 | ⚠️ **中譯名訊號** — 站內 le-four 頁沒寫「萊法小館」，使用者搜得到卻看不到對應內容 → 點擊掛 0 |
| `site:vercel.app` | 0 | 1 | 雜訊 |

#### 觀察與下一步

- **「萊法小館」中譯名訊號**：有人在 Google 搜中譯名找到本站，但 le-four 頁完全沒寫這 4 個字 → 考慮在 albums.yaml 補 alias 欄位或 H2 補一行（既不破壞品牌也讓搜尋對得上）
- **9 頁未索引**：今日已用 GSC 網址審查逐個「要求建立索引」（中文 4 頁優先，日文 5 頁次日做）
- 8/18 重測時，預期：索引 12/12、查詢覆蓋更多餐廳關鍵字、Perplexity / Claude 來源命中數 > 1

### 2026-06-03 — 🎉 餐廳主人主動回傳貼到自家 IG（首個外部有機提及）

- **事件**：Le Four 萊法小館（@le_four_restaurant）店家主動把食散步的 `/album-le-four.html` 文章貼到自家 **IG / FB / Threads**，IG 貼文 https://www.instagram.com/p/DZFTRcHCSQ6/（已編輯，發布 6/2 晚間）
- 貼文 caption 含 **明文連結 https://kenji-shoku-sanpo.vercel.app**（「Kenji 食散步 部落格」字樣 + 🔗）→ 站外有機提及 +1
- 互動脈絡：店家「太完美了 😍」並主動問可否分享；同為父母聊小孩教育話匣子打開，店家允諾下次帶寶寶來用餐
- **對追蹤的意義**：
  - 內容品質好到**被報導對象本人**願意主動擴散，驗證 portfolio 沙盒策略（先在食散步試、成果正向再套 biocamao / tccia）
  - IG 連結雖 nofollow，但屬社群發現訊號 + 潛在 AI 爬取來源；8/18 重測 AI 引用時可留意是否因此被帶到
- **可做的具體強化（待 Kenji 決定）**：
  - le-four 頁 Restaurant schema `sameAs` 目前只放 Google Maps → 可補店家 IG profile `https://www.instagram.com/le_four_restaurant/`，讓 AI 把「文章 ↔ 店家官方帳號」綁在同一實體（外科式小改，需 rebuild + redeploy）
  - 呼應 5/22「萊法小館中譯名訊號」：店家既然認這篇，le-four 頁補一行中譯名「萊法小館」alias 更站得住腳

---

## 待追蹤（按時間排序）

### 🔵 立刻（本週內）：建立 AI 引用 baseline

用以下 6 個查詢分別到 **Perplexity / ChatGPT search / Claude.ai** 試一次，看 citations 有沒有列 kenji-shoku-sanpo.vercel.app。

**一鍵打開 18 個分頁**（用 Edge 開，已登入 ChatGPT / Claude.ai）：

```bash
bash ~/Documents/KJ-agent/food-album-site/scripts/open_baseline_queries.command
```

#### 我要看什麼？

每個分頁的核心是「**這個 AI 回答的時候，有沒有把 kenji-shoku-sanpo.vercel.app 列為來源？**」

各家「來源」長的樣子不一樣：

| 平台 | 來源在哪 | 看什麼 |
|------|---------|--------|
| **Perplexity** | 答案上方有「Sources」橫條（小卡片），每張卡片有 domain（如 `tripadvisor.com`、`google.com`）| 卡片裡有沒有 `kenji-shoku-sanpo.vercel.app` |
| **ChatGPT search** | 答案中段一句話後面會有 🔗 角標，hover 顯示來源網址；底部「Sources」section | 列表中有沒有 `kenji-shoku-sanpo.vercel.app` |
| **Claude.ai**（web search 開啟時）| 答案中段或最後會列「Sources」連結 | 同上 |

⚠️ **沒登入會卡 login wall** — ChatGPT 和 Claude.ai 用 Edge 開時要確認上面顯示你的頭像/帳號

#### 怎麼填表？

只用 3 種符號，**不用寫長句**：

- `✅ #N` = 有引用，排第 N 條 source（例：`✅ #3` 表示排第 3 條）
- `❌` = 完全沒引用本站
- `—` = AI 沒給 source（純自由發揮，沒網路搜尋）／或這查詢平台跳 login wall

#### 範例（假資料，幫你看格式）

| 查詢 | Perplexity | ChatGPT search | Claude.ai | 截圖檔名 |
|------|------------|----------------|-----------|---------|
| Kenji 食散步（品牌字） | ✅ #1 | ✅ #2 | ✅ #1 | `brand_2026-05-18.png` |
| 台中 Le Four 法式料理 評價 | ❌ | ❌ | ❌ | — |
| 新竹 天樂里冰室 | ✅ #5 | ❌ | — | `tianle_perplexity.png` |

→ 解讀：品牌字 3 家都有引用（很好），餐廳關鍵字幾乎沒引用（**這就是 baseline，3 個月後重測比改善幅度**）

#### 截圖（可選但強烈建議）

任何一格出現 `✅` 都截圖存到 `reports/baseline_2026-05-18_screenshots/`：
- Mac 截圖：`Cmd+Shift+4` 框選 → 桌面 → 拖到 screenshots 資料夾
- 命名：`<查詢關鍵字>_<平台>.png`（例：`brand_perplexity.png`、`tianle_chatgpt.png`）

3 個月後做對比時，這些截圖是「以前是這樣→現在變這樣」的鐵證。

#### 2026-05-18 Baseline（已測）

填法：`✅ #N` 表示有引用且排第 N 條 source ／ `❌` 未引用 ／ `—` 平台沒回 sources

| 查詢 | Perplexity | ChatGPT search | Claude.ai | 截圖檔名 |
|------|------------|----------------|-----------|---------|
| 台中 Le Four 法式料理 評價 | ❌ | — | ❌ | |
| 台中 大和牧場 南港店 | ❌ | — | ❌ | |
| 台中 開飯 文心 | ❌ | — | ❌ | |
| 台中 二樓 文心 | ❌ | — | ❌ | |
| 新竹 天樂里冰室 | ❌ | — | ❌ | |
| Kenji 食散步（品牌字） | ✅（8 來源內，inline pill）| — | ❌ | `brand_perplexity_2026-05-18.png`（待補）|

**Baseline 重點解讀**：
- 唯一命中：Perplexity 搜「Kenji 食散步」品牌字 → 答案內 inline 顯示 `kenji-shoku-sanpo.vercel` pill，底部 8 個來源（精確排名未細看）
- 5 個餐廳關鍵字在 Perplexity / Claude 全 ❌（**這正是 baseline 起點**）
- ChatGPT search 全 `—`：`?q=` 參數沒觸發 web search，GPT 用內建知識回答（不準，下次手動點 Search icon 重測）

**這份 baseline 的意義**：3 個月後（2026-08-18）重測，只要 6 個查詢中**任一個**從 ❌→✅，就證明 AI 友善 v1（llms.txt / robots / Restaurant schema 強化）有效。

#### ChatGPT search 補測（可選，本週內）

`?q=` 不會觸發網路搜尋。要正確 baseline 必須：
1. 開 https://chatgpt.com/
2. 在輸入框**先點地球 icon「Search the web」**
3. 再貼查詢字串
4. 看回答底部是否有 Sources 區

如果這 6 個 ChatGPT search 都還是 ❌，跟其他平台一致就 OK。先這樣留 `—` 也不影響 8/18 比對（重測時走同樣方式即可）。

截圖存放：`reports/baseline_2026-05-18_screenshots/`（建好了，雙擊執行檔會自動 mkdir）

#### 代理指標：Google 索引基準（同時記）

- [x] 用 `site:kenji-shoku-sanpo.vercel.app` 在 Google 查目前索引筆數（理想 ≥ 6 頁：1 index + 5 album + 雙語版 = 12）→ **2026-05-22 GSC 實測：3/12（25%）**
- [x] 用 GSC（Search Console）抓「最近 28 天熱門查詢」前 10 名 → **2026-05-22 baseline 見下方時間軸**
- [x] 兩筆都填到下方 → 見「2026-05-22 — GSC baseline + sitemap 重提」

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
