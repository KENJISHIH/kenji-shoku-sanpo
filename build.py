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
LANGS = ["zh", "ja", "en"]

SITE_NAME = {"zh": "Kenji 食散步", "ja": "Kenji 食散歩", "en": "Kenji Shoku-Sanpo"}
LANG_LABEL = {"zh": "中文", "ja": "日本語", "en": "English"}
HTML_LANG = {"zh": "zh-Hant", "ja": "ja", "en": "en"}
OG_LOCALE = {"zh": "zh_TW", "ja": "ja_JP", "en": "en_US"}

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
        "today_dishes": "我這次點的",
        "signature_dishes": "店家招牌",
        "good_for": "適合",
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
        "sep": "｜",
        "paren_open": "（",
        "paren_close": "）",
        "dot": "・",
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
        "today_dishes": "今回注文した料理",
        "signature_dishes": "店の看板メニュー",
        "good_for": "おすすめシーン",
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
        "sep": "｜",
        "paren_open": "（",
        "paren_close": "）",
        "dot": "・",
    },
    "en": {
        "site_subtitle": "A Restaurant Notebook by Kenji Shih",
        "site_intro": "Tasting notes from restaurants across Taiwan — mostly Taichung. Each entry has dish photos, shop info (address, phone, hours), tasting notes, and a rating. Filter by cuisine or rating.",
        "n_restaurants": "{n} restaurants",
        "n_photos": "{n} photos",
        "sort_label": "Sort",
        "sort_date": "Latest visit",
        "sort_rating": "★ Top rated",
        "city_label": "City",
        "all": "All",
        "cuisine_label": "Cuisine",
        "back": "← Back to all restaurants",
        "photos_count": "photos",
        "today_dishes": "What I ordered",
        "signature_dishes": "House specialties",
        "good_for": "Good for",
        "main_dishes": "Dishes",
        "menu_section": "Menu",
        "storefront_section": "Storefront & more",
        "shop_info": "Restaurant info",
        "address": "Address",
        "maps_open": "Open in Google Maps →",
        "phone": "Phone",
        "hours": "Hours",
        "closed": "Closed",
        "reservation": "Reservations",
        "service": "Service",
        "price": "Price",
        "type": "Cuisine",
        "visited": "Visited",
        "dining_record": "Dining notes",
        "dining_overall": "Overall",
        "dining_extras": "Extra notes",
        "transit": "Getting there",
        "languages": "Languages spoken",
        "foreign_menu": "Menu languages",
        "payment": "Payment",
        "dietary": "Dietary",
        "empty": "No restaurants match these filters",
        "continue_reading": "Continue reading →",
        "no_photo": "No photo",
        "rating_suffix": " / 5",
        "sep": " | ",
        "paren_open": " (",
        "paren_close": ")",
        "dot": " · ",
    },
}


# Section header aliases per language. Add ko variants when supported.
SECTION_ALIASES = {
    "overall": {"整體印象", "全体の印象", "Overall Impressions", "Overall"},
    "dishes": {"菜色清單", "料理一覧", "Dishes"},
    "extras": {"其他補充", "補足", "Extra Notes", "Additional Notes"},
}


