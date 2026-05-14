"""Build multi-language static HTML site from data/albums.json + translations.yaml.

For each language in LANGS:
  - Localize album fields using translations.yaml
  - Render index + album pages into dist/ (zh) or dist/{lang}/ (others)
  - Add hreflang alternates between languages

Only writes / overwrites HTML files in dist/. dist/photos/ is managed by scan.py.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
DATA = ROOT / "data" / "albums.json"
CONFIG = ROOT / "restaurants.yaml"
TRANSLATIONS_FILE = ROOT / "translations.yaml"

# Production URL — change when custom domain ready. Used in sitemap.xml + robots.txt.
SITE_URL = "https://kenji-shoku-sanpo.vercel.app"

# Languages to build. zh is default (root), others go in subdirs.
LANGS = ["zh", "ja"]

SITE_NAME = {"zh": "Kenji 食散步", "ja": "Kenji 食散歩"}
LANG_LABEL = {"zh": "中文", "ja": "日本語"}
HTML_LANG = {"zh": "zh-Hant", "ja": "ja"}
OG_LOCALE = {"zh": "zh_TW", "ja": "ja_JP"}

# UI strings per language. Add 'ko' / 'en' here in future.
I18N = {
    "zh": {
        "site_subtitle": "A Restaurant Notebook by Kenji Shih",
        "site_intro": "走訪過的餐廳菜色筆記。每一篇收錄菜色照片、店舖資訊（地址・電話・營業時間）、品嚐筆記與評價。依菜系或評分快速篩選。",
        "n_restaurants": "{n} restaurants",
        "n_photos": "{n} photos",
        "sort_label": "排序",
        "sort_date": "最新造訪",
        "sort_rating": "★ 評分高",
        "city_label": "縣市",
        "all": "全部",
        "cuisine_label": "類型",
        "back": "← 回餐廳列表",
        "photos_count": "張照片",
        "today_dishes": "當天點的菜",
        "main_dishes": "本日菜色",
        "menu_section": "菜單",
        "storefront_section": "店舖外觀／相關資料",
        "shop_info": "店舖資訊",
        "address": "住所",
        "maps_open": "在 Google Maps 開啟 →",
        "phone": "電話",
        "hours": "營業時間",
        "closed": "公休",
        "reservation": "訂位",
        "service": "用餐",
        "price": "價位",
        "type": "類型",
        "visited": "造訪",
        "dining_record": "用餐紀錄",
        "dining_overall": "整體印象",
        "dining_extras": "其他補充",
        "transit": "交通",
        "languages": "店員語言",
        "foreign_menu": "外文菜單",
        "payment": "付款方式",
        "dietary": "飲食標記",
        "empty": "沒有符合條件的餐廳",
        "continue_reading": "繼續閱讀 →",
        "no_photo": "無照片",
        "rating_suffix": " / 5",
    },
    "ja": {
        "site_subtitle": "A Restaurant Notebook by Kenji Shih",
        "site_intro": "訪れた台湾レストランの食レポ。料理写真、店舗情報（住所・電話・営業時間）、感想と評価を記録。ジャンルや評価で絞り込めます。",
        "n_restaurants": "{n} 軒",
        "n_photos": "{n} 枚",
        "sort_label": "並べ替え",
        "sort_date": "最新訪問",
        "sort_rating": "★ 評価順",
        "city_label": "都市",
        "all": "すべて",
        "cuisine_label": "ジャンル",
        "back": "← 一覧へ戻る",
        "photos_count": "枚",
        "today_dishes": "注文した料理",
        "main_dishes": "本日のメニュー",
        "menu_section": "メニュー",
        "storefront_section": "店舗外観・関連資料",
        "shop_info": "店舗情報",
        "address": "住所",
        "maps_open": "Google マップで開く →",
        "phone": "電話",
        "hours": "営業時間",
        "closed": "定休日",
        "reservation": "予約",
        "service": "サービス",
        "price": "予算",
        "type": "ジャンル",
        "visited": "訪問日",
        "dining_record": "お食事の記録",
        "dining_overall": "全体の印象",
        "dining_extras": "補足",
        "transit": "アクセス",
        "languages": "対応言語",
        "foreign_menu": "外国語メニュー",
        "payment": "支払い方法",
        "dietary": "食事制限対応",
        "empty": "該当する店舗がありません",
        "continue_reading": "続きを読む →",
        "no_photo": "写真なし",
        "rating_suffix": " / 5",
    },
}


# Section header aliases per language. Add ko / en variants when supported.
SECTION_ALIASES = {
    "overall": {"整體印象", "全体の印象"},
    "dishes": {"菜色清單", "料理一覧"},
    "extras": {"其他補充", "補足"},
}


def parse_dining_record(md_text: str) -> dict | None:
    """Parse a Whisper-polished dining record markdown.

    Supports zh + ja section headers via SECTION_ALIASES.
    Returns None if no dishes parsed (format unrecognized).
    """
    if not md_text:
        return None

    # Strip YAML frontmatter
    text = md_text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end > 0:
            text = text[end + 5:]

    result = {"overall": "", "dishes": [], "extras": ""}
    # Any leading preamble (e.g. Gemini's "Here's the translation:" line) sits
    # in sections[0] and won't match any alias — silently ignored.
    sections = re.split(r"\n## ", "\n" + text)

    for sec in sections:
        header, _, body = sec.partition("\n")
        header = header.strip()
        for key, aliases in SECTION_ALIASES.items():
            if header in aliases:
                if key == "dishes":
                    result["dishes"] = _parse_dishes_section(body)
                else:
                    result[key] = body.strip()
                break

    return result if result["dishes"] else None


def _parse_dishes_section(section: str) -> list[dict]:
    """Split '### 菜名 ...' blocks → list of dicts."""
    parts = re.split(r"\n### ", "\n" + section)
    dishes = []
    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue
        raw_name = lines[0].strip()
        # Trim trailing "[菜名待確認]" / "[聽不清]" tags from display name
        name = re.sub(r"\s*\[[^\]]+\]\s*$", "", raw_name)
        dish = {"name": name, "raw_name": raw_name, "fields": {}}
        current = None
        for line in lines[1:]:
            line = line.rstrip()
            if not line:
                continue
            m = re.match(r"\s*-\s*\*\*(.+?)\*\*[:：]\s*(.*)", line)
            if m:
                current = m.group(1).strip()
                dish["fields"][current] = m.group(2).strip()
            elif current:
                # 續行(罕見,但保險起見)
                dish["fields"][current] += "\n" + line.strip()
        if dish["fields"]:
            dishes.append(dish)
    return dishes


def load_dining_record(slug: str, source_root: Path) -> dict | None:
    """Read photos/{slug}/notes.md and parse. Returns None if not present."""
    md_path = source_root / "photos" / slug / "notes.md"
    if not md_path.exists():
        return None
    return parse_dining_record(md_path.read_text(encoding="utf-8"))


def resolve_cover(album: dict) -> dict | None:
    if not album.get("photos"):
        return None
    want = (album.get("cover") or "").strip()
    if want:
        stem = want.rsplit(".", 1)[0]
        for p in album["photos"]:
            if p["filename"] == want or p["filename"].rsplit(".", 1)[0] == stem:
                return p
        print(f"  ⚠️  cover '{want}' not found in {album['slug']}")
    return album["photos"][0]


def extract_city(loc: str) -> str:
    m = re.match(r"^(.*?[市縣区県])", loc or "")
    return m.group(1) if m else (loc or "其他")


def localize_album(album: dict, lang: str, translations: dict) -> dict:
    """Override album fields with translated versions for non-zh language."""
    if lang == "zh":
        return album
    a = dict(album)
    t = translations.get(album["slug"], {}).get(lang, {})
    for field in ["name", "name_alt", "location", "description"]:
        if t.get(field):
            a[field] = t[field]
    if t.get("cuisine"):
        a["cuisine"] = t["cuisine"]
    # Per-language price range override
    price_key = f"price_range_{ {'ja': 'jpy', 'ko': 'krw', 'en': 'usd'}.get(lang, '') }"
    if a.get(price_key):
        a["price_range"] = a[price_key]
    # Dining record: each language has its own parsed MD
    if t.get("dining_record_md"):
        a["dining_record"] = parse_dining_record(t["dining_record_md"])
    else:
        # No translation available — keep dining_record only on zh
        a["dining_record"] = None
    return a


def has_translation(slug: str, lang: str, translations: dict) -> bool:
    return bool(translations.get(slug, {}).get(lang, {}).get("name"))


def render_site(lang: str, albums_raw: list[dict], translations: dict, env: Environment):
    """Render one language's site."""
    # Filter & localize
    if lang == "zh":
        albums = list(albums_raw)
    else:
        albums = [a for a in albums_raw if has_translation(a["slug"], lang, translations)]
    albums = [localize_album(a, lang, translations) for a in albums]

    if not albums:
        print(f"  [{lang}] no translations available — skipping")
        return

    for a in albums:
        a["city"] = extract_city(a.get("location", ""))
        a["cover_photo"] = resolve_cover(a)

    cuisine_counter = Counter(c for a in albums for c in (a.get("cuisine") or []))
    all_cuisines = [c for c, _ in cuisine_counter.most_common()]
    city_counter = Counter(a["city"] for a in albums if a["city"])
    cities = city_counter.most_common()

    # Output paths
    if lang == "zh":
        out_dir = DIST
        photo_prefix = ""
    else:
        out_dir = DIST / lang
        photo_prefix = "../"

    out_dir.mkdir(exist_ok=True, parents=True)
    for f in out_dir.glob("*.html"):
        f.unlink()

    # Language switcher links (relative to current lang page)
    # If current=zh, ja link is "ja/", others reverse
    lang_links = []
    for other in LANGS:
        if other == lang:
            continue
        # Only show link if there's any content in that lang
        has_content = any(has_translation(a["slug"], other, translations) for a in albums_raw) if other != "zh" else True
        if not has_content:
            continue
        if lang == "zh" and other != "zh":
            href = f"{other}/"
        elif lang != "zh" and other == "zh":
            href = "../"
        else:
            href = f"../{other}/"
        lang_links.append({"code": other, "label": LANG_LABEL[other], "href": href})

    # hreflang alternates for <head>
    hreflang_alts = []
    for other in LANGS:
        if other == lang:
            continue
        if other == "zh":
            base = "../"
        elif lang == "zh":
            base = f"{other}/"
        else:
            base = f"../{other}/"
        hreflang_alts.append({"code": HTML_LANG[other], "href": base})

    t = I18N[lang]
    site_name = SITE_NAME[lang]

    ctx_common = {
        "t": t,
        "lang": lang,
        "html_lang": HTML_LANG[lang],
        "og_locale": OG_LOCALE[lang],
        "site_name": site_name,
        "site_subtitle": t["site_subtitle"],
        "photo_prefix": photo_prefix,
        "lang_links": lang_links,
        "hreflang_alts": hreflang_alts,
    }

    index_tpl = env.get_template("index.html")
    album_tpl = env.get_template("album.html")

    (out_dir / "index.html").write_text(
        index_tpl.render(
            albums=albums,
            all_cuisines=all_cuisines,
            cities=cities,
            **ctx_common,
        )
    )
    for a in albums:
        (out_dir / f"album-{a['slug']}.html").write_text(
            album_tpl.render(album=a, **ctx_common)
        )

    rel = "dist/" if lang == "zh" else f"dist/{lang}/"
    print(f"  [{lang}] {rel}index.html + {len(albums)} album pages")


