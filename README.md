# metadatapacket.dev

A catalog and specification site for the **Metadata Packet for AI Indexing (MPAI)** discipline.

🌐 **Live site:** [metadatapacket.dev](https://metadatapacket.dev)
📚 **Specification:** [/spec/](https://metadatapacket.dev/spec/)
📥 **Submit a packet:** [/submit/](https://metadatapacket.dev/submit/)
⚙️ **LFB Protocol:** [/protocols/lfb/](https://metadatapacket.dev/protocols/lfb/)
🗄️ **Zenodo community:** [crimsonhexagonal](https://zenodo.org/communities/crimsonhexagonal/)

## What this is

A static site that indexes metadata packets — structured documents designed for entity-level retrieval architecture, disciplinary clarification, and AI knowledge graph alignment. The site does not host packet source files; it indexes DOI-anchored deposits hosted on Zenodo (or other DOI-issuing repositories).

## Categories

- **Bridge Packets** — disciplinary clarification, extending field-current concepts to AI-era articulations via the inverted fan
- **Disambiguation Packets** — entity-level identity work (persons, frameworks, organizations)
- **Retrieval Architecture Suite** — the formal infrastructure of indexing as a discipline
- **Forensic & Provenance Packets** — AI failure documentation, summarizer corrections, attribution scars
- **Methodology** — specifications, protocols, the MPAI architecture itself

## How to submit

1. Deposit your packet on Zenodo (or any DOI-issuing repository) following the [MPAI Specification](https://metadatapacket.dev/spec/).
2. Open a [submission issue](https://github.com/leesharks000/metadatapacket-dev/issues/new?template=submit-packet.yml) using the provided form.
3. Or open a Pull Request adding your packet to `public/catalog.json`.

No external accounts or apps are required beyond GitHub. The site is static and rebuilds automatically when `public/catalog.json` is updated.

## Architecture

- Static HTML, vanilla CSS, vanilla JS
- Zero build step — `public/` is the deployed root
- Catalog driven by `public/catalog.json`
- Submissions via GitHub Issue Templates
- Auto-deploys to Vercel on push to `main`

## License

Site code: MIT.
Catalog metadata (title, DOI, tooth, entity bridge, authors, date): CC0 — public domain.
Packet content: governed by the license attached to each Zenodo deposit (typically CC BY 4.0).

## ∮ = 1

Maintained by the Crimson Hexagonal Archive. Authority is structural.