# Top-level cuisine groups → child cuisine tags. The index filter shows groups
# instead of every child tag (avoid the "17 tags one-row" visual overload).
# Children appear under more than one group on purpose (e.g. 定食 is both
# 和食 and 洋食 friendly) so users find what they expect.
CUISINE_GROUPS = {
    "zh": {
        "中式料理": ["川菜", "中式", "合菜"],
        "西式料理": ["法式", "義式", "美式", "套餐", "預約制"],
        "日式料理": ["日式", "漢堡排", "定食"],
        "港式料理": ["港式", "茶餐廳", "冰室", "粉麵飯"],
        "韓式料理": ["韓式", "韓食", "炸雞", "拉麵"],
        "輕食/咖啡": ["早午餐", "咖啡"],
    },
    "ja": {
        "中華": ["四川料理", "中華料理"],
        "洋食": ["フレンチ", "イタリアン", "アメリカ料理", "洋食", "ハンバーグ", "コース", "完全予約制", "定食"],
        "和食": ["和食", "定食"],
        "香港": ["香港料理", "茶餐廳", "氷室", "麺類・ご飯もの"],
        "韓国料理": ["韓国料理", "韓食", "フライドチキン", "ラーメン"],
        "ブランチ/カフェ": ["ブランチ", "カフェ"],
    },
    "en": {
        "Chinese": ["Sichuan", "Chinese", "Family-style"],
        "Western": ["French", "Italian", "American", "Course menu", "Reservation only", "Diner"],
        "Japanese": ["Japanese", "Hamburg steak", "Teishoku", "Set meal"],
        "Hong Kong": ["Hong Kong", "Cha chaan teng", "Bing sutt", "Noodles & rice"],
        "Korean": ["Korean", "Fried chicken", "Ramyeon", "Rice bowl"],
        "Cafe / Light bites": ["Brunch", "Cafe", "Coffee"],
    },
}


# Per-language glossary for fields that don't go through Gemini translation
# (hours / closed / reservation / service / phone). Order matters — longer
# phrases first so they're matched before their substrings get rewritten.
GLOSSARIES = {
    "ja": [
        # good_for values (whole-string matches — longest first within this group)
        ("家庭聚餐", "ファミリー"),
        ("朋友聚餐", "友人との食事"),
        ("帶長輩", "ご年配の方と"),
        ("帶小孩", "お子様連れ"),
        ("一人吃", "一人ご飯"),
        ("商務", "ビジネス"),
        ("慶生", "誕生日祝い"),
        ("約會", "デート"),
        # service / closed / reservation phrases
        ("白飯、味噌湯無限續，無服務費", "ご飯・味噌汁おかわり自由、サービス料なし"),
        ("白飯、味噌湯無限續", "ご飯・味噌汁おかわり自由"),
        ("最長提前一個月", "最大1ヶ月前から"),
        ("最低消 NT$", "最低利用金額 NT$"),
        ("完全預約制", "完全予約制"),
        ("現場候位", "予約不可（先着順）"),
        ("單點式", "アラカルト"),
        ("可外帶", "テイクアウト可"),
        ("接受訂位", "予約可"),
        ("無服務費", "サービス料なし"),
        ("無公休", "定休日なし"),
        ("+10% 服務費", "サービス料 +10%"),
        ("週一", "月曜"),
        ("週二", "火曜"),
        ("週三", "水曜"),
        ("週四", "木曜"),
        ("週五", "金曜"),
        ("週日", "日曜"),
        ("假日", "土日祝"),
        ("(", "（"),
        (")", "）"),
        ("，", "、"),
    ],
    "en": [
        # good_for values
        ("家庭聚餐", "family gatherings"),
        ("朋友聚餐", "meals with friends"),
        ("帶長輩", "dining with elders"),
        ("帶小孩", "kid-friendly"),
        ("一人吃", "solo dining"),
        ("商務", "business meals"),
        ("慶生", "birthdays"),
        ("約會", "dates"),
        # service / closed / reservation phrases (longest first)
        ("白飯、味噌湯無限續，無服務費", "free rice & miso soup refills, no service charge"),
        ("白飯、味噌湯無限續", "free rice & miso soup refills"),
        ("假日建議先訂", "booking recommended on weekends"),
        ("最長提前一個月", "up to one month ahead"),
        ("最低消 NT$", "minimum charge NT$"),
        ("低消一份飲料", "one-drink minimum"),
        ("平日不限時", "no time limit on weekdays"),
        ("完全預約制", "reservation only"),
        ("現場候位", "walk-in only"),
        ("接受訂位", "reservations accepted"),
        ("可訂位", "reservations accepted"),
        ("有插座", "power outlets available"),
        ("單點式", "à la carte"),
        ("可外帶", "takeout available"),
        ("無服務費", "no service charge"),
        ("無公休", "open daily"),
        ("+10% 服務費", "+10% service charge"),
        ("週一", "Mondays"),
        ("週二", "Tuesdays"),
        ("週三", "Wednesdays"),
        ("週四", "Thursdays"),
        ("週五", "Fridays"),
        ("週六", "Saturdays"),
        ("週日", "Sundays"),
        ("假日", "weekends & holidays"),
        ("平日", "weekdays"),
        ("（", " ("),
        ("）", ")"),
        ("，", ", "),
        ("；", "; "),
        ("、", ", "),
        ("／", " / "),
    ],
}


