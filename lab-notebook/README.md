# Lab notebook

Two tiers, spanning **bench + computational** work:

- **`main.md`** — high-level dated log. One short block per working day; links out to the facet
  notebook(s) and experiment IDs touched. This is the chronology spine of the project.
- **Facet notebooks** — deeper running logs per area:
  - `wet-lab.md` — bench work: procedures, protocol changes/deviations, reagents & lots, imaging sessions.
  - `if-analysis.md` — IF image analysis (segmentation, foci, features, AnnData, cross-condition).
  - `probe-design.md` — E–P probe / panel design.
  - `autofoci.md` — agent parameter tuning + agnostic autofoci search.
  - (add one per new module.)

## Entry template (both tiers) — see `../_templates/notebook-entry.md`
```
## YYYY-MM-DD — <short title>
- What:    <bench procedure or computational step>
- Why:     <goal / question>
- Changes: <protocol version + deviations, or config/param changes; wet-lab: reagents/lots>
- Result:  <observation / outcome>
- Links:   experiment <ID> · results/... · [[wiki-page]] · raw data <pointer>
```

## The bench-day workflow
Tell Claude what you did on the bench (and any changes). It will: add a line to `main.md`, write the
detailed `wet-lab.md` entry, version the relevant `[[wiki/protocols]]` page if a protocol changed, and
register the raw-data pointer for the experiment that will consume it — keeping **bench → data →
analysis → figure** one traceable chain.

Dates are ISO `YYYY-MM-DD`. Durable knowledge (not chronology) belongs in `../wiki/`.
