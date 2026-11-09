#!/usr/bin/env python3
"""build_site.py — the catalog's derived surfaces, from public/catalog.json.

  1. One page per packet at /packets/<deposit>/: since 2026-10-29 (operator: "each metadata packet
     should have its own page under an index, like glyphic checksums") the page carries the
     packet's full text, read from the archive's seated text, below its title, identifiers,
     summary and aphoristic tooth; a superseded packet says so and links forward. The page is
     canonical for itself and names the alexanarch record as the work it is based on (ruling 2a,
     2026-09-28, which kept the full text on the record alone, is extended by that ruling).
  1a. The index at /packets/: every packet, newest first, each linking to its page, with a filter.
  2. Every count and date on the homepage, written from the catalog and the cards on the page
     (header, meta, stat, contents), so no figure is typed by hand.
  3. A "packet page" link on each homepage card.
  4. Domain-served copies of the drop-in files kept at the repository root (the root copies
     stay: other fleet sites cite them through raw.githubusercontent.com).
  5. The sitemap: the four standing pages, every packet page, every served drop-in.

Checks record; they do not block. Disagreements between the cards and the catalog are printed.

    python3 scripts/build_site.py --archive /path/to/alexanarch
"""
import argparse, hashlib, html, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUB = ROOT / "public"
SITE = "https://www.metadatapacket.dev"


def esc(s): return html.escape(s or "", quote=True)


def md_to_html(md):
    import markdown
    return markdown.markdown(md, extensions=["tables", "fenced_code"])


def full_text(archive, p):
    """The packet's seated text from the archive (data/texts), its YAML header and repeated title headings removed."""
    if not archive: return None
    reg = REG.get(p["deposit"]) or {}
    cand = [archive / reg["full_text_path"]] if reg.get("full_text_path") else []
    cand.append(archive / "data/texts" / (p["axn"].split(".")[0].replace(":", "-") + "-text.md"))
    f = next((c for c in cand if c.exists()), None)
    if not f: return None
    t = re.sub(r"\A---\n.*?\n---\n", "", f.read_text(encoding="utf-8"), flags=re.S).lstrip("\n")
    while re.match(r"#\s[^\n]*\n", t):  # the title heading, often written twice
        t = t.split("\n", 1)[1].lstrip("\n")
    return md_to_html(t)


REG = {}


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
.wrap>h2{{font:13px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--dim);margin:2.2em 0 .6em;border-top:1px solid var(--rule);padding-top:1.2em}}
.faq h3,.faq h4{{font-size:1em;margin:1.2em 0 .3em}}table{{border-collapse:collapse;display:block;overflow-x:auto}}td,th{{border:1px solid var(--rule);padding:4px 8px}}
.links a{{display:inline-block;margin:0 1em .4em 0}}
.full{{border-top:1px solid var(--rule);margin-top:.6em;padding-top:.4em;overflow-wrap:anywhere}}.full pre{{overflow-wrap:normal}}.full h2{{font-size:1.25em;margin:1.6em 0 .4em}}.full h3{{font-size:1.1em;margin:1.4em 0 .3em}}.full h4{{font-size:1em}}
.full pre{{background:var(--card);border:1px solid var(--rule);padding:.8em;overflow-x:auto;font-size:.8em;line-height:1.45}}.full code{{font-size:.88em;overflow-wrap:anywhere}}.full pre code{{overflow-wrap:normal}}
.full table{{font-size:.88em;margin:1em 0}}.full blockquote{{border-left:3px solid var(--rule);margin:1em 0;padding:.1em 1em;color:var(--dim)}}.full img{{max-width:100%}}
.sup{{background:var(--card);border:1px solid var(--rule);border-left:3px solid #a0522d;padding:.6em 1em;margin:1em 0;font-size:.95em}}
.colophon{{font:11px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);border-top:1px solid var(--rule);margin-top:2.5em;padding-top:.8em;overflow-wrap:anywhere}}
</style></head><body><div class="wrap">
<div class="crumb"><a href="/">metadatapacket.dev</a> · <a href="/packets/">every packet</a> · packet</div>
<h1>{title}</h1>
<div class="ids">{ids}</div>
{sup}{tooth}
<h2>Summary</h2>
<p>{desc}</p>
<p class="links"><a href="{record}">Deposit #{deposit} (the canonical record)</a>{drop}{text}</p>
{body}
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
    reg = REG.get(p["deposit"]) or {}
    sup = ""
    if reg.get("superseded_by_deposit_number"):
        n = reg["superseded_by_deposit_number"]
        sup = (f'<div class="sup">Superseded by <a href="/packets/{n}/">#{n}</a>' if n in BYDEP else f'<div class="sup">Superseded by <a href="https://www.alexanarch.org/s/records/{n}/">#{n}</a>') \
              + (f'. {esc(reg.get("superseded_reason") or "")}' if reg.get("superseded_reason") else "") + "</div>"
    ft = full_text(ARCHIVE, p)
    body = (f'<h2>The packet, in full</h2><div class="full">{ft}</div>' if ft else
            (f'<h2>{esc(p["faq"]["heading"])}</h2><div class="faq">{md_to_html(p["faq"]["markdown"])}</div>' if p.get("faq") else ""))
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
                    record=p["record"], deposit=p["deposit"], drop=drop, text=text, sup=sup, body=body)
    return render_hash(s)


