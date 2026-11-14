#!/usr/bin/env python3
"""build_holograms.py — the page /holograms/: every framework hologram in the catalog on one page.

At the operator's word (2026-11-14 16:51: "metadatapacket probably needs a separate page for hfs"). A framework hologram (EA-HK-FRAME-01,
#1753) is one record in two components: a map for a human reader, its body, and a holographic kernel a machine can rebuild and test,
attached as files. Each hologram here is a catalog entry whose ea_id begins EA-HK-; its record, kernel files, structural tests and reader
rounds are read from the archive's registry and from the mantle-bearing dataset, the archive's table for inspection and evaluation.
Nothing is typed by hand.

    python3 scripts/build_holograms.py --archive /path/to/alexanarch
"""
import argparse, html, json, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]; PUB = ROOT / "public"; SITE = "https://www.metadatapacket.dev"; A = "https://www.alexanarch.org"
esc = lambda s: html.escape(s or "", quote=True)

PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta content="width=device-width,initial-scale=1" name="viewport"/>
<title>Framework holograms — MPAI Catalog</title>
<link rel="canonical" href="{site}/holograms/">
<meta content="Every framework hologram in the catalog: a map for the human reader and a holographic kernel a machine can rebuild and test, under EA-HK-FRAME-01 (#1753). {n} holograms." name="description"/>
<script type="application/ld+json">{jsonld}</script>
<style>
:root{{--bg:#fafaf7;--fg:#1c1c1a;--dim:#6b6b66;--accent:#1a3a5c;--rule:#d9d9d0;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111214;--fg:#e4e2dc;--dim:#9a9a94;--accent:#8fb4d9;--rule:#2a2b2f;--card:#18191c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 Georgia,'Times New Roman',serif}}
.wrap{{max-width:820px;margin:0 auto;padding:28px 16px 48px}}a{{color:var(--accent)}}
.crumb{{font:12px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}}
h1{{font-size:1.6em;margin:.5em 0 .2em}}.lede{{color:var(--dim);margin:0 0 1.4em}}
article{{border-top:1px solid var(--rule);padding:1em 0}}h2{{font-size:1.15em;margin:.2em 0 .3em}}
.m{{font:12px/1.6 ui-monospace,Menlo,monospace;color:var(--dim);overflow-wrap:anywhere}}.d{{margin:.4em 0}}
dl{{display:grid;grid-template-columns:max-content 1fr;gap:.2em .9em;font-size:.92em;margin:.6em 0 0}}dt{{color:var(--dim)}}dd{{margin:0;overflow-wrap:anywhere}}
.colophon{{font:11px/1.5 ui-monospace,Menlo,monospace;color:var(--dim);border-top:1px solid var(--rule);margin-top:2.5em;padding-top:.8em;overflow-wrap:anywhere}}
</style></head><body><div class="wrap">
<div class="crumb"><a href="/">metadatapacket.dev</a> · <a href="/packets/">every packet</a> · framework holograms</div>
<h1>Framework holograms</h1>
<p class="lede">A framework hologram holds a framework in two components, deposited as one record: the map, which a person reads, and the holographic kernel, which a machine can rebuild and test against the records it points to. The specification is <a href="{a}/s/records/1753/">EA-HK-FRAME-01 (#1753)</a>. Each hologram's readings by machine readers, its reconstructions and evaluations, are kept in the <a href="https://huggingface.co/datasets/leesharks/mantle-bearing">mantle-bearing dataset</a>, the archive's table for inspection and evaluation. {n} holograms, newest first.</p>
{rows}
<div class="colophon">surface_id: metadatapacket.dev/holograms · generator_version: scripts/build_holograms.py (from public/catalog.json, the archive's registry and the mantle-bearing dataset) · {n} holograms · human_approver: Lee Sharks (MANUS)</div>
</div></body></html>
"""


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--archive", required=True); a = ap.parse_args()
    AR = pathlib.Path(a.archive)
    REG = {d["deposit_number"]: d for d in json.loads((AR / "data/registry.json").read_text(encoding="utf-8"))["deposits"]}
    MB = json.loads((AR / "datasets/mantle-bearing/EA-MANTLE-BEARING-01-dataset.json").read_text(encoding="utf-8"))
    HB = {}
    for h in MB.get("holograms") or []:
        for r in h.get("hologram_record") or []: HB[r["deposit"]] = h
    EV = {}
    for e in MB.get("hologram_evaluations") or []: EV.setdefault(e["hologram"], []).append(e)
    cat = json.loads((PUB / "catalog.json").read_text(encoding="utf-8"))
    P = sorted([p for p in cat["packets"] if (p.get("ea_id") or "").startswith("EA-HK-")], key=lambda p: p["deposit"], reverse=True)
    rows, parts = [], []
    for p in P:
        r = REG.get(p["deposit"]) or {}; h = HB.get(p["deposit"]) or {}
        kf = (h.get("kernel_files") or {}).get("record") or f"{A}/files/AXN-{r.get('hex', '')}/kernel/"
        ev = EV.get(h.get("hologram"), [])
        rec = [e for e in ev if e.get("kind") == "reconstruction"]; evl = [e for e in ev if e.get("kind") == "evaluation"]; rv = [e for e in ev if e.get("kind") == "review"]
        rounds = "; ".join(f"round {x['round']} on {x.get('packet')}: mean {x['mean']}" if x.get("mean") is not None else f"round {x['round']} on {x.get('packet')}"
                           for x in (h.get("reader_rounds") or [])) or "none recorded"
        desc = re.sub(r"\s+", " ", html.unescape(p.get("description") or ""))
        desc = (desc[:600].rsplit(" ", 1)[0] + "…") if len(desc) > 600 else desc
        dl = [("record", f'<a href="{p["record"]}">#{p["deposit"]}</a> · {esc(r.get("axn") or p["axn"])} · {esc(r.get("version") or "")}'),
              ("map", f'<a href="/packets/{p["deposit"]}/">the packet page, with the map in full</a>' + (f' · <a href="{p["drop_in"]}">drop-in (.md)</a>' if p.get("drop_in") else "")),
              ("kernel", f'<a href="{kf}">the kernel files</a> ({len(r.get("files") or [])} attached files)'),
              ("structural tests", esc(h.get("structural_tests") or "—")), ("reader rounds", esc(rounds)),
              ("readings recorded", f"{len(rec)} reconstructions, {len(evl)} evaluations, {len(rv)} reviews"),
              ("failure flags", esc(", ".join((h.get("failure_flags") or {}).keys())) or "—")]
        rows.append(f'<article><h2><a href="{p["record"]}">{esc(p["title"])}</a></h2><div class="m">{esc(p.get("ea_id"))} · #{p["deposit"]} · {esc(p.get("date"))}</div>'
                    f'<p class="d">{esc(desc)}</p><dl>' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in dl) + "</dl></article>")
        parts.append({"@type": "Dataset", "name": p["title"], "url": p["record"], "identifier": [p["axn"], p.get("ea_id")]})
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": SITE + "/holograms/", "name": "Framework holograms — MPAI Catalog",
          "isPartOf": {"@type": "Dataset", "name": "MPAI Catalog", "url": SITE + "/"}, "hasPart": parts}
    (PUB / "holograms").mkdir(exist_ok=True)
    (PUB / "holograms/index.html").write_text(PAGE.format(site=SITE, a=A, n=len(P), rows="\n".join(rows), jsonld=json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")
    print(f"holograms: {len(P)} on /holograms/")


if __name__ == "__main__":
    main()
