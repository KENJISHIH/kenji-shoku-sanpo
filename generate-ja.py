"""Translate restaurants.yaml fields to a target language via Gemini CLI.

Usage:
    python generate-ja.py                # translate to Japanese (default)
    python generate-ja.py --lang ja      # explicit
    python generate-ja.py --force        # re-translate even if cached

Output: translations.yaml — keyed by slug → lang → field.
Incremental: skips already-translated entries unless --force.

Future: add 'ko' / 'en' prompts to PROMPTS dict to support Korean / English.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
RESTAURANTS = ROOT / "restaurants.yaml"
TRANSLATIONS = ROOT / "translations.yaml"
WORKSPACE = ROOT.parent  # Gemini CLI must run inside KJ-agent workspace

# Prompts per language. Each field has its own prompt for tone control.
PROMPTS = {
    "ja": {
        "name": '請將以下餐廳名稱翻譯為日文(用日本人習慣的寫法)。若名稱本身已含官方英文/外文品牌名(拉丁字母),以該品牌名為主、可加片假名音;純中文漢字部分保留原字即可,**不要為它硬編一個中文漢字的音讀假名(例如不要把「橘子堂」標成「きつしどう」)**:「{value}」。只回答譯名,不要解釋。',
        "name_alt": '請將以下餐廳副標題翻譯為自然日語:「{value}」。只回答譯名,不要解釋。',
        "location": '請將台灣地名「{value}」翻譯為日文常用寫法(例如「台中市南屯區」→「台中市南屯区」)。只回答譯名。',
        "cuisine": '請將以下料理類型翻譯為日文(用日本食記/食べログ常見詞):「{value}」。多個用「、」分隔,直接列出譯名,不要解釋。',
        "dishes": '請將以下台灣餐廳的菜色名稱逐一翻譯為日文(用日本人習慣的料理名寫法,括號內的補充說明一併翻譯;保持項目數量與順序一致):「{value}」。多個用「、」分隔,直接列出譯名,不要加編號或解釋。',
        "signature_dishes": '請將以下台灣餐廳的招牌菜名稱逐一翻譯為日文(用日本人習慣的料理名寫法,括號內補充一併翻譯;保持項目數量與順序一致):「{value}」。多個用「、」分隔,直接列出譯名,不要加編號或解釋。',
        "description": '''請將以下台灣餐廳簡介翻譯為自然流暢的日文,符合食べログ等日本食記網站的語氣。
重要:
- 保留段落結構與換行
- 用「ですます」體
- 直接輸出譯文,不要加標題、引言或解說
- 漢字使用日本當用漢字

原文:
{value}''',
        "dining_record_md": '''請將以下台灣餐廳的用餐紀錄翻譯為自然流暢的日文,符合食べログ食記語氣。

嚴格保留以下 markdown 結構不變:
- 「## 整體印象」翻成「## 全体の印象」
- 「## 菜色清單」翻成「## 料理一覧」
- 「## 其他補充」翻成「## 補足」
- 每道菜的「### 菜名」結構保留;菜名翻成日本人習慣的寫法
- 「- **食材**：」「- **做法**：」「- **老闆說的點**：」「- **建議吃法**：」這類欄位
  分別翻成「- **食材**：」「- **調理法**：」「- **シェフのコメント**：」「- **おすすめの食べ方**：」
- 整段用「ですます」體
- 「[菜名待確認]」「[聽不清]」等標註保留並翻成「[料理名要確認]」「[聞き取れず]」
- 直接輸出譯後 markdown,不要加引言或解說

原文:
{value}''',
    },
    "en": {
        "name": '請將以下餐廳名稱翻譯為英文(用歐美食記/Google Maps 常見的寫法)。**若店名本身已含官方英文品牌名(拉丁字母),就直接只用那個英文名,不要另加中文拼音或音譯(例如「Orange Square 橘子堂」→「Orange Square」,不要變成「Orange Square (Ju Zi Tang)」)**;只有在完全沒有官方英文名時才音譯:「{value}」。只回答譯名,不要解釋。',
        "name_alt": '請將以下餐廳副標題翻譯為自然英文:「{value}」。只回答譯名,不要解釋。',
        "location": '請將台灣地名「{value}」翻譯為英文常用寫法,格式「District, City」(例如「台中市南屯區」→「Nantun District, Taichung」)。只回答譯名。',
        "cuisine": '請將以下料理類型翻譯為英文標籤(用歐美食記常見詞,每個標籤 1-2 個單字,首字母大寫):「{value}」。多個用「、」分隔,直接列出譯名,不要解釋。',
        "dishes": '請將以下台灣餐廳的菜色名稱逐一翻譯為英文(用歐美菜單常見寫法,括號內補充一併翻譯,必要時於括號附原文拼音;保持項目數量與順序一致):「{value}」。多個用「、」分隔,直接列出譯名,不要加編號或解釋。',
        "signature_dishes": '請將以下台灣餐廳的招牌菜名稱逐一翻譯為英文(用歐美菜單常見寫法,括號內補充一併翻譯,必要時附原文拼音;保持項目數量與順序一致):「{value}」。多個用「、」分隔,直接列出譯名,不要加編號或解釋。',
        "description": '''請將以下台灣餐廳簡介翻譯為自然流暢的英文,語氣像歐美旅遊美食部落格,寫給來台灣旅遊的外國讀者。
重要:
- 保留段落結構與換行
- 自然口語化(conversational),避免「The restaurant is located at...」這類機械句式
- 台灣特有詞彙第一次出現時可附簡短說明
- 若原文最後有「適合 X、Y、Z」的句子,翻成以「Perfect for」開頭的句子(例如 "Perfect for cat lovers, laptop work, and casual get-togethers.")
- 直接輸出譯文,不要加標題、引言或解說

原文:
{value}''',
        "dining_record_md": '''請將以下台灣餐廳的用餐紀錄翻譯為自然流暢的英文,語氣像歐美美食部落格。

嚴格保留以下 markdown 結構不變:
- 「## 整體印象」翻成「## Overall Impressions」
- 「## 菜色清單」翻成「## Dishes」
- 「## 其他補充」翻成「## Extra Notes」
- 每道菜的「### 菜名」結構保留;菜名翻成英文(必要時附原文)
- 「- **食材**：」「- **做法**：」「- **老闆說的點**：」「- **建議吃法**：」這類欄位
  分別翻成「- **Ingredients**:」「- **Preparation**:」「- **Chef's notes**:」「- **How to enjoy**:」
- 「[菜名待確認]」「[聽不清]」等標註翻成「[dish name TBC]」「[inaudible]」
- 直接輸出譯後 markdown,不要加引言或解說

原文:
{value}''',
    },
}

LANG_LABEL = {"ja": "日本語", "ko": "한국어", "en": "English"}


def gemini(prompt: str) -> str:
    """Call gemini CLI; strip auth banner, return clean text."""
    result = subprocess.run(
        ["gemini", "-p", prompt, "-o", "text"],
        capture_output=True,
        text=True,
        cwd=WORKSPACE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Gemini failed: {result.stderr}")
    lines = [
        line for line in result.stdout.splitlines()
        if "Loaded cached credentials" not in line
    ]
    return "\n".join(lines).strip()


def translate_field(value, prompt_template: str, field: str):
    """Translate a single field. Handles list-type fields (cuisine)."""
    if isinstance(value, list):
        value_str = "、".join(value)
    else:
        value_str = str(value)
    result = gemini(prompt_template.format(value=value_str))
    if isinstance(value, list):
        return [c.strip() for c in result.split("、") if c.strip()]
    return result


def parse_args():
    lang = "ja"
    force = False
    only_slug = None
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lang" and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
            i += 2
        elif arg == "--slug" and i + 1 < len(sys.argv):
            only_slug = sys.argv[i + 1]
            i += 2
        elif arg == "--force":
            force = True
            i += 1
        else:
            sys.exit(f"unknown arg: {arg}")
    return lang, force, only_slug


def main():
    lang, force, only_slug = parse_args()
    if lang not in PROMPTS:
        sys.exit(f"unsupported lang: {lang}. Supported: {list(PROMPTS)}")

    prompts = PROMPTS[lang]
    cfg = yaml.safe_load(RESTAURANTS.read_text())

    if TRANSLATIONS.exists():
        translations = yaml.safe_load(TRANSLATIONS.read_text()) or {}
    else:
        translations = {}

    for r in cfg["restaurants"]:
        slug = r["slug"]
        if only_slug and slug != only_slug:
            continue
        entry = translations.setdefault(slug, {}).setdefault(lang, {})
        print(f"\n[{slug}] → {LANG_LABEL[lang]}")

        for field, template in prompts.items():
            # Special source: dining_record_md reads from photos/{slug}/notes.md
            if field == "dining_record_md":
                notes_path = ROOT / "photos" / slug / "notes.md"
                if not notes_path.exists():
                    continue
                value = notes_path.read_text(encoding="utf-8")
                # Strip YAML frontmatter before sending to LLM
                if value.startswith("---\n"):
                    end = value.find("\n---\n", 4)
                    if end > 0:
                        value = value[end + 5:]
            else:
                value = r.get(field)
            if not value:
                continue
            if entry.get(field) and not force:
                print(f"  ✓ {field} (cached)")
                continue
            print(f"  → {field}...", end="", flush=True)
            try:
                translated = translate_field(value, template, field)
                entry[field] = translated
                print(" OK")
            except Exception as e:
                print(f" FAIL: {e}")

    TRANSLATIONS.write_text(
        yaml.safe_dump(translations, allow_unicode=True, sort_keys=False, default_flow_style=False)
    )
    print(f"\nOK → translations.yaml")


if __name__ == "__main__":
    main()