def apply_glossary(text, lang: str):
    """Translate inline phrases using language glossary. No-op for zh/non-str."""
    if lang == "zh" or not isinstance(text, str):
        return text
    for zh, ja in GLOSSARIES.get(lang, []):
        text = text.replace(zh, ja)
    if lang == "en" and text:
        text = text[0].upper() + text[1:]
    return text


# Match "適合 X、Y、Z 等..." or "X、Y、Zにおすすめ..." within a description.
# Stops at sentence end (。/！/？/newline) so unrelated text after isn't pulled in.
GOOD_FOR_PATTERNS = {
    "zh": re.compile(r"適合([^。！？\n]+)"),
    "ja": re.compile(r"([^。！？\n]+?)に(?:も|は)?(?:ぴったり|最適|おすすめ)"),
    "en": re.compile(r"(?:perfect|ideal|great|good)\s+for\s+([^.!?\n(]+)", re.IGNORECASE),
}

# Phrases that look like good_for items but are actually food / side dishes /
# verb tails picked up when "...が付き、X、Yにもぴったり" sentences get parsed.
GOOD_FOR_DENY = [
    re.compile(r"[がをへ][付含入]"),  # …が付き / …が含ま / …が入って
    re.compile(r"^(?:サラダ|フライドポテト|ドリンク|ご飯|味噌汁|スープ|コーヒー|ライス|パン|デザート)$"),
]


def extract_good_for(description: str, lang: str) -> list[str]:
    """Pull occasion tags from the localized description. Returns [] if nothing
    sensible found — caller skips the tag row in that case."""
    pattern = GOOD_FOR_PATTERNS.get(lang)
    if not pattern or not description:
        return []
    m = pattern.search(description)
    if not m:
        return []
    chunk = m.group(1).strip()
    # Split on common conjunctions across zh/ja/en.
    items = re.split(r"[、，,]|\s+and\s+|\s*&\s*|や|や/|及び|以及|或者|或|和(?!菜)|與|また", chunk)
    cleaned = []
    # English items run longer than CJK ("cat lovers" vs 「愛貓人士」).
    max_len = 32 if lang == "en" else 8
    for it in items:
        it = it.strip()
        # Trim trailing "等..." (zh) or "など..." (ja) modifiers.
        it = re.sub(r"(等|など).*$", "", it).strip()
        # Skip impractically long or empty entries — they're usually noise.
        if not (2 <= len(it) <= max_len):
            continue
        # Skip food / verb-tail artifacts that aren't real occasions.
        if any(p.search(it) for p in GOOD_FOR_DENY):
            continue
        cleaned.append(it)
    return cleaned


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


def extract_city(loc: str, lang: str = "zh") -> str:
    # English locations read "Dali District, Taichung" — city is the last part.
    if lang == "en":
        return loc.split(",")[-1].strip() if loc else "Other"
    m = re.match(r"^(.*?[市縣区県])", loc or "")
    return m.group(1) if m else (loc or "其他")


