---
name: lit-spot-detection-benchmark
description: Spot-detector performance is strongly SNR-dependent; wavelet-multiscale & supervised methods best at low SNR (Smal 2010)
type: reference
tags:
- spot-detection
- benchmark
- SNR
- wavelet
- method
- reference
sources:
- Smal, Loog, Niessen, Meijering 2010, IEEE Trans. Medical Imaging 29:282-301 (PMID 19556194), https://smal.ws/pdf/tmi2010.pdf
links:
- log-dog-blob-method
- h-dome-localmax-method
- wavelet-spot-method
---

A systematic comparison of spot detectors (local background subtraction, linear &
morphological filtering, **wavelet multiscale**, and supervised ML) on synthetic and real
fluorescence data. Key findings:

- **Performance is strongly SNR-dependent** — no single detector wins everywhere.
- At **low SNR**, **wavelet-based multiscale** detectors and supervised methods are the most
  robust; simple intensity thresholds degrade fast.
- At **high SNR**, even simple methods do well.

**Implication for autofoci.** (1) Include a **wavelet / à-trous** family in the algorithm
pool — it is a literature-backed strong performer, especially for dim markers (Pol2). (2)
Make the proxy objective **SNR-aware** and **record SNR per marker**, since the best
algorithm depends on it. (3) Expect the winning detector to differ across markers.
