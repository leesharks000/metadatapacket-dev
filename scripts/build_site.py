#!/usr/bin/env python3
"""build_site.py — the catalog's derived surfaces, from public/catalog.json.

  1. One page per packet at /packets/<deposit>/ (ruling 2a, 2026-09-28): the packet's face on
     its institutional surface — title, identifiers, description, aphoristic tooth, error-
     correction FAQ where the text carries one — pointing to the alexanarch record, which
     stays canonical for the full text. The page is canonical for itself and names the record
     as the work it is based on.
  2. Every count and date on the homepage, written from the catalog and the cards on the page
     (header, meta, stat, contents), so no figure is typed by hand.
  3. A "packet page" link on each homepage card.
  4. Domain-served copies of the drop-in files kept at the repository root (the root copies
     stay: other fleet sites cite them through raw.githubusercontent.com).
  5. The sitemap: the four standing pages, every packet page, every served drop-in.

Checks record; they do not block. Disagreements between the cards and the catalog are printed.

    python3 scripts/build_site.py
"""
import hashlib, html, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SITE = "https://www.metadatapacket.dev"


def esc(s): return html.escape(s or "", quote=True)


def md_to_html(md):
    import markdown
    return markdown.markdown(md, extensions=["tables"])


def render_hash(s):
    m = list(re.finditer(r"render_sha256[^:\n]{0,80}:\s*([0-9a-f]{64}|null)", s))
    if len(m) != 1: return s
    m = m[0]; t = s[:m.start(1)] + "null" + s[m.end(1):]
    return s[:m.start(1)] + hashlib.sha256(t.encode()).hexdigest() + s[m.end(1):]


PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta content="width=device-width,initial-scale=1" name="viewport"/>
<title>{title_t} — MPAI Catalog</title>
<link rel="canonical" href="{page}">
<meta content="{desc_m}" name="description"/>
<meta content="Lee Sharks" name="author"/>
<meta content="{title_t}" property="og:title"/><meta content="{desc_m}" property="og:description"/><meta content="{page}" property="og:url"/>
<script type="application/ld+json">{jsonld}</script>
<style>
:root{{--bg:#fafaf7;--fg:#1c1c1a;--dim:#6b6b66;--accent:#1a3a5c;--rule:#d9d9d0;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111214;--fg:#e4e2dc;--dim:#9a9a94;--accent:#8fb4d9;--rule:#2a2b2f;--card:#18191c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 Georgia,'Times New Roman',serif}}
.wrap{{max-width:760px;margin:0 auto;padding:28px 16px 48px}}a{{color:var(--accent)}}
.crumb{{font:12px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}}
h1{{font-size:1.6em;line-height:1.25;margin:.5em 0 .3em}}
.ids{{font:13px/1.6 ui-monospace,Menlo,monospace;color:var(--dim);overflow-wrap:anywhere}}
.tooth{{border-left:3px solid var(--accent);background:var(--card);padding:.8em 1.1em;margin:1.4em 0;font-size:1.08em}}
.tooth b{{display:block;font:11px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin-bottom:.3em;font-weight:normal}}
h2{{font:13px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:2.2em 0 .6em;border-top:1px solid var(--rule);padding-top:1.2em}}
.faq h3,.faq h4{{font-size:1em;margin:1.2em 0 .3em}}table{{border-collapse:collapse;display:block;overflow-x:auto}}td,th{{border:1px solid var(--rule);padding:4px 8px}}
.links a{{display:inline-block;margin:0 1em .4em 0}}
.colophon{{font:11px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);border-top:1px solid var(--rule);margin-top:2.5em;padding-top:.8em;overflow-wrap:anywhere}}
</style></head><body><div class="wrap">
<div class="crumb"><a href="/">metadatapacket.dev</a> · the MPAI catalog · packet</div>
<h1>{title}</h1>
<div class="ids">{ids}</div>
{tooth}
<h2>The packet</h2>
<p>{desc}</p>
<p class="links"><a href="{record}">Full packet — deposit #{deposit} (canonical record)</a>{drop}{text}</p>
{faq}
<h2>Where it sits</h2>
<p>A Metadata Packet for AI Indexing catalogued at <a href="/">metadatapacket.dev</a>. The specification is <a href="https://www.alexanarch.org/s/records/656/">deposit #656</a>; the catalog as data is <a href="/catalog.json">catalog.json</a>.</p>
<div class="colophon">colophon · surface_id: metadatapacket.dev/packets/{deposit} · canonical_url: {page} · object_state: canonical · source_object_ids: deposit #{deposit} · generator_version: scripts/build_site.py (from public/catalog.json) · human_approver: Lee Sharks (MANUS) · render_sha256 (of this file with this field’s value set to null): null</div>
</div></body></html>
"""


def packet_page(p):
    title = p["title"]
    ids = " · ".join(x for x in [f"deposit #{p['deposit']}", p.get("ea_id"), esc(p["axn"]), p.get("date")] if x)
    tooth = f'<div class="tooth"><b>Aphoristic tooth</b>{esc(p["tooth"])}</div>' if p.get("tooth") else ""
    faq = ""
    if p.get("faq"):
        faq = f'<h2>{esc(p["faq"]["heading"])}</h2><div class="faq">{md_to_html(p["faq"]["markdown"])}</div>'
    drop = f' <a href="{p["drop_in"]}">Drop-in file (.md)</a>' if p.get("drop_in") else ""
    text = f' <a href="{p["text"]}">Plain text</a>' if p.get("text") else ""
    desc = p.get("description") or ""
    desc_m = (desc[:280].rsplit(" ", 1)[0] + "…") if len(desc) > 280 else desc
    ld = {"@context": {"@vocab": "https://schema.org/", "spxi": "https://spxi.dev/vocabulary#"},
          "@type": "WebPage", "@id": p["page"], "url": p["page"], "name": title,
          "isPartOf": {"@type": "Dataset", "name": "MPAI Catalog", "url": SITE + "/"},
          "mainEntity": {"@type": "CreativeWork", "name": title, "url": p["record"],
                         "identifier": [x for x in [p["axn"], p.get("ea_id"), f"alexanarch:{p['deposit']}"] if x],
                         "author": {"@type": "Person", "name": "Lee Sharks", "identifier": "https://orcid.org/0009-0000-1599-0703"},
                         "datePublished": p.get("date"), "license": "https://creativecommons.org/licenses/by/4.0/"},
          "isBasedOn": p["record"]}
    if p.get("tooth"): ld["mainEntity"]["abstract"] = p["tooth"]
    s = PAGE.format(title_t=esc(re.sub(r"\s+", " ", title)[:160]), title=esc(title), page=p["page"], desc_m=esc(desc_m),
                    jsonld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"), ids=ids, tooth=tooth, desc=esc(desc),
                    record=p["record"], deposit=p["deposit"], drop=drop, text=text, faq=faq)
    return render_hash(s)


def main():
    cat = json.loads((PUB / "catalog.json").read_text(encoding="utf-8"))
    P = cat["packets"]
    # 4. served copies of root drop-ins
    served = []
    for f in sorted(ROOT.glob("EA-*.md")):
        dst = PUB / f.name
        if not dst.exists() or dst.read_bytes() != f.read_bytes():
            shutil.copyfile(f, dst)
    served = sorted(p.name for p in PUB.glob("EA-*.md"))
    # 1. packet pages
    for p in P:
        d = PUB / "packets" / str(p["deposit"]); d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(packet_page(p), encoding="utf-8")
    # 2–3. homepage
    ip = PUB / "index.html"; s = ip.read_text(encoding="utf-8")
    by_dep = {p["deposit"]: p for p in P}

    def link_card(m):
        art = m.group(0)
        if "packet-page" in art: return art
        r = re.search(r'alexanarch\.org/s/records/(\d+)/', art)
        if not r or int(r.group(1)) not in by_dep: return art
        return art.replace('<div class="packet-meta">', f'<div class="packet-meta"><a class="packet-page" href="/packets/{r.group(1)}/">packet page</a> &middot; ', 1)
    s = re.sub(r'<article class="packet">.*?</article>', link_card, s, flags=re.S)
    i_dis = s.find('<section class="category" id="disambiguation">'); i_meth = s.find('<h2 id="methodology"')
    i_build = s.find('<section class="category" id="build">')
    end = s.find("</section>", i_meth)
    n_build = s[i_build:i_dis].count('<article class="packet">')
    n_dis = s[i_dis:i_meth].count('<article class="packet">')
    n_meth = s[i_meth:end].count('<article class="packet">')
    cards = {int(x) for x in re.findall(r'<article class="packet">.*?alexanarch\.org/s/records/(\d+)/', s[i_dis:end], flags=re.S)}
    n_pk = n_dis + n_meth
    s = re.sub(r'(<div class="subtitle">Metadata Packet for AI Indexing · )\d+ packets · updated [0-9-]+(</div>)',
               rf'\g<1>{n_pk} packets · updated {cat["updated"]}\g<2>', s)
    s = re.sub(r'\d+ AXN-anchored packets(?=[. ])', f'{n_pk} AXN-anchored packets', s)
    s = re.sub(r'(<span class="stat-num">)\d+(</span><span class="stat-label">AXN-anchored MPAIs)', rf'\g<1>{n_pk}\g<2>', s)
    s = re.sub(r'(<a href="#disambiguation">Disambiguation Packets<span>)\d+', rf'\g<1>{n_dis}', s)
    s = re.sub(r'(<a href="#methodology">Methodology &amp; Specifications<span>)\d+', rf'\g<1>{n_meth}', s)
    s = re.sub(r'(<a href="#build">Build a packet<span>)\d+', rf'\g<1>{n_build}', s)
    s = re.sub(r'(<h2 id="methodology">Methodology &amp; Specifications <span class="count">)\d+', rf'\g<1>{n_meth}', s)
    s = re.sub(r'(<section class="category" id="disambiguation">\s*<h2 class="category-title">[^<]*<span class="category-count">)\d+', rf'\g<1>{n_dis}', s)
    ip.write_text(s, encoding="utf-8")
    # 5. sitemap
    urls = [f"{SITE}/", f"{SITE}/spec/", f"{SITE}/submit/", f"{SITE}/protocols/lfb/", f"{SITE}/catalog.json"]
    urls += [p["page"] for p in P] + [f"{SITE}/{n}" for n in served]
    lastmod = {p["page"]: p.get("date") for p in P}
    body = "\n".join(f"  <url><loc>{u}</loc>" + (f"<lastmod>{lastmod[u]}</lastmod>" if lastmod.get(u) else "") + "</url>" for u in urls)
    (PUB / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n', encoding="utf-8")
    cat_deps = set(by_dep)
    print(f"site: {len(P)} packet pages · homepage {n_pk} packets ({n_dis} disambiguation, {n_meth} methodology) + {n_build} build · "
          f"{len(served)} served drop-ins · sitemap {len(urls)} urls · updated {cat['updated']}")
    if cards - cat_deps: print(f"  RECORD: cards not in catalog: {sorted(cards - cat_deps)}")
    if cat_deps - cards: print(f"  RECORD: catalog entries without a card: {sorted(cat_deps - cards)}")


if __name__ == "__main__":
    main()
