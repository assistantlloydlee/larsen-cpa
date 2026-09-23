#!/usr/bin/env python3
"""Build the Larsen CPA site assets from the approved comps + brand logo.

Inputs (read only):
  lloyd/larsen_cpa/site_assets/logo.png          brand wordmark (1448x317)
  lloyd/larsen_cpa/comps/assets/img/hero-band.jpg
  lloyd/larsen_cpa/comps/assets/img/logo-reverse.png

Outputs:
  lloyd/larsen_cpa/site/assets/img/*   favicon.*, apple-touch-icon.png
  lloyd/larsen_cpa/site/assets/fonts/* self-hosted Inter / Source Serif 4 (latin)

No generated imagery: the favicon is a crop of the licensed brand mark.
"""
import os
import re
import urllib.parse
import urllib.request
from PIL import Image
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "comps", "assets", "img")
BRAND = os.path.join(ROOT, "site_assets", "logo.png")
OUT = os.path.join(ROOT, "site")
IMG = os.path.join(OUT, "assets", "img")
FONTS = os.path.join(OUT, "assets", "fonts")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36")


def ensure_dirs():
    for d in (IMG, FONTS, OUT):
        os.makedirs(d, exist_ok=True)


def kb(path):
    return os.path.getsize(path) // 1024


def ink_mask(im):
    px = im.load()
    W, H = im.size
    mask = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            mask[y][x] = a > 20 and not (r > 235 and g > 235 and b > 235)
    return mask


def monogram_bbox(path):
    """Largest letterform cluster at the left of the wordmark = the brand monogram.

    Found by connected components, not guessed: the text letters are ~50x79 and sit
    to the right, so everything whose bounding box ends before x=300 is the mark.
    """
    im = Image.open(path).convert("RGBA")
    W, H = im.size
    mask = ink_mask(im)
    seen = [[False] * W for _ in range(H)]
    boxes = []
    for y in range(H):
        for x in range(W):
            if mask[y][x] and not seen[y][x]:
                q = deque([(x, y)])
                seen[y][x] = True
                x0 = x1 = x
                y0 = y1 = y
                n = 0
                while q:
                    cx, cy = q.popleft()
                    n += 1
                    x0 = min(x0, cx); x1 = max(x1, cx)
                    y0 = min(y0, cy); y1 = max(y1, cy)
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            q.append((nx, ny))
                boxes.append((n, x0, y0, x1, y1))
    left = [b for b in boxes if b[3] <= 300]
    if not left:
        raise SystemExit("monogram detection failed")
    x0 = min(b[1] for b in left); y0 = min(b[2] for b in left)
    x1 = max(b[3] for b in left); y1 = max(b[4] for b in left)
    return im, (x0, y0, x1, y1)


def square_monogram(path, paper=(251, 250, 247)):
    im, (x0, y0, x1, y1) = monogram_bbox(path)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    side = int(max(w, h) * 1.14)              # optical padding inside the tile
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
    tile = Image.new("RGBA", (side, side), paper + (255,))
    crop = im.crop(box)
    tile.alpha_composite(crop, (max(0, -box[0]), max(0, -box[1])))
    return tile


def build_favicons():
    tile = square_monogram(BRAND)
    sizes = {"favicon-32.png": 32, "favicon-192.png": 192, "apple-touch-icon.png": 180,
             "favicon-512.png": 512}
    for name, px in sizes.items():
        tile.resize((px, px), Image.LANCZOS).convert("RGB").save(
            os.path.join(OUT, name), optimize=True)
    ico = [tile.resize((s, s), Image.LANCZOS).convert("RGB") for s in (16, 32, 48)]
    ico[0].save(os.path.join(OUT, "favicon.ico"), format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48)])
    for stale in ("favicon-512.png", "inter-500.woff2"):
        p = os.path.join(OUT if stale.startswith("favicon") else FONTS, stale)
        if os.path.exists(p):
            os.remove(p)
    print("favicon: monogram tile %dpx -> ico + png set" % tile.size[0])


def key_plate(im, opaque_at=208, clear_at=248):
    """Drop the flat white plate the brand lockup is supplied on.

    The mark arrives as dark artwork on an opaque near-white ground, which paints a
    visible rectangle on --paper (#FBFAF7). Pixels at or above `clear_at` become
    fully transparent, pixels at or below `opaque_at` keep full opacity, and the
    anti-aliased boundary ramps between the two so the cut stays clean. Applied
    after resizing, so the downscale's own anti-aliasing is what gets ramped.
    """
    im = im.convert("RGBA")
    px = im.load()
    W, H = im.size
    span = clear_at - opaque_at
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            m = min(r, g, b)
            if m >= clear_at:
                al = 0
            elif m <= opaque_at:
                al = 255
            else:
                al = int(round(255 * (clear_at - m) / span))
            px[x, y] = (r, g, b, min(a, al) if a < 255 else al)
    return im


