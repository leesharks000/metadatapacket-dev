#!/usr/bin/env python3
"""refresh_catalog.py — fill the curated catalog from the archive's own records.

MEMBERSHIP IS CURATED, FIELDS ARE DERIVED (2026-09-28). Which deposits the catalog holds is
an editorial act and stays in public/catalog.json. What each entry says about its deposit —
date, description, the aphoristic tooth, the error-correction FAQ, the identifier strings —
is read from the Crimson Hexagonal Archive's registry and texts, so the catalog cannot
drift from the records it lists.

On 2026-09-28 the page carried four packet counts at once (58 in the header, "updated
2026-07-20"; 57 in the meta tags; 61 in the stat block; catalog.json count 71 over 72
entries), and a Google AI Overview composed the site from the stat block that day. Counts
and dates are now derived: this script writes the catalog, build_site.py writes the page.

    python3 scripts/refresh_catalog.py --archive /path/to/alexanarch [--add 726,...]
"""
import argparse, datetime, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAT = ROOT / "public/catalog.json"
SITE = "https://www.metadatapacket.dev"


def text_path(archive, entry):
    p = entry.get("full_text_path")
    if p and (archive / p).exists():
        return archive / p
    return archive / "data/texts" / (entry["axn"].split(".")[0].replace(":", "-") + "-text.md")


def clean(s):
    s = re.sub(r"^\s*>\s?", "", s, flags=re.M)
    s = re.sub(r"\*\*|__", "", s)
    s = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", s)
    return " ".join(s.split()).strip()


def tooth(lines):
    for i, l in enumerate(lines):
        if re.match(r"^#+\s*aphoristic tooth\s*$", l.strip(), re.I):
            buf = []
            for m in lines[i + 1:]:
                if not m.strip():
                    if buf: break
                    continue
                if m.lstrip().startswith("#"): break
                buf.append(m)
            return clean(" ".join(buf)) or None
        m = re.match(r"^\s*(?:\*\*aphoristic tooth:\*\*|the aphoristic tooth:)\s*(.+)$", l, re.I)
        if m:
            return clean(m.group(1)) or None
    return None


def faq(lines):
    for i, l in enumerate(lines):
        m = re.match(r"^(#+)\s.*(FAQ|Frequently Asked)", l)
        if m:
            lvl = len(m.group(1)); out = []
            for n in lines[i + 1:]:
                h = re.match(r"^(#+)\s", n)
                if h and len(h.group(1)) <= lvl: break
                out.append(n)
            body = "\n".join(out).strip()
            return {"heading": re.sub(r"^#+\s*", "", l).strip(), "markdown": body} if body else None
    return None


def ea_id(title):
    m = re.search(r"\b(EA-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2})\b", title)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--add", default="")
    a = ap.parse_args()
    archive = pathlib.Path(a.archive)
    reg = {d["deposit_number"]: d for d in json.loads((archive / "data/registry.json").read_text(encoding="utf-8"))["deposits"]}
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    have = {p["deposit"] for p in cat["packets"]}
    for n in [int(x) for x in a.add.split(",") if x.strip()]:
        if n not in have:
            cat["packets"].append({"deposit": n}); have.add(n)
    drop_ins = {p.stem: p.name for p in list(ROOT.glob("EA-*.md")) + list((ROOT / "public").glob("EA-*.md"))}
    for p in cat["packets"]:
        r = reg[p["deposit"]]
        p["axn"] = r["axn"]; p["title"] = " ".join(r["title"].split()); p["date"] = str(r.get("date") or "")[:10]
        p["record"] = f"https://www.alexanarch.org/s/records/{p['deposit']}/"
        p["page"] = f"{SITE}/packets/{p['deposit']}/"
        p["description"] = " ".join(str(r.get("description") or "").split()) or None
        p["ea_id"] = ea_id(p["title"])
        p["drop_in"] = f"{SITE}/{drop_ins[p['ea_id']]}" if p["ea_id"] in drop_ins else None
        tp = text_path(archive, r)
        lines = tp.read_text(encoding="utf-8").split("\n") if tp.exists() else []
        p["tooth"] = tooth(lines); p["faq"] = faq(lines)
        p["text"] = f"https://www.alexanarch.org/data/texts/{tp.name}" if tp.exists() else None
    cat["count"] = len(cat["packets"])
    cat["updated"] = max(p["date"] for p in cat["packets"] if p["date"])
    cat["generated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()[:19] + "Z"
    cat["_derivation"] = ("Membership curated in this file; every other field derived from the Crimson Hexagonal "
                          "Archive registry and texts by scripts/refresh_catalog.py. count = entries; updated = latest deposit date.")
    CAT.write_text(json.dumps(cat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    t = sum(1 for p in cat["packets"] if p["tooth"]); f = sum(1 for p in cat["packets"] if p["faq"])
    print(f"catalog: {cat['count']} entries · updated {cat['updated']} · tooth {t} · faq {f}")


if __name__ == "__main__":
    main()
