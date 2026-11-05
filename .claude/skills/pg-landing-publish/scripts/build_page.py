#!/usr/bin/env python3
"""build_page.py: locked PG 2.0 landing page renderer (video section removed in v1). page.json keys: name, slug, owner, brandkit (path),
prepared, eyebrow, h1, lede, why_h2, why_p, signals[3-4]{date,title,body,angle,src}, props[3]?, proof[]{name,metric,quote?,cite?,url?,must_anonymize?}?, proof_h2?, final_h2?,
team? ("Airtable ANZ" default; "Airtable APAC" for accounts outside Australia / New Zealand).
Multi-view (pg-landing-publish v1, 2026-11-06): optional pov {key,label} and tabs[] {key,label,href,current}. With two or more tabs a tab bar
is rendered under the header; with none the output is byte-identical to the single-page v1 renderer. build_account.py fills tabs for you."""
import argparse, html, json, os, urllib.parse

OWNERS = {"Ryan Morris": ("Ryan", "ryan.morris@airtable.com"), "Harry O'Connor": ("Harry", "harry.oconnor@airtable.com")}
NAVY, NAVY2, CORAL = "#0a0e1a", "#1c243c", "#F82B60"
BEACON = """<!-- Cloudflare Web Analytics --><script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon='{"token": "1801083d0aad420c8b06164c2dc46273"}'></script><!-- End Cloudflare Web Analytics -->"""
PROPS = ["Replace the spreadsheets and status decks steering your programs with one source of truth for every workstream.",
         "Connect the systems you already run so data flows between them instead of being re-keyed.",
         "Give operations, technology, marketing and finance one connected way to run the work."]
CSS = """:root{--brand-primary:@@P@@;--brand-secondary:@@S@@;--airtable-accent:#F82B60;--ink:#0B0B0C;--muted:#5b6069;--line:#ececef;--bg:#ffffff;--bg-soft:#fafafa;--maxw:1080px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.55}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 6%}h1,h2,h3{letter-spacing:-.02em;line-height:1.08;margin:0}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--brand-secondary)}
.bk-header{display:flex;align-items:center;gap:16px;padding:20px 6%;border-bottom:4px solid var(--brand-primary)}
.bk-logo{height:34px;width:34px;border-radius:7px;object-fit:cover;box-shadow:0 0 0 1px var(--line)}.bk-name{font-weight:800;font-size:16px}
.bk-x{color:#b7bcc4;font-weight:300;font-size:20px;margin:0 2px}.bk-at{font-weight:900;font-size:18px;color:var(--airtable-accent);letter-spacing:-.02em}
.bk-tag{margin-left:auto;font-size:13px;font-weight:600;color:var(--brand-secondary)}
.hero{position:relative;overflow:hidden}.hero-band{position:absolute;inset:0;background:linear-gradient(115deg,@@P@@22,rgba(11,11,12,.04) 60%,transparent);z-index:0}
.hero .wrap{position:relative;z-index:1;padding-top:76px;padding-bottom:64px;display:grid;grid-template-columns:1.15fr .85fr;gap:48px;align-items:center}
.hero h1{font-size:clamp(34px,5vw,58px);font-weight:900}.hero h1 .grad{background:linear-gradient(90deg,var(--brand-primary),var(--airtable-accent));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p.lede{font-size:clamp(17px,2vw,20px);color:var(--muted);margin:22px 0 30px;max-width:34ch}
.hero-img{width:100%;aspect-ratio:16/11;object-fit:cover;border-radius:16px;box-shadow:0 24px 60px -24px @@P@@66;border:1px solid var(--line)}
.cta{display:inline-flex;align-items:center;gap:10px;background:var(--airtable-accent);color:#fff;font-weight:700;font-size:16px;padding:15px 26px;border-radius:10px;text-decoration:none;box-shadow:0 10px 24px -10px rgba(248,43,96,.6);transition:transform .15s ease}
.cta:hover{transform:translateY(-2px)}.cta-sub{display:block;margin-top:12px;font-size:13px;color:var(--muted)}
section{padding:64px 0;border-top:1px solid var(--line)}.sec-head{max-width:60ch;margin-bottom:36px}.sec-head h2{font-size:clamp(26px,3.4vw,38px);font-weight:800;margin-top:10px}.sec-head p{color:var(--muted);font-size:17px;margin:14px 0 0}
.signals{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}.signal{border:1px solid var(--line);border-left:4px solid var(--brand-primary);border-radius:12px;padding:22px 24px;background:var(--bg-soft)}
.signal .date{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--brand-secondary)}.signal h3{font-size:18px;font-weight:700;margin:8px 0 8px}.signal p{margin:0;color:var(--muted);font-size:15px}
.signal .angle{margin-top:12px;padding-top:12px;border-top:1px dashed var(--line);color:var(--ink);font-size:14.5px}.signal .angle b{color:var(--airtable-accent)}.signal .src{display:inline-block;margin-top:10px;font-size:12px;color:#9aa0a6}
.props{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;align-items:stretch}.prop{padding:28px 26px;border-radius:14px;border:1px solid var(--line);background:#fff;display:flex;flex-direction:column;height:100%}
.prop .n{font-size:13px;font-weight:800;color:var(--brand-primary)}.prop h3{font-size:21px;font-weight:800;margin:6px 0 10px}.prop p{margin:0;color:var(--muted);font-size:15px}
.proof-wrap{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}.customer-proof{border:1px solid var(--line);border-radius:14px;padding:26px;background:linear-gradient(180deg,#fff,var(--bg-soft))}
.cs-name{font-weight:800;font-size:15px;letter-spacing:.02em;color:var(--brand-secondary);text-transform:uppercase}.cs-metric{font-size:30px;font-weight:900;letter-spacing:-.02em;margin:8px 0 14px}
.cs-quote{margin:0;font-size:15.5px;line-height:1.5;color:#3a3f47;border:0;padding:0}.cs-quote cite{display:block;margin-top:10px;font-style:normal;font-size:13px;color:var(--muted)}
.cs-link{display:inline-block;margin-top:16px;font-weight:700;font-size:14px;color:var(--airtable-accent);text-decoration:none}.cs-link:hover{text-decoration:underline}
.final{background:linear-gradient(120deg,@@FA@@,@@FB@@);color:#fff;border:0;border-top:4px solid #F82B60}.final h2{color:#fff;font-size:clamp(26px,3.4vw,38px);font-weight:800}.final p{color:#e8e0ea;font-size:17px;margin:14px 0 28px;max-width:52ch}
footer{padding:34px 0;color:var(--muted);font-size:13px}footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:center}
@media(max-width:820px){.hero .wrap{grid-template-columns:1fr;padding-top:48px}.hero-img{order:-1}.signals,.props,.proof-wrap{grid-template-columns:1fr}}"""