def localize_album(album: dict, lang: str, translations: dict) -> dict:
    """Override album fields with translated versions for non-zh language,
    then derive auto-extracted fields (good_for) from the localized description."""
    a = dict(album)
    if lang != "zh":
        t = translations.get(album["slug"], {}).get(lang, {})
        for field in ["name", "name_alt", "location", "description"]:
            if t.get(field):
                a[field] = t[field]
        if t.get("cuisine"):
            a["cuisine"] = t["cuisine"]
    else:
        t = {}
    # Per-language address override (e.g. address_ja in restaurants.yaml).
    addr_key = f"address_{lang}"
    if a.get(addr_key):
        a["address"] = a[addr_key]
    # Per-language list-field overrides (case-by-case translations).
    for field in ["dishes", "signature_dishes", "good_for"]:
        if t.get(field):
            a[field] = t[field]
    # Per-language price range override
    price_key = f"price_range_{ {'ja': 'jpy', 'ko': 'krw', 'en': 'usd'}.get(lang, '') }"
    if a.get(price_key):
        a["price_range"] = a[price_key]
    # Glossary pass for store-info fields that don't have their own LLM translation.
    for field in ["hours", "closed", "reservation", "service"]:
        if a.get(field):
            a[field] = apply_glossary(a[field], lang)
    # Auto-extract good_for from description if not manually set. Keeps Kenji's
    # natural writing ("適合 X、Y、Z") working as a structured tag without him
    # filling a separate field per restaurant.
    if not a.get("good_for") and a.get("description"):
        a["good_for"] = extract_good_for(a["description"], lang)
    # Apply glossary to good_for list items for non-zh.
    if a.get("good_for"):
        a["good_for"] = [apply_glossary(item, lang) for item in a["good_for"]]
    # Dining record: zh uses the one already loaded from notes.md; non-zh
    # parses from translations.yaml or drops it (no MT for the structured record).
    if lang != "zh":
        if t.get("dining_record_md"):
            a["dining_record"] = parse_dining_record(t["dining_record_md"])
        else:
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
        a["city"] = extract_city(a.get("location", ""), lang)
        a["cover_photo"] = resolve_cover(a)

    # Compute cuisine groups for the index filter UI. Each card's data-cuisine
    # carries both its original tags AND matched group names, so filter logic
    # in the index template stays a simple string match.
    groups_for_lang = CUISINE_GROUPS.get(lang, {})
    for a in albums:
        raw = a.get("cuisine") or []
        matched_groups = [
            g for g, children in groups_for_lang.items()
            if any(c in children for c in raw)
        ]
        a["card_cuisines"] = list(raw) + matched_groups

    group_counter = Counter(
        g for a in albums for g in (a.get("card_cuisines") or [])
        if g in groups_for_lang
    )
    all_cuisines = [g for g, _ in group_counter.most_common()] if groups_for_lang else \
        [c for c, _ in Counter(c for a in albums for c in (a.get("cuisine") or [])).most_common()]
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

    # hreflang alternates for <head>. "lang" key kept so album pages can filter
    # out languages that particular restaurant isn't translated into yet.
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
        hreflang_alts.append({"code": HTML_LANG[other], "href": base, "lang": other})

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
        # Album pages only link to languages this restaurant actually has —
        # otherwise partially-translated languages produce 404 switcher links.
        a_langs = {l for l in LANGS if l == "zh" or has_translation(a["slug"], l, translations)}
        ctx_album = dict(
            ctx_common,
            lang_links=[ll for ll in lang_links if ll["code"] in a_langs],
            hreflang_alts=[alt for alt in hreflang_alts if alt["lang"] in a_langs],
        )
        (out_dir / f"album-{a['slug']}.html").write_text(
            album_tpl.render(album=a, **ctx_album)
        )

    rel = "dist/" if lang == "zh" else f"dist/{lang}/"
    print(f"  [{lang}] {rel}index.html + {len(albums)} album pages")


def write_sitemap(albums_raw, translations):
    """Write dist/sitemap.xml with hreflang alternates per page."""
    def has_lang(slug, lang):
        return lang == "zh" or bool(translations.get(slug, {}).get(lang, {}).get("name"))

    def url_for(lang, path=""):
        # Vercel has trailingSlash:false — non-zh root must be /ja (no slash),
        # otherwise GSC sees the sitemap loc as a 308 redirect.
        if lang == "zh":
            return f"{SITE_URL}/{path}"
        if path:
            return f"{SITE_URL}/{lang}/{path}"
        return f"{SITE_URL}/{lang}"

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
    ai_bots = ["GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "anthropic-ai",
               "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended",
               "CCBot", "Bytespider", "Amazonbot"]
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
    ]
    for bot in ai_bots:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines += [f"Sitemap: {SITE_URL}/sitemap.xml", ""]
    (DIST / "robots.txt").write_text("\n".join(lines))