def build_logos():
    for src, dst, height in (("logo.png", "logo.png", 160),
                             ("logo-reverse.png", "logo-reverse.png", 200)):
        p = os.path.join(SRC, src)
        im = Image.open(p).convert("RGBA")
        w, h = im.size
        nw = round(w * height / h)
        out = os.path.join(IMG, dst)
        # Resize first, then key the plate: the mark keeps the downscale's own
        # anti-aliasing, and the surrounding pixels become the page, not a plate.
        im = im.resize((nw, height), Image.LANCZOS)
        if dst == "logo.png":
            im = key_plate(im)
        im.save(out, optimize=True)
        a = im.split()[3].getextrema()
        print("%-20s %4dK -> %-20s %4dK (%dx%d) alpha %s"
              % (src, kb(p), dst, kb(out), nw, height, a))


def build_hero():
    src = os.path.join(SRC, "hero-band.jpg")
    im = Image.open(src).convert("RGB")
    # The band renders at most 1140x400 CSS px; 1800px keeps it crisp at 2x on desktop.
    im = im.resize((1800, 750), Image.LANCZOS)
    jpg = os.path.join(IMG, "hero-band.jpg")
    im.save(jpg, quality=70, optimize=True, progressive=True)
    webp = os.path.join(IMG, "hero-band.webp")
    im.save(webp, quality=72, method=6)
    print("hero-band.jpg %4dK -> %4dK jpg, %4dK webp" % (kb(src), kb(jpg), kb(webp)))


def site_text_charset():
    """Every character that actually renders on the built pages (entities resolved),
    plus a safety set so ordinary English copy never hits a missing glyph."""
    import glob
    import html as htmllib
    base = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            " .,;:!?'\"()[]{}<>/\\|@#$%^&*_+=~`-\u2013\u2014\u2018\u2019\u201c\u201d"
            "\u00b7\u00a9\u00ae\u2122\u00b0\u2026\u00a0\u2022\u00a7\u00a3\u20ac\u2192")
    chars = set(base)
    for f in glob.glob(os.path.join(OUT, "*.html")):
        s = open(f).read()
        s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
        s = re.sub(r"<[^>]+>", " ", s)
        chars |= set(htmllib.unescape(s))
    return "".join(sorted(c for c in chars if c.isprintable() or c == " "))


def build_fonts():
    # Google Fonts subsets to exactly the characters the site renders, so the webfont
    # payload is a fraction of the full latin subset. Only 400/600 are used.
    charset = site_text_charset()
    css_url = ("https://fonts.googleapis.com/css2"
               "?family=Source+Serif+4:wght@400;600"
               "&family=Inter:wght@400;600&display=swap&text="
               + urllib.parse.quote(charset, safe=""))
    req = urllib.request.Request(css_url, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=30).read().decode()
    blocks = re.findall(r"(?:/\*\s*([a-z\-]+)\s*\*/\s*)?@font-face\s*\{(.*?)\}", css, re.S)
    out_css = []
    seen = set()
    for subset, body in blocks:
        if subset and subset != "latin":
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        wt = re.search(r"font-weight:\s*(\d+)", body).group(1)
        if (fam, wt) in seen:
            continue
        seen.add((fam, wt))
        url = re.search(r"url\((https://[^)]+)\)", body).group(1)
        slug = fam.lower().replace(" ", "-") + "-" + wt + ".woff2"
        dest = os.path.join(FONTS, slug)
        r = urllib.request.Request(url, headers={"User-Agent": UA})
        with open(dest, "wb") as fh:
            fh.write(urllib.request.urlopen(r, timeout=30).read())
        out_css.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
            "font-display:swap;src:url('%s') format('woff2');}" % (fam, wt, slug))
        print("font %-16s w%s -> %-24s %4dK" % (fam, wt, slug, kb(dest)))
    with open(os.path.join(FONTS, "fonts.css"), "w") as fh:
        fh.write("/* Self-hosted (SIL OFL), subset to the site's own text. "
                 "Generated by build/build_assets.py. */\n" + "\n".join(out_css) + "\n")
    print("charset: %d characters" % len(charset))


if __name__ == "__main__":
    ensure_dirs()
    build_logos()
    build_favicons()
    build_hero()
    build_fonts()
    print("assets done")
