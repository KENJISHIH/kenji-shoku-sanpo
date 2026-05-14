# 部署與監測指引

## 線上 URL

- **正式站**：https://kenji-shoku-sanpo.vercel.app
- **日文版**：https://kenji-shoku-sanpo.vercel.app/ja/
- **sitemap**：https://kenji-shoku-sanpo.vercel.app/sitemap.xml
- **robots.txt**：https://kenji-shoku-sanpo.vercel.app/robots.txt

GitHub repo：https://github.com/KENJISHIH/kenji-shoku-sanpo （Public）
Vercel project：`kenjishihs-projects/kenji-shoku-sanpo`

## Auto-deploy 已開啟

Vercel 已連 GitHub repo。**`git push origin main` 自動觸發 production deploy**，1-2 分鐘上線。

日常修改流程：

```bash
cd ~/Documents/KJ-agent/food-album-site

# 改完 yaml / template / notes.md 後
python scan.py && python build.py   # 或只 python build.py（如沒新照片）
git add . && git commit -m "新增餐廳：XXX"
git push origin main                # ← 自動 deploy
```

## Google Search Console 註冊（你親手 5 分鐘）

我做不到（要你 Google 帳號驗證），照這 5 步做：

### 1. 開 Search Console
https://search.google.com/search-console

用你 `kenjishih@gmail.com` 登入。

### 2. 新增資源
左上「+ 新增資源」→ 選「**網址前置字串**」（不是「網域」，網域要 DNS 驗證較麻煩）
貼上：`https://kenji-shoku-sanpo.vercel.app`

### 3. 驗證擁有權
推薦選「**HTML 標記**」驗證（最簡單）：
- Google 給你一段 `<meta name="google-site-verification" content="XXXX">` 標籤
- **複製整段** 給我（下次對話貼給我，我加進 `templates/index.html` 的 `<head>`）
- push → 自動 deploy → 回 Search Console 按「驗證」

或更快：選「**Google Analytics**」驗證（如果你已裝 GA）。

### 4. 提交 Sitemap
驗證成功後，左側選「Sitemap」→ 貼上 `sitemap.xml` → 提交。

### 5. 等資料
- **1-3 天**：Google 開始抓取
- **1-2 週**：第一批頁面進索引
- **4-8 週**：開始有實質「曝光次數」資料

之後每週/每月看「成效」分頁，重點看：
- **曝光次數**（impressions）：你的頁面在搜尋結果出現幾次
- **點擊率**（CTR）：曝光中被點的比例
- **平均排名**：關鍵字平均落在第幾名
- **熱門查詢**：哪些關鍵字找到你（決定後續加哪些內容）

## 加 custom domain（之後想做再做）

如果要換成 `kenji.tw` 或 `shoku-sanpo.com` 等自己網域：

```bash
# 1. 買網域（Cloudflare Registrar / Namecheap 等）
# 2. Vercel 加 domain
vercel domains add YOUR-DOMAIN.com
# 3. 在註冊商 DNS 設定 CNAME 指向 cname.vercel-dns.com
# 4. 改 build.py 內 SITE_URL = "https://YOUR-DOMAIN.com"
# 5. rebuild + push
```

換 domain 後 Google Search Console 要重新註冊新 domain（舊資料不會搬）。所以 custom domain 越早決定越好（避免 SEO 累積浪費）。

## 重要 reminders

1. **`SITE_URL` 在 `build.py` 頂部**（line 22 附近），改 domain 時記得改
2. **`photos/` 不入 repo**，原圖留本機 + iCloud
3. **`dist/` 整個入 repo**，Vercel 從這 serve
4. **`_private/` 永遠不會被 build**，安全閥
5. **`translations.yaml` 入 repo**，這樣換機器也能繼續開發
