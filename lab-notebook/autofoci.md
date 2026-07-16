# Autofoci + agent tuning — facet notebook

Log for the agent "dry lab": guided foci-parameter tuning and the agnostic multi-algorithm autofoci
search (`agents/`, `IF/src/eporca/autofoci/`). Detector-choice knowledge → `[[wiki/methods]]` and
`[[wiki/findings]]`. Template: `../_templates/notebook-entry.md`.

---

## 2026-06-20 — Autofoci search, second pass
- **What:** Re-ran the agnostic search for all four markers. Picks: Brd4 `otsu_adaptive` (proxy 0.983),
  Pol2 `wavelet` (0.910), DAPI `wavelet` (0.971), Sc35 `mean_fold` (0.984). Adopted Sc35 into the config;
  kept Brd4/Pol2/DAPI on the lab's hand-tuned recipes.
- **Links:** `[[autofoci-brd4-20260620]]` · `[[autofoci-pol2-20260620]]` · `[[autofoci-dapi-20260620]]` · `[[autofoci-sc35-20260620]]`.

## 2026-06-12 — Autofoci search, first pass + Pol2 cliff
- **What:** First agnostic search. Found the Pol2 `mean_fold` threshold is cliff-like — the guided tuning
  loop oscillated (6→75→2→56→0.5) and never converged; wavelet is more robust at Pol2's low SNR.
- **Links:** `[[pol2-meanfold-cliff]]` · `[[wavelet-spot-method]]` · `[[autofoci-pol2-20260612]]`.