TAB_CSS = """
.pov-tabs{display:flex;gap:2px;padding:0 6%;border-bottom:1px solid var(--line);overflow-x:auto;background:#fff}
.pov-tabs a{flex:none;padding:14px 16px 11px;font-size:14px;font-weight:600;color:var(--muted);text-decoration:none;border-bottom:3px solid transparent;white-space:nowrap}
.pov-tabs a:hover{color:var(--ink)}.pov-tabs a.on{color:var(--ink);border-bottom-color:var(--brand-primary)}"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def sig(s):
    return (f'<div class="signal"><span class="date">{esc(s.get("date"))}</span><h3>{esc(s.get("title"))}</h3><p>{esc(s.get("body"))}</p>'
            f'<div class="angle"><b>Airtable angle:</b> {esc(s.get("angle"))}</div><span class="src">{esc(s.get("src"))}</span></div>')


def proof(p):
    q = f'<blockquote class="cs-quote">&ldquo;{esc(p["quote"])}&rdquo;' + (f' <cite>&mdash; {esc(p["cite"])}</cite>' if p.get("cite") else "") + "</blockquote>" if p.get("quote") else ""
    link = f'<a class="cs-link" href="{esc(p["url"])}" target="_blank" rel="noopener noreferrer">Read the {esc(p["name"])} story &rarr;</a>' if p.get("url") and not p.get("must_anonymize") else ""
    return f'<div class="customer-proof"><div class="cs-name">{esc(p["name"])}</div><div class="cs-metric">{esc(p.get("metric"))}</div>{q}{link}</div>'


def render(d):
    kit = json.load(open(d["brandkit"])) if d.get("brandkit") and os.path.exists(d["brandkit"]) else {}
    branded = kit.get("palette_source") not in (None, "airtable-default")
    P = kit.get("primary") if branded else NAVY
    S = kit.get("secondary") if branded else NAVY2
    FA, FB = (S, NAVY) if branded else (NAVY2, NAVY)
    first, email = OWNERS[d["owner"]]
    name = d["name"]
    pov = d.get("pov") or {}
    pov_label = pov.get("label") if pov.get("key") not in (None, "overview") else None
    subject = urllib.parse.quote(f"Airtable x {name}" + (f" ({pov_label})" if pov_label else ""))
    team = d.get("team") or "Airtable ANZ"
    tabs = d.get("tabs") or []
    tabbar = ""
    if len(tabs) > 1:
        tabbar = ('<nav class="pov-tabs" aria-label="Views">' + "".join(
            f'<a href="{esc(t["href"])}"' + (' class="on" aria-current="page"' if t.get("current") else "") + f'>{esc(t["label"])}</a>'
            for t in tabs) + "</nav>\n")
    props = d.get("props") or PROPS
    cta = f'<a class="cta" href="mailto:{email}?subject={subject}">Book 20 minutes with {first} &rarr;</a>'
    logo = f'<img class="bk-logo" src="{esc(kit["logo_url"])}" alt="{esc(name)}" onerror="this.style.display=\'none\'">' if kit.get("logo_url") else ""
    hero = (f'<img class="hero-img" src="{esc(kit["hero_url"])}" alt="{esc(name)}" onerror="this.closest(\'.wrap\').style.gridTemplateColumns=\'1fr\';this.style.display=\'none\'">'
            if kit.get("hero_url") else "")
    proofs = "".join(proof(p) for p in d.get("proof", []))
    proof_sec = (f'<section><div class="wrap"><div class="sec-head"><span class="eyebrow">Proof</span><h2>{esc(d.get("proof_h2") or "Teams running connected work on Airtable")}</h2></div>'
                 f'<div class="proof-wrap">{proofs}</div></div></section>') if proofs else ""
    css = (CSS + ("\n" + TAB_CSS if tabbar else "")).replace("@@P@@", P).replace("@@S@@", S).replace("@@FA@@", FA).replace("@@FB@@", FB)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Airtable × {esc(name)}{(" · " + esc(pov_label)) if pov_label else ""}</title>
<meta name="description" content="A connected layer for {esc(name)}, grounded in its own strategy.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>{css}</style>
{BEACON}
</head><body>
<header class="bk-header">{logo}<span class="bk-name">{esc(name)}</span><span class="bk-x">&times;</span><span class="bk-at">Airtable</span>
  <span class="bk-tag">Prepared for {esc(name)} · {esc(d.get("prepared"))}</span></header>
{tabbar}<div class="hero"><div class="hero-band"></div><div class="wrap"><div>
  <span class="eyebrow">{esc(d.get("eyebrow"))}</span><h1>{d.get("h1", "")}</h1><p class="lede">{d.get("lede", "")}</p>
  {cta}<span class="cta-sub">{esc(d["owner"])} · Account Executive, {esc(team)}</span></div>{hero}</div></div>
<section><div class="wrap"><div class="sec-head"><span class="eyebrow">Why now</span><h2>{esc(d.get("why_h2"))}</h2><p>{esc(d.get("why_p"))}</p></div>
  <div class="signals">{"".join(sig(s) for s in d.get("signals", []))}</div></div></section>
<section><div class="wrap"><div class="sec-head"><span class="eyebrow">What Airtable does</span><h2>Consolidate, bridge, and unify the work</h2></div>
  <div class="props"><div class="prop"><div class="n">01 · CONSOLIDATE</div><h3>Consolidate</h3><p>{esc(props[0])}</p></div>
  <div class="prop"><div class="n">02 · BRIDGE</div><h3>Bridge</h3><p>{esc(props[1])}</p></div>
  <div class="prop"><div class="n">03 · UNIFY</div><h3>Unify</h3><p>{esc(props[2])}</p></div></div></div></section>
{proof_sec}
<section class="final"><div class="wrap"><span class="eyebrow" style="color:#fff">Let's talk</span><h2>{esc(d.get("final_h2") or "Twenty minutes on what's next")}</h2>
  <p>No pitch. Just a look at where a connected layer could take friction out of the work you're already driving.</p>{cta}</div></section>
<footer><div class="wrap"><span>Prepared for {esc(name)} by {esc(d["owner"])}, {esc(team)}.</span><span>Airtable &times; {esc(name)}</span></div></footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); d = json.load(open(a.inp))
    for k in ("name", "slug", "owner"):
        assert d.get(k), f"page.json missing {k}"
    assert d["owner"] in OWNERS, "owner must be Ryan Morris or Harry O'Connor (PG Plan Assignee)"
    assert len(d.get("signals", [])) >= 3, "need 3-4 dated, cited why-now signals"
    out = render(d); os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w").write(out)
    print(f"wrote {a.out} ({len(out)} bytes) slug={d['slug']}")


if __name__ == "__main__":
    main()