def write_sitemap(albums_raw, translations):
    """Write dist/sitemap.xml with hreflang alternates per page."""
    def has_lang(slug, lang):
        return lang == "zh" or bool(translations.get(slug, {}).get(lang, {}).get("name"))

    def url_for(lang, path=""):
        prefix = "" if lang == "zh" else f"{lang}/"
        return f"{SITE_URL}/{prefix}{path}"

    # (slug=None means index page); pages added in canonical order
    pages = [(None, "")]
    for a in albums_raw:
        pages.append((a["slug"], f"album-{a['slug']}.html"))

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for slug, path in pages:
        for lang in LANGS:
            if slug is not None and not has_lang(slug, lang):
                continue
            lines.append(f"  <url><loc>{url_for(lang, path)}</loc>")
            for alt in LANGS:
                if slug is not None and not has_lang(slug, alt):
                    continue
                lines.append(
                    f'    <xhtml:link rel="alternate" hreflang="{HTML_LANG[alt]}" '
                    f'href="{url_for(alt, path)}"/>'
                )
            lines.append("  </url>")
    lines.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(lines))


def write_robots():
    content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    (DIST / "robots.txt").write_text(content)


def main():
    if not DATA.exists():
        raise SystemExit("ERROR: data/albums.json not found — run `python scan.py` first")

    albums_raw = json.loads(DATA.read_text())

    # Overlay latest metadata from restaurants.yaml
    cfg = yaml.safe_load(CONFIG.read_text())
    yaml_by_slug = {r["slug"]: r for r in cfg["restaurants"]}
    for a in albums_raw:
        if a["slug"] in yaml_by_slug:
            for k, v in yaml_by_slug[a["slug"]].items():
                a[k] = v

    # Load dining records (Chinese SSOT from photos/{slug}/notes.md)
    for a in albums_raw:
        a["dining_record"] = load_dining_record(a["slug"], ROOT)

    # Load translations
    translations = {}
    if TRANSLATIONS_FILE.exists():
        translations = yaml.safe_load(TRANSLATIONS_FILE.read_text()) or {}

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    DIST.mkdir(exist_ok=True)

    for lang in LANGS:
        render_site(lang, albums_raw, translations, env)

    write_sitemap(albums_raw, translations)
    write_robots()
    print(f"  ✓ dist/sitemap.xml + dist/robots.txt")


if __name__ == "__main__":
    main()
