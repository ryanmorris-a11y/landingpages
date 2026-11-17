#!/usr/bin/env python3
"""make_cards.py: render the 8-scene title cards for a landing page video in the locked identity
(navy gradient, coral accent line, Inter, white and grey three-line layouts). Runs in the cloud with Pillow and the
installed Inter OTF files. No network.

Usage:  make_cards.py <config.json> <account_dir>
config.json: {"slug": "atlassian", "name": "Atlassian", "overlay": "Atlassian",
              "s1": [["LINE ONE", 30, "grey", 600], ["Big line", 96, "white", 800], ["Line three", 34, "grey", 600]]}
Writes <account_dir>/cards/{s0_overlay,s1,s2,s6,s7,s8}.png. Weights: 600 SemiBold, 700 Bold, 800 ExtraBold.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
NAVY, NAVY_LIGHT, WHITE, GREY, CORAL = (10, 14, 26), (28, 36, 60), (255, 255, 255), (163, 170, 184), (248, 43, 96)
CMAP = {"grey": GREY, "white": WHITE}
FONT_DIR = os.environ.get("INTER_DIR", "/usr/share/fonts/opentype/inter")
FILES = {600: "Inter-SemiBold.otf", 700: "Inter-Bold.otf", 800: "Inter-ExtraBold.otf"}


def font(size, weight=700):
    return ImageFont.truetype(os.path.join(FONT_DIR, FILES.get(weight, FILES[700])), size)


def bg():
    base = Image.new("RGB", (W, H), NAVY)
    ell = Image.new("RGB", (W, H), NAVY)
    ImageDraw.Draw(ell).ellipse([W * 0.15, H * 0.05, W * 0.85, H * 0.95], fill=NAVY_LIGHT)
    return Image.blend(base, ell.filter(ImageFilter.GaussianBlur(300)), 0.85)


def card(path, lines, accent=True):
    img = bg()
    dd = ImageDraw.Draw(img)
    fs = [font(s, w) for (_, s, _, w) in lines]
    dims = []
    for i, ln in enumerate(lines):
        b = dd.textbbox((0, 0), ln[0], font=fs[i])
        dims.append((b[2] - b[0], b[3] - b[1]))
    gap = 40
    y = (H - (sum(h for _, h in dims) + gap * (len(lines) - 1))) // 2
    if accent:
        dd.rectangle([(W - 120) // 2, y - 52, (W - 120) // 2 + 120, y - 48], fill=CORAL)
    for i, (t, s, c, w) in enumerate(lines):
        dd.text(((W - dims[i][0]) // 2, y), t, font=fs[i], fill=CMAP[c])
        y += dims[i][1] + gap
    img.save(path)
    print("wrote", path)


def main():
    cfg = json.load(open(sys.argv[1]))
    out = os.path.join(sys.argv[2], "cards")
    os.makedirs(out, exist_ok=True)
    card(f"{out}/s1.png", [tuple(x) for x in cfg["s1"]])
    G, Wt = "grey", "white"
    card(f"{out}/s2.png", [("THE WORK IN BETWEEN", 34, G, 600), ("One connected layer", 96, Wt, 800), ("above the systems you already run", 34, G, 600)])
    card(f"{out}/s6.png", [("TRUSTED AT ENTERPRISE SCALE", 34, G, 600), ("80% of the Fortune 100", 104, Wt, 800), ("500,000+ organisations run on Airtable", 34, G, 600)])
    card(f"{out}/s7.png", [("THE FOUNDATION IS ALREADY IN PLACE", 34, G, 600), ("Let's build what's next", 96, Wt, 800), ("A conversation with Airtable ANZ", 34, G, 600)])
    card(f"{out}/s8.png", [(cfg["name"], 58, G, 700), ("+  Airtable", 108, Wt, 800)], accent=False)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(ov)
    f = font(72, 800)
    t = cfg["overlay"]
    b = dd.textbbox((0, 0), t, font=f)
    dd.rectangle([0, H - 230, W, H - 90], fill=(10, 14, 26, 90))
    dd.rectangle([(W - 120) // 2, H - 250, (W - 120) // 2 + 120, H - 246], fill=CORAL + (255,))
    dd.text(((W - (b[2] - b[0])) // 2, H - 210), t, font=f, fill=WHITE + (255,))
    ov.save(f"{out}/s0_overlay.png")
    print("overlay", cfg["slug"])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main()
