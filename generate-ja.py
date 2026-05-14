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
        "name": '請將以下台灣餐廳名稱翻譯為日文(用日本人習慣的寫法,中文漢字保留可用日文讀法,可加片假名讀音):「{value}」。只回答譯名,不要解釋。',
        "name_alt": '請將以下餐廳副標題翻譯為自然日語:「{value}」。只回答譯名,不要解釋。',
        "location": '請將台灣地名「{value}」翻譯為日文常用寫法(例如「台中市南屯區」→「台中市南屯区」)。只回答譯名。',
        "cuisine": '請將以下料理類型翻譯為日文(用日本食記/食べログ常見詞):「{value}」。多個用「、」分隔,直接列出譯名,不要解釋。',
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
    if field == "cuisine" and isinstance(value, list):
        return [c.strip() for c in result.split("、") if c.strip()]
    return result


def parse_args():
    lang = "ja"
    force = False
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lang" and i + 1 < len(sys.argv):
            lang = sys.argv[i + 1]
            i += 2
        elif arg == "--force":
            force = True
            i += 1
        else:
            sys.exit(f"unknown arg: {arg}")
    return lang, force


def main():
    lang, force = parse_args()
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
