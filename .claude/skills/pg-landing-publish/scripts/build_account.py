#!/usr/bin/env python3
"""build_account.py: render every view (point of view) of one account from its page sources.

Sources live in the repo at .pg-pages/<slug>/<view>.json (one build_page.py page.json per view; .pg-pages is a dot folder, so GitHub
Pages does not publish it). overview.json is required and renders to <slug>/index.html; every other view renders to
<slug>/<view>/index.html. With two or more views, each page gets the same tab bar (Overview first, then the POVS order below).

Run from the repo root:  python3 .claude/skills/pg-landing-publish/scripts/build_account.py <slug> [<slug> ...]
Prints one JSON line per account: {"slug", "views": [{"key","label","path","url"}]}. Exit 1 on any invalid source.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_page  # noqa: E402

BASE_URL = "https://ryanmorris-a11y.github.io/landingpages"
SRC = ".pg-pages"
# Fixed view keys. `functions` = the Champion Scorer CANON_FUNCTIONS each view speaks to, so the engagement step can pick the view
# that matches a lead (Exec persona leads get `executive` when it exists, else the overview).
POVS = {
    "overview":   {"label": "Overview",   "functions": []},
    "executive":  {"label": "Executive",  "functions": ["Executive/GM"]},
    "technology": {"label": "Technology", "functions": ["IT/Security", "Engineering/Tech", "Data/Analytics", "Product"]},
    "operations": {"label": "Operations", "functions": ["Operations", "PMO/Program"]},
    "finance":    {"label": "Finance",    "functions": ["Finance/Procurement", "Legal/Compliance"]},
    "marketing":  {"label": "Marketing",  "functions": ["Marketing/Growth", "Creative/Editorial", "Design"]},
    "customer":   {"label": "Customer",   "functions": ["Customer/Support", "Sales/Revenue"]},
    "people":     {"label": "People",     "functions": ["HR/People"]},
}
ORDER = list(POVS)


def load_views(slug):
    d = os.path.join(SRC, slug)
    if not os.path.isfile(os.path.join(d, "overview.json")):
        raise SystemExit(f"{slug}: {d}/overview.json missing")
    views = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        key = f[:-5]
        if key not in POVS:
            raise SystemExit(f"{slug}: unknown view '{key}' (allowed: {', '.join(ORDER)})")
        page = json.load(open(os.path.join(d, f)))
        if page.get("slug") != slug:
            raise SystemExit(f"{slug}/{f}: slug field is '{page.get('slug')}'")
        views.append((key, page))
    views.sort(key=lambda kv: ORDER.index(kv[0]))
    return views


def build(slug):
    views = load_views(slug)
    out = []
    for key, page in views:
        here_overview = key == "overview"
        tabs = []
        for k, _ in views:
            if here_overview:
                href = "./" if k == "overview" else f"{k}/"
            else:
                href = "../" if k == "overview" else f"../{k}/"
            tabs.append({"key": k, "label": POVS[k]["label"], "href": href, "current": k == key})
        page = dict(page, pov={"key": key, "label": POVS[key]["label"]}, tabs=tabs if len(views) > 1 else [])
        for k in ("name", "slug", "owner"):
            assert page.get(k), f"{slug}/{key}: missing {k}"
        assert page["owner"] in build_page.OWNERS, f"{slug}/{key}: owner must be one of {list(build_page.OWNERS)}"
        assert len(page.get("signals", [])) >= 3, f"{slug}/{key}: needs 3-4 dated, cited signals"
        path = f"{slug}/index.html" if here_overview else f"{slug}/{key}/index.html"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(build_page.render(page))
        url = f"{BASE_URL}/{slug}/" + ("" if here_overview else f"{key}/")
        out.append({"key": key, "label": POVS[key]["label"], "functions": POVS[key]["functions"], "path": path, "url": url})
    return {"slug": slug, "views": out}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for s in sys.argv[1:]:
        print(json.dumps(build(s)))
