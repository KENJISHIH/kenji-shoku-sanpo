"""Scan photos/{slug}/ → compress + thumbnails → data/albums.json.

For each restaurant folder under photos/, this:
  1. Reads EXIF DateTimeOriginal for chronological order
  2. Writes a 1600px-long-edge JPG to dist/photos/{slug}/{name}.jpg
  3. Writes a 400px square-ish thumb to dist/photos/{slug}/thumb/{name}.jpg
  4. Records width/height/date_taken into data/albums.json
  5. Merges with restaurants.yaml metadata (name, location, rating, note...)

Incremental: skips files whose source mtime <= existing output mtime, so
re-runs are fast when you only add a few photos.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from PIL import ExifTags, Image, ImageOps
from pillow_heif import register_heif_opener

register_heif_opener()

ROOT = Path(__file__).parent
PHOTOS_DIR = ROOT / "photos"
DIST_PHOTOS = ROOT / "dist" / "photos"
DATA_DIR = ROOT / "data"

LARGE_EDGE = 1600
THUMB_EDGE = 400
JPEG_QUALITY_LARGE = 85
JPEG_QUALITY_THUMB = 80

SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
DOC_EXT = {".pdf"}


def exif_date(path: Path) -> str:
    """Return ISO date string from EXIF DateTimeOriginal, or '' if missing."""
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            for tag_id, value in exif.items():
                if ExifTags.TAGS.get(tag_id) == "DateTimeOriginal":
                    return str(value).replace(":", "-", 2)[:10]
    except Exception:
        pass
    return ""


def process_photo(src: Path, dst_large: Path, dst_thumb: Path) -> dict:
    needs_rebuild = (
        not dst_large.exists()
        or not dst_thumb.exists()
        or src.stat().st_mtime > dst_large.stat().st_mtime
    )

    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        w, h = im.size

        if needs_rebuild:
            large = im.copy()
            large.thumbnail((LARGE_EDGE, LARGE_EDGE), Image.LANCZOS)
            dst_large.parent.mkdir(parents=True, exist_ok=True)
            large.save(dst_large, "JPEG", quality=JPEG_QUALITY_LARGE, optimize=True)
            lw, lh = large.size

            thumb = im.copy()
            thumb.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.LANCZOS)
            dst_thumb.parent.mkdir(parents=True, exist_ok=True)
            thumb.save(dst_thumb, "JPEG", quality=JPEG_QUALITY_THUMB, optimize=True)
        else:
            with Image.open(dst_large) as lg:
                lw, lh = lg.size

    return {"width": lw, "height": lh, "date_taken": exif_date(src)}


def make_photo_record(src: Path, slug: str, subdir: str = "") -> dict:
    """Process one photo: compress + thumb, return dict for templates.
    subdir: "" for main grid, "_menu" / "_docs" for aux sections."""
    out_name = src.stem + ".jpg"
    rel_dir = f"{slug}/{subdir}" if subdir else slug
    dst_large = DIST_PHOTOS / rel_dir / out_name
    dst_thumb = DIST_PHOTOS / rel_dir / "thumb" / out_name
    info = process_photo(src, dst_large, dst_thumb)
    return {
        "filename": out_name,
        "title": src.stem,
        "large": f"photos/{rel_dir}/{out_name}",
        "thumb": f"photos/{rel_dir}/thumb/{out_name}",
        **info,
    }


def scan_aux(slug: str, folder: Path, subdir: str) -> list[dict]:
    """Scan _menu/ or similar subfolders for photos only."""
    if not folder.exists():
        return []
    files = sorted(p for p in folder.iterdir()
                   if p.is_file() and p.suffix.lower() in SUPPORTED_EXT)
    return [make_photo_record(p, slug, subdir) for p in files]


def scan_docs(slug: str, folder: Path) -> list[dict]:
    """_docs/: images compressed (with thumb), PDFs copied as-is."""
    if not folder.exists():
        return []
    items = []
    for src in sorted(folder.iterdir()):
        if not src.is_file():
            continue
        ext = src.suffix.lower()
        if ext in SUPPORTED_EXT:
            rec = make_photo_record(src, slug, "_docs")
            rec["type"] = "image"
            items.append(rec)
        elif ext in DOC_EXT:
            dst = DIST_PHOTOS / slug / "_docs" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                shutil.copy2(src, dst)
            items.append({
                "type": "pdf",
                "filename": src.name,
                "title": src.stem,
                "url": f"photos/{slug}/_docs/{src.name}",
            })
    return items


def scan_album(slug: str, folder: Path) -> list[dict]:
    """Scan main grid photos. Files/folders starting with `_` are skipped.
    - `_menu/` — public menu shots (handled by scan_aux)
    - `_docs/` — public store docs / storefront / PDFs (handled by scan_docs)
    - `_private/` — local-only, NEVER read by build pipeline (receipts, etc.)
    - `_captions.yaml` — per-photo dish names (future)
    """
    files = sorted(
        p for p in folder.iterdir()
        if p.is_file()
        and p.suffix.lower() in SUPPORTED_EXT
        and not p.name.startswith("_")
    )
    photos = [make_photo_record(p, slug) for p in files]
    # sort: by EXIF date, fall back to filename
    photos.sort(key=lambda p: (p["date_taken"] or "9999", p["filename"]))
    return photos


def main():
    if not PHOTOS_DIR.exists():
        raise SystemExit(f"ERROR: {PHOTOS_DIR} not found — drop photos in there first")

    cfg = yaml.safe_load((ROOT / "restaurants.yaml").read_text())
    out = []

    for r in cfg["restaurants"]:
        slug = r["slug"]
        folder = PHOTOS_DIR / slug
        if not folder.exists():
            print(f"  ⚠️  skip {slug}: photos/{slug}/ not found")
            continue

        print(f"  scanning {r['name']} (photos/{slug}/)...")
        photos = scan_album(slug, folder)
        menu_photos = scan_aux(slug, folder / "_menu", "_menu")
        docs = scan_docs(slug, folder / "_docs")
        out.append({
            **r,
            "photos": photos,
            "photo_count": len(photos),
            "menu_photos": menu_photos,
            "docs": docs,
        })
        extras = []
        if menu_photos: extras.append(f"{len(menu_photos)} menu")
        if docs: extras.append(f"{len(docs)} doc")
        extra_str = f" (+{', '.join(extras)})" if extras else ""
        print(f"    → {len(photos)} photos{extra_str}")

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "albums.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"OK: {len(out)} albums → data/albums.json")


if __name__ == "__main__":
    main()
