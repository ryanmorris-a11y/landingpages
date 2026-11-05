#!/usr/bin/env python3
"""brand_kit.py: account-brand-kit extractor on the CONFIRMED domain. Public no-auth GETs; Pillow optional; never fabricates (see gaps[])."""
import argparse, json, os, re, sys, colorsys, urllib.request, urllib.error

UA = "Mozilla/5.0 (compatible; PG2-BrandKit/1.0; +https://airtable.com)"
TIMEOUT = 20


def _get(url, binary=False, max_bytes=3_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ct = r.headers.get("Content-Type", "")
            data = r.read(max_bytes)
            return {"ok": True, "status": r.status, "ct": ct, "url": r.geturl(), "data": data}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e), "url": url}
    except Exception as e:
        return {"ok": False, "status": None, "error": str(e), "url": url}


def norm_domain(d):
    d = d.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0]
    d = re.sub(r"^www\.", "", d)
    return d


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def hex_of(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def luminance(rgb):
    r, g, b = [c / 255 for c in rgb[:3]]
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def text_on(rgb):
    # WCAG-ish: white text on dark brand colour, near-black on light.
    return "#FFFFFF" if luminance(rgb) < 0.45 else "#0B0B0C"


def is_neutralish(rgb):
    r, g, b = rgb[:3]
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0 if mx == 0 else (mx - mn) / mx
    lum = luminance(rgb)
    return sat < 0.12 or lum > 0.93 or lum < 0.04  # greys / near-white / near-black


def palette_from_logo(logo_bytes):
    try:
        from PIL import Image
        import io
    except Exception:
        return None
    try:
        im = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        # composite over white so transparent logos don't yield black
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
        im = im.resize((120, 120))
        q = im.quantize(colors=16, method=2).convert("RGB")
        counts = {}
        for px in q.getdata():
            counts[px] = counts.get(px, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
        chromatic = [rgb for rgb, _ in ranked if not is_neutralish(rgb)]
        # order chromatic by saturation*count blend for a confident primary
        def score(rgb):
            r, g, b = [c / 255 for c in rgb]
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            return s * (counts.get(rgb, 0) ** 0.5)
        chromatic.sort(key=score, reverse=True)
        palette = [hex_of(c) for c in chromatic[:5]]
        return palette or None
    except Exception:
        return None


def palette_from_html(html):
    hexes = re.findall(r"#([0-9a-fA-F]{6})\b", html)
    theme = re.findall(r'name=["\']theme-color["\'][^>]*content=["\']#?([0-9a-fA-F]{6})', html)
    order, seen = [], set()
    for h in theme + hexes:
        h = h.upper()
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        if h in seen or is_neutralish(rgb):
            continue
        seen.add(h)
        order.append("#" + h)
        if len(order) >= 5:
            break
    return order or None


def meta(html, prop):
    for pat in (
        rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(prop)}["\']',
        rf'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)',
    ):
        m = re.search(pat, html, re.I)
        if m:
            return m.group(1)
    return None


def link_icon(html, base):
    icons = re.findall(r'<link[^>]+rel=["\']([^"\']*icon[^"\']*)["\'][^>]+href=["\']([^"\']+)', html, re.I)
    icons += [(rel, href) for href, rel in re.findall(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']([^"\']*icon[^"\']*)', html, re.I)]
    # prefer apple-touch-icon (bigger)
    icons.sort(key=lambda x: 0 if "apple" in x[0].lower() else 1)
    if icons:
        return absolutize(icons[0][1], base)
    return None


def absolutize(href, base):
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return base.rstrip("/") + href
    return base.rstrip("/") + "/" + href


def _valid_img(r):
    return r["ok"] and r["status"] == 200 and "image" in r["ct"] and len(r["data"]) > 512


def build(domain, account, outdir):
    domain = norm_domain(domain)
    account = account or domain.split(".")[0].capitalize()
    slug = slugify(account) or slugify(domain)
    base = f"https://{domain}"
    gaps = []

    html = ""
    hp = _get(base)
    if not hp["ok"]:
        hp = _get("https://www." + domain)
    if hp["ok"]:
        html = hp["data"].decode("utf-8", "ignore")
        base = hp["url"]
    else:
        gaps.append(f"homepage-unreachable({hp.get('status')})")

    site_name = meta(html, "og:site_name") or account
    hero_url = meta(html, "og:image")
    if hero_url:
        hero_url = absolutize(hero_url, base)
    else:
        gaps.append("og:image-miss")
    favicon = link_icon(html, base) if html else None

    candidates = [
        f"https://logo.clearbit.com/{domain}",
        favicon,
        f"https://www.google.com/s2/favicons?domain={domain}&sz=256",
    ]
    logo_url, logo_bytes = None, None
    tried = []
    for c in candidates:
        if not c:
            continue
        r = _get(c, binary=True)
        tried.append(f"{c.split('/')[2]}:{r.get('status')}")
        if _valid_img(r):
            logo_url, logo_bytes = c, r["data"]
            break
    if not logo_url:
        gaps.append("logo-miss(" + ",".join(tried) + ")")

    palette, src = None, None
    if logo_bytes:
        palette = palette_from_logo(logo_bytes)
        src = "logo-quantize" if palette else None
    if not palette and hero_url:
        hr = _get(hero_url, binary=True)
        if _valid_img(hr):
            palette = palette_from_logo(hr["data"])
            src = "hero-quantize" if palette else src
    if not palette and html:
        palette = palette_from_html(html)
        src = "html-scrape" if palette else src
    if not palette:
        palette = ["#F82B60"]  # last resort = Airtable coral; flagged, not a brand claim
        src = "airtable-default"
        gaps.append("palette-fallback")

    primary = palette[0]
    secondary = palette[1] if len(palette) > 1 else primary
    prgb = tuple(int(primary[i:i+2], 16) for i in (1, 3, 5))
    on_primary = text_on(prgb)

    kit = {
        "account": account,
        "site_name": site_name,
        "domain": domain,
        "logo_url": logo_url,
        "favicon_url": favicon,
        "hero_url": hero_url,
        "palette": palette,
        "primary": primary,
        "secondary": secondary,
        "on_primary": on_primary,
        "palette_source": src,
        "airtable_accent": "#F82B60",
        "gaps": gaps,
    }

    os.makedirs(outdir, exist_ok=True)
    json_path = os.path.join(outdir, f"brandkit-{slug}.json")
    with open(json_path, "w") as f:
        json.dump(kit, f, indent=2)

    kit["_files"] = {"json": json_path}
    return kit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, help="CONFIRMED account domain (from account-identity-gate)")
    ap.add_argument("--account", help="Account display name (derived from domain if omitted)")
    ap.add_argument("--out", default="./brandkit_out")
    a = ap.parse_args()
    kit = build(a.domain, a.account, a.out)
    print(json.dumps(kit, indent=2))


if __name__ == "__main__":
    main()
