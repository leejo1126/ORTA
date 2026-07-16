# Results catalog — experiment `<ID>`

Every file in `results/` gets a row here — this row **is** the required note. Curating an output into
`results/` is a deliberate act; anything not worth a row belongs in `scratch/` instead.

| File | What it is | How generated (cmd/script · experiment ID · git commit) | How to read (axes/panels/colors/units) | What it says (takeaway) | Links |
|---|---|---|---|---|---|
| `figures/example.png` | <one line> | `eporca analyze ... @<sha>` | <axes / color meaning / units> | <the result> | `[[wiki-page]]` |

<!--
Large binaries (multi-MB TIFFs, etc.): keep them gitignored under data/ or scratch/, and in the row
put their path + how to regenerate instead of tracking the blob.
For a figure needing a longer write-up, add a sidecar `figures/<name>.md` (see _templates/figure-sidecar.md).
-->
