# food-album-site

Kenji 的餐廳菜色紀錄站。**本機資料夾 → 自動壓縮 → 靜態 HTML → Vercel/Pages 部署**。

Flickr 那邊完全不參與展示（理由：Flickr 權限是照片層級，無法在「同一張照片」上做雙重 privacy；繼續當 Private 備份就好）。

## 概念

- **本機 `photos/{slug}/`** = 原圖（HEIC/JPG，從 iPhone/iCloud 來），**不入 repo**
- **`restaurants.yaml`** = SSOT，列每家店的 slug + 店名 + 地點 + 日期 + 評分 + 心得
- **`scan.py`** = 掃 `photos/` → 壓縮成 1600px 大圖 + 400px 縮圖 → 輸出到 `dist/photos/{slug}/` + `data/albums.json`
- **`build.py`** = 套 Jinja2 模板 → 寫 `dist/index.html` 和 `dist/album-{slug}.html`
- **`dist/`** = 整個拿去部署（包含壓縮後照片）

## 一次性安裝

```bash
cd ~/Documents/KJ-agent/food-album-site
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 日常流程

每次去新餐廳：

1. **照片拉到本機**
   - iPhone → AirDrop / iCloud Photos.app → 從中挑要展示的
   - 丟到 `photos/{slug}/`（slug 自己取，例如 `le-four`、`din-tai-fung-taichung`）
   - HEIC、JPG、PNG 都吃

2. **登錄 metadata**

   編輯 `restaurants.yaml`：
   ```yaml
   - slug: le-four
     name: "Le Four 萊法小館"
     location: "台中市"
     visited_at: "2026-05-12"
     rating: 4.5
     note: "母親節帶哈妮來"
   ```

3. **跑兩行**

   ```bash
   python scan.py    # 壓縮 + 寫 albums.json（增量，重跑不會重壓已壓過的）
   python build.py   # 生成 HTML
   ```

4. **本機預覽**

   ```bash
   open dist/index.html
   ```

5. **部署**

   首次：
   ```bash
   cd dist
   vercel        # 跟著問答走，選 link 到一個新 project
   vercel --prod
   ```

   之後改了就 `vercel --prod`。或 push 到 GitHub 後設定 Vercel auto-deploy（你已經有經驗）。

## 為什麼 `photos/` 進 `.gitignore`、`dist/photos/` 卻入 repo？

- `photos/` 是原圖（每張 5–10 MB HEIC），不該 push 到 GitHub（會撐爆 repo）
- `dist/photos/` 是壓縮後的副本（每張 ~300 KB JPG），Vercel deploy 需要這份檔
- 概念：iCloud 存原檔，repo 存「沖印過的展示版」

## 原圖會不會丟失？

- **原圖**留在 iCloud Photos.app / iPhone（永久備份）
- **本機 `photos/` 資料夾**是 working copy，刪了不影響網站
- **`dist/photos/`** 是 commit 進 GitHub 的展示版，網站靠這份

只要 iCloud 跟 GitHub repo 任一個還在，照片就沒丟。

## 檔案結構

```
food-album-site/
├── photos/             # 原圖（HEIC/JPG）— gitignored
│   └── le-four/
│       ├── IMG_001.heic          # 主菜色（進主 grid 公開）
│       ├── IMG_002.jpg
│       ├── _menu/                # 菜單照（進「菜單」section 公開）
│       ├── _docs/                # 店面外觀 / 店家 PDF（進「店舖外觀」section 公開）
│       ├── _private/             # 收據 / 訂位單（本機保留，永不公開）
│       └── notes.md              # 用餐紀錄（Whisper polished MD，進「用餐紀錄」section 公開）
├── dist/               # 部署目標 — 整個 commit 進 repo
│   ├── photos/
│   │   └── le-four/
│   │       ├── IMG_001.jpg     # 1600px
│   │       └── thumb/
│   │           └── IMG_001.jpg # 400px
│   ├── index.html
│   └── album-le-four.html
├── data/albums.json    # scan.py 產出 — gitignored
├── restaurants.yaml    # SSOT
├── scan.py
├── build.py
└── templates/
    ├── index.html
    └── album.html
```

## 增量更新（不會重壓所有照片）

`scan.py` 會比對源檔 mtime 跟 `dist/photos/` 的 mtime，沒改的跳過。所以加 1 張新照片只壓 1 張，不會把整本相簿重做。

## 用餐紀錄（notes.md）整合

在每家餐廳有錄音 → Whisper polished MD 的場景下，把 MD 複製到 `photos/{slug}/notes.md` 就會自動接到頁面：

```bash
# 從 Whisper output cp 過來
cp ~/Documents/KJ-agent/Whisper/output/polished/2026-05-12_Le_Four_用餐紀錄__gemini.md \
   photos/le-four/notes.md

# 翻譯日文版（一次 Gemini 呼叫翻整段 MD）
python generate-ja.py    # 增量，只翻新增的

# rebuild
python build.py
```

### notes.md 結構約定（Whisper polished 標準格式）

```markdown
---
title: ...
date: 2026-05-12
---

## 整體印象
<段落>

## 菜色清單
### 菜名 [optional 標註]
- **食材**：...
- **做法**：...
- **老闆說的點**：...
- **建議吃法**：...

(每道菜重複)

## 其他補充
- <bullet>
```

`build.py` 用 regex 解析這個格式 → 「用餐紀錄」section。有 notes.md 時隱藏 yaml `dishes` pill（避免重複），沒 notes.md 時 fallback 顯示 dishes。