INDEX = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta content="width=device-width,initial-scale=1" name="viewport"/>
<title>Every packet — MPAI Catalog</title>
<link rel="canonical" href="{site}/packets/">
<meta content="Every Metadata Packet for AI Indexing in the catalog, each on its own page with its full text: {n} packets, updated {updated}." name="description"/>
<script type="application/ld+json">{jsonld}</script>
<style>
:root{{--bg:#fafaf7;--fg:#1c1c1a;--dim:#6b6b66;--accent:#1a3a5c;--rule:#d9d9d0;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111214;--fg:#e4e2dc;--dim:#9a9a94;--accent:#8fb4d9;--rule:#2a2b2f;--card:#18191c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 Georgia,'Times New Roman',serif}}
.wrap{{max-width:820px;margin:0 auto;padding:28px 16px 48px}}a{{color:var(--accent)}}
.crumb{{font:12px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}}
h1{{font-size:1.6em;margin:.5em 0 .2em}}.lede{{color:var(--dim);margin:0 0 1.2em}}
input{{width:100%;font:inherit;font-size:.95em;padding:9px 14px;border:1px solid var(--rule);border-radius:999px;background:var(--card);color:var(--fg);margin:0 0 1.2em}}
ol{{list-style:none;padding:0;margin:0}}li{{border-top:1px solid var(--rule);padding:.75em 0}}li a.t{{font-size:1.05em;text-decoration:none}}li a.t:hover{{text-decoration:underline}}
.m{{font:12px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);overflow-wrap:anywhere;margin-top:.15em}}.d{{font-size:.92em;margin-top:.25em}}.sup{{color:#a0522d}}
.none{{display:none;color:var(--dim)}}
.colophon{{font:11px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);border-top:1px solid var(--rule);margin-top:2.5em;padding-top:.8em}}
</style></head><body><div class="wrap">
<div class="crumb"><a href="/">metadatapacket.dev</a> · the MPAI catalog · every packet</div>
<h1>Every packet</h1>
<p class="lede">{n} Metadata Packets for AI Indexing, newest first, each on its own page with its full text. The catalog as data is <a href="/catalog.json">catalog.json</a>; each packet's canonical record is in the Crimson Hexagonal Archive.</p>
<input type="search" placeholder="Filter by title, identifier or AXN" aria-label="Filter the packets">
<ol id="L">{rows}</ol><p class="none" id="none">No packet matches.</p>
<div class="colophon">surface_id: metadatapacket.dev/packets · generator_version: scripts/build_site.py (from public/catalog.json) · {n} packets · updated {updated}</div>
</div>
<script>const q=document.querySelector('input'),L=[...document.querySelectorAll('#L li')];q.oninput=()=>{{const w=q.value.toLowerCase().split(' ').filter(Boolean);let n=0;L.forEach(x=>{{const ok=w.every(v=>x.dataset.t.includes(v));x.style.display=ok?'':'none';n+=ok}});document.getElementById('none').style.display=n?'none':'block'}}</script>
</body></html>
"""


def index_page(P, updated):
    def summ(p):
        d = re.sub(r"\s+", " ", p.get("description") or "")
        return (d[:220].rsplit(" ", 1)[0] + "…") if len(d) > 220 else d
    rows = []
    for p in sorted(P, key=lambda p: (p.get("date") or "", p["deposit"]), reverse=True):
        reg = REG.get(p["deposit"]) or {}
        sup = f' · <span class="sup">superseded by #{reg["superseded_by_deposit_number"]}</span>' if reg.get("superseded_by_deposit_number") else ""
        meta = " · ".join(x for x in [f"#{p['deposit']}", p.get("ea_id"), esc(p["axn"]), p.get("date")] if x)
        key = esc(" ".join([p["title"], p.get("ea_id") or "", p["axn"], str(p["deposit"]), p.get("description") or ""]).lower())
        rows.append(f'<li data-t="{key}"><a class="t" href="/packets/{p["deposit"]}/">{esc(p["title"])}</a><div class="m">{meta}{sup}</div><div class="d">{esc(summ(p))}</div></li>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + "/packets/", "name": "Every packet — MPAI Catalog",
          "isPartOf": {"@type": "Dataset", "name": "MPAI Catalog", "url": SITE + "/"},
          "hasPart": [{"@type": "CreativeWork", "name": p["title"], "url": p["page"]} for p in P]}
    return INDEX.format(site=SITE, n=len(P), updated=updated, rows="".join(rows), jsonld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/"))


ARCHIVE = None; BYDEP = set()


def main():
    global ARCHIVE, BYDEP
    ap = argparse.ArgumentParser(); ap.add_argument("--archive", help="the alexanarch checkout, for the packets' full texts and supersession")
    a = ap.parse_args()
    if a.archive:
        ARCHIVE = pathlib.Path(a.archive)
        REG.update({d["deposit_number"]: d for d in json.loads((ARCHIVE / "data/registry.json").read_text(encoding="utf-8"))["deposits"]})
    else:
        print("  RECORD: no --archive given; packet pages carry the summary only")
    cat = json.loads((PUB / "catalog.json").read_text(encoding="utf-8"))
    P = cat["packets"]; BYDEP = {p["deposit"] for p in P}
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
    (PUB / "packets" / "index.html").write_text(index_page(P, cat["updated"]), encoding="utf-8")
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
    s = re.sub(r'(<section class="category" id="disambiguation">\s*<div class="packets">\s*<h2>Disambiguation Packets <span class="count">)\d+', rf'\g<1>{n_dis}', s)
    link = '<p class="all-packets" style="margin:.6em 0 0"><a href="/packets/">Every packet on its own page, with its full text &rarr;</a></p>'
    if 'class="all-packets"' not in s:
        s = re.sub(r'(<div class="subtitle">Metadata Packet for AI Indexing · [^<]*</div>)', lambda m: m.group(1) + link, s, count=1)
    ip.write_text(s, encoding="utf-8")
    # 5. sitemap
    urls = [f"{SITE}/", f"{SITE}/packets/", f"{SITE}/spec/", f"{SITE}/submit/", f"{SITE}/protocols/lfb/", f"{SITE}/catalog.json"]
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
