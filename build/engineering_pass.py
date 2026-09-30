#!/usr/bin/env python3
"""Engineering pass asset fixes for the staged larsen-cpa.com rebuild.

Run from anywhere:  python3 site/build/engineering_pass.py

Fixes (item 3 + item 4 of the engineering review):
  * logos: regenerate at the size they are actually displayed (masthead <=38px,
    footer <=46px, phone 30px) instead of 160/200px tall.
  * fonts: the shipped "400" and "600" files are byte-identical copies of the
    SAME variable font (Inter wght 100..900, Source Serif 4 wght 200..900), so
    the 600 face was a duplicate that never provided a distinct weight. Keep one
    file per family and declare the variable weight range, so weight 600 resolves
    to a real instance instead of a duplicate.
  * hero photo: keep the 1800px master for desktop byte-for-byte and add a 900px
    source for phones/small screens (item 4).

Nothing is downloaded; all inputs are the files already in the working copy.
"""
import os
import shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
IMG = os.path.join(SITE, "assets", "img")
FONTS = os.path.join(SITE, "assets", "fonts")
COMP = "/Users/lloyd/.openclaw/workspace/lloyd/larsen_cpa/comps/assets/img"
BRAND = "/Users/lloyd/.openclaw/workspace/lloyd/larsen_cpa/site_assets/logo.png"


def kb(p):
    return os.path.getsize(p) // 1024


def key_plate(im, opaque_at=208, clear_at=248):
    """Drop the flat near-white plate the brand lockup is supplied on.
    Same ramp as build/build_assets.py so the mark keeps its existing edges."""
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


def _same_pixels(a, b, tol=6):
    """True when two RGBA images match within tol on every channel."""
    if a.size != b.size:
        return False
    from PIL import ImageChops
    diff = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
    return diff.getextrema() not in (None,) and all(hi <= tol for _lo, hi in diff.getextrema())


def save_png(im, out):
    """Save the smallest PNG that still renders as the RGBA original."""
    im.save(out, format="PNG", optimize=True)
    cand = out + ".q.png"
    try:
        q = im.quantize(colors=48, method=Image.FASTOCTREE)
        q.save(cand, format="PNG", optimize=True)
        check = Image.open(cand)
        if os.path.getsize(cand) < os.path.getsize(out) and _same_pixels(im, check):
            os.replace(cand, out)
        else:
            os.remove(cand)
    except Exception as exc:            # quantiser unavailable -> keep the RGBA file
        print("   (quantize skipped: %s)" % exc)
        if os.path.exists(cand):
            os.remove(cand)


def build_logos():
    jobs = [
        (BRAND, "logo.png", 76, True),                    # masthead renders at 38px -> 2x
        (os.path.join(COMP, "logo-reverse.png"), "logo-reverse.png", 92, False),  # footer 46px -> 2x
    ]
    for src, dst, height, key in jobs:
        im = Image.open(src).convert("RGBA")
        w, h = im.size
        nw = round(w * height / h)
        im = im.resize((nw, height), Image.LANCZOS)
        if key:
            im = key_plate(im)
        out = os.path.join(IMG, dst)
        save_png(im, out)
        print("%-20s %5dK -> %-20s %5dK (%dx%d)" % (os.path.basename(src), kb(src), dst, kb(out), nw, height))


def build_hero():
    master_jpg, master_webp = os.path.join(IMG, "hero-band.jpg"), os.path.join(IMG, "hero-band.webp")
    # 1800 master -> new names, byte for byte (desktop unchanged)
    shutil.copyfile(master_jpg, os.path.join(IMG, "hero-band-1800.jpg"))
    shutil.copyfile(master_webp, os.path.join(IMG, "hero-band-1800.webp"))
    # 900 phone/small-screen source, from the 2400 source for a clean downscale
    big = Image.open(os.path.join(COMP, "hero-band.jpg")).convert("RGB")
    small = big.resize((900, 375), Image.LANCZOS)
    small.save(os.path.join(IMG, "hero-band-900.jpg"), quality=70, optimize=True, progressive=True)
    small.save(os.path.join(IMG, "hero-band-900.webp"), quality=72, method=6)
    for stale in (master_jpg, master_webp):
        os.remove(stale)
    for n in ("hero-band-1800.jpg", "hero-band-1800.webp", "hero-band-900.jpg", "hero-band-900.webp"):
        p = os.path.join(IMG, n)
        print("hero %-22s %5dK" % (n, kb(p)))


def build_fonts():
    keep = [("inter-400.woff2", "inter-var.woff2", "Inter", "100 900"),
            ("source-serif-4-400.woff2", "source-serif-4-var.woff2", "Source Serif 4", "200 900")]
    lines = []
    for src, dst, fam, rng in keep:
        s, d = os.path.join(FONTS, src), os.path.join(FONTS, dst)
        shutil.copyfile(s, d)
        lines.append("@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
                     "font-display:swap;src:url('%s') format('woff2');}" % (fam, rng, dst))
        print("font %-22s -> %-24s %5dK  range %s" % (src, dst, kb(d), rng))
    for stale in ("inter-400.woff2", "inter-600.woff2",
                  "source-serif-4-400.woff2", "source-serif-4-600.woff2"):
        p = os.path.join(FONTS, stale)
        if os.path.exists(p):
            os.remove(p)
    with open(os.path.join(FONTS, "fonts.css"), "w") as fh:
        fh.write("/* Self-hosted (SIL OFL), subset to the site's own text. "
                 "Generated by build/build_assets.py, de-duplicated by "
                 "build/engineering_pass.py.\n"
                 "   The shipped files are variable fonts, so one file per family "
                 "covers every weight the site uses. */\n" + "\n".join(lines) + "\n")
    print("fonts.css written")


if __name__ == "__main__":
    build_logos()
    build_hero()
    build_fonts()
    print("engineering assets done")