def write_llms_txt(albums_raw, translations):
    """Write dist/llms.txt and dist/ja/llms.txt per llmstxt.org spec.

    LLMs.txt is a markdown file at site root that summarises the site for LLMs:
    purpose, key resources, structured data overview, language versions.
    """
    lang_names = {"zh": "繁體中文 (zh-Hant)", "ja": "日本語 (ja)", "en": "English (en)"}

    def render(lang: str) -> str:
        site = SITE_NAME[lang]
        t = I18N[lang]
        out_dir_url = SITE_URL if lang == "zh" else f"{SITE_URL}/{lang}"
        lang_list = ", ".join(lang_names[l] for l in LANGS)
        lines = [
            f"# {site}",
            "",
            f"> {t['site_intro']}",
            "",
            f"Author: Kenji Shih. Personal restaurant notebook focused on Taichung, Taiwan. "
            f"Each entry includes dish photos, shop info (address / phone / hours), "
            f"tasting notes, and a 1-5 rating. Languages: {lang_list}.",
            "",
            "## Restaurants",
            "",
        ]
        for a in albums_raw:
            if lang != "zh" and not has_translation(a["slug"], lang, translations):
                continue
            loc_a = localize_album(a, lang, translations)
            url = f"{out_dir_url}/album-{a['slug']}.html"
            desc_parts = []
            if loc_a.get("cuisine"):
                desc_parts.append("/".join(loc_a["cuisine"]) if isinstance(loc_a["cuisine"], list) else str(loc_a["cuisine"]))
            if loc_a.get("location"):
                desc_parts.append(str(loc_a["location"]))
            if loc_a.get("rating"):
                desc_parts.append(f"★{loc_a['rating']}/5")
            desc = " · ".join(desc_parts) if desc_parts else ""
            line = f"- [{loc_a['name']}]({url})"
            if desc:
                line += f": {desc}"
            if loc_a.get("description"):
                line += f" — {loc_a['description'].splitlines()[0][:160]}"
            lines.append(line)
        lines += [
            "",
            "## Language versions",
            "",
        ]
        lines += [
            f"- {lang_names[l]}: {SITE_URL}/" if l == "zh" else f"- {lang_names[l]}: {SITE_URL}/{l}"
            for l in LANGS
        ]
        lines += [
            "",
            "## Structured data",
            "",
            "- Per restaurant page: schema.org/Restaurant with PostalAddress, telephone, "
            "servesCuisine, priceRange, aggregateRating, image, sameAs (Google Maps), "
            "acceptsReservations, paymentAccepted, openingHours.",
            "- Index page: schema.org/CollectionPage with ItemList of restaurants.",
            "- Sitemap with hreflang alternates: " + f"{SITE_URL}/sitemap.xml",
            "",
            "## About the author",
            "",
            "Kenji Shih — CEO of Camao International (a Taiwan-based cosmetic OEM/ODM "
            "manufacturer) and Vice Chairperson of TCCIA (Taichung Cosmetic Industry "
            "Association). This site is a personal restaurant journal, independent from "
            "professional work.",
            "",
            "## License & usage",
            "",
            "Content (text + photos) is © Kenji Shih. AI assistants are welcome to read, "
            "summarise, and cite with attribution + link back to the source page.",
            "",
        ]
        return "\n".join(lines)

    for lang in LANGS:
        out_dir = DIST if lang == "zh" else DIST / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "llms.txt").write_text(render(lang), encoding="utf-8")


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
    write_llms_txt(albums_raw, translations)
    print(f"  ✓ dist/sitemap.xml + dist/robots.txt + dist/llms.txt ({' + '.join(LANGS)})")


if __name__ == "__main__":
    main()
