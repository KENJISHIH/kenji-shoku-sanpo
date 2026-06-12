"""Generate PWA / home-screen icons for 食散步 into static/.

Brand: warm amber gradient background, cream "食" wordmark glyph.
Run: ./.venv/bin/python scripts/gen_icons.py
Outputs static/{icon-192.png,icon-512.png,apple-touch-icon.png,favicon.ico}.
build.py copies static/ icons + writes manifest.json into dist/.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
STATIC.mkdir(exist_ok=True)

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
GLYPH = "食"
TOP = (217, 119, 6)      # amber-600  #d97706
BOTTOM = (146, 64, 14)   # amber-900  #92400e
FG = (253, 251, 247)     # cream      #fdfbf7


def render_master(size: int) -> Image.Image:
    """Render a square icon at the given pixel size."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        px_row = tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        for x in range(size):
            px[x, y] = px_row

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, int(size * 0.62))
    bbox = draw.textbbox((0, 0), GLYPH, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Center the glyph by its ink bounding box (CJK fonts carry side bearing).
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1]
    draw.text((x, y), GLYPH, font=font, fill=FG)
    return img


def main():
    master = render_master(1024)
    master.resize((512, 512), Image.LANCZOS).save(STATIC / "icon-512.png")
    master.resize((192, 192), Image.LANCZOS).save(STATIC / "icon-192.png")
    master.resize((180, 180), Image.LANCZOS).save(STATIC / "apple-touch-icon.png")
    master.resize((64, 64), Image.LANCZOS).save(
        STATIC / "favicon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )
    for f in sorted(STATIC.iterdir()):
        print(f"  ✓ {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
