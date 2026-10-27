# Pre-freeze verification log: `reference_classes.json`

Date: `2026-10-27`
Scope: every item in `pre_freeze_verification.values_pending`, plus the
"pending" qualitative claims in `literature_basis.md` where time allowed.

Method: arXiv full texts were downloaded and their text extracted. Each value
below was read in that text, or in an arXiv abstract page where stated. A value
counts as VERIFIED only if it was read in a source. Values computed from source
exponents are marked "derived" and show the arithmetic. Quotations are kept
under 15 words. PDF text extraction adds stray spaces inside numbers (for example
`0 .644700185(5)`), so those spaces were removed when transcribing.

Status key: **VERIFIED** = matches the source. **VERIFIED (derived)** = matches
a value computed from source-stated exponents. **MISMATCH** = the source gives a
different value or uncertainty. **UNREACHABLE** = no source was read.

---

## 1. `thresholds.domany_kinzel_bond_1p1.p_c` = 0.644700185(5)

- Source consulted: I. Jensen, "Low-density series expansions for directed
  percolation I: A new efficient algorithm with applications to the square
  lattice," J. Phys. A 32 (1999) 5233, DOI 10.1088/0305-4470/32/28/304,
  <https://arxiv.org/abs/cond-mat/9906036> (full text, arXiv v1).
- Found (Sec. 4.1 and Summary): "It seems reasonable to estimate that pc = 0.644700185(5)."
- Status: **VERIFIED**.

## 2. `thresholds.domany_kinzel_site_1p1.p_c` = 0.705485(5)

- Source consulted: the same Jensen (1999) paper, Sec. 4.2. It covers directed
  site percolation on the square lattice, which is the site-DP point
  `p1 = p2` of the Domany–Kinzel model.
- Found: the site series alone gives `pc = 0.70548515(20)`. The final estimate,
  which also uses the bond-series exponents, is
  "pc = 0.70548522(4), which I take as the final estimate."
- Cross-check: Hinrichsen, Adv. Phys. 49 (2000) 815, arXiv:cond-mat/0001070,
  Table 1, lists site DP as `0.705489(4)` (cited there to Tretyakov and Inui).
  It agrees with Jensen to within about 1σ of its own error.
- Status: **VERIFIED** (the value is in the paper). The registered number is a
  rounded, lower-precision form of Jensen's final `0.70548522(4)`, and the two
  agree. I recommend registering the final value.

## 3. `thresholds.simple_cubic_bond_percolation.p_c` = 0.24881182(10)

- Source consulted: J. Wang, Z. Zhou, W. Zhang, T. M. Garoni, Y. Deng, "Bond and
  Site Percolation in Three Dimensions," Phys. Rev. E 87 (2013) 052107,
  <https://arxiv.org/abs/1302.0421> (full text, v4).
- Found (abstract): "pc(bond) = 0.24881182(10)".
- Alternative `0.2488126(5)`: C. D. Lorenz and R. M. Ziff, "Precise
  determination of the bond percolation thresholds and finite-size scaling
  corrections for the s.c., f.c.c., and b.c.c. lattices," Phys. Rev. E 57 (1998)
  230, <https://arxiv.org/abs/cond-mat/9710044> (full text). Abstract:
  "pc(s.c.) = 0.2488126 ± 0.0000005". Wang et al. Table VII cites the same value
  to Lorenz and Ziff, PRE 57, 230.
- Further cross-check: Xu, Wang, Lv, Deng (2014, see item 4), Table V, gives a
  simultaneous-fit value of `0.24881185(10)`. It is consistent with the
  registered value.
- Status: **VERIFIED** (both the registered value and the alternative).

## 4. `thresholds.simple_cubic_site_percolation_z6.p_c` = 0.31160768(15)

- Source consulted: X. Xu, J. Wang, J.-P. Lv, Y. Deng, "Simultaneous analysis of
  three-dimensional percolation models," Front. Phys. 9 (2014) 113,
  DOI 10.1007/s11467-013-0403-z, <https://arxiv.org/abs/1310.5399> (full text).
- Found: Table V, row SC, "Site pc(Present)" `0.31160768(15)`.
- Alternatives:
  - `0.3116077(2)`: Wang et al. 2013 (arXiv:1302.0421), abstract
    "pc(site) = 0.3116077(2)". **VERIFIED**.
  - `0.3116080(4)`: listed in Wang et al. 2013 Table VII and cited there to
    Lorenz and Ziff, J. Phys. A 31 (1998) 8147. Read only in that table; the
    primary paper was not opened. **VERIFIED (via citing table)**.
  - Ballesteros et al. (arXiv:cond-mat/9805125), Table 8, gives
    `0.3116081(7)(2)`, which is consistent.
- Status: **VERIFIED**. The registered value comes from Xu et al. 2014, not from
  Wang et al. 2013.

## 5. `thresholds.simple_cubic_site_percolation_z26.p_c` = 0.0976445(10)

- Sources consulted:
  - Z. Xun, D. Hao, R. M. Ziff, "Site percolation on square and simple cubic
    lattices with extended neighborhoods and their continuum limit,"
    <https://arxiv.org/abs/2010.02895> (full text). Its 3D table, row
    `sc-1,2,3`, z = 26, gives present `0.0976444(6)`. Its "previous" column lists
    `0.0976445(10)`, cited to ref. [42]: "R. M. Ziff and S. Torquato. unpublished. 2010."
  - Z. Xun, D. Hao, R. M. Ziff, arXiv:2111.10975 (published as PRE 105 (2022)
    024105). Its table repeats `sc-1,2,3  26  0.0976444(6)`.
  - Kurzawski and Malarz, arXiv:1111.3254. Its abstract (seen through search
    results) gives `0.0976(1)`.
- Note: the arXiv number in the brief, `1910.11408`, is a different paper:
  Xun and Ziff on four-dimensional bond percolation. It contains no z = 26 SC
  site value.
- Status: **VERIFIED (value), but the precise figure has no published primary
  source.** `0.0976445(10)` is an unpublished Ziff–Torquato value, known only
  through Xun–Hao–Ziff's table. The published primary is `0.0976444(6)`, which
  agrees with it within error. I recommend registering the published value.
  Journal reference for arXiv:2010.02895: I did not read it from the arXiv page,
  so it should be confirmed before freeze. Search results suggest
  PRE 103 (2021) 022126.

## 6. `classes.DyP_3` static and dynamic exponents

### 6a. `static_tau` = 2.18906(8)

- Source consulted: H. G. Ballesteros, L. A. Fernández, V. Martín-Mayor,
  A. Muñoz Sudupe, G. Parisi, J. J. Ruiz-Lorenzo, "Scaling corrections:
  site-percolation and Ising model in three dimensions," J. Phys. A 32 (1999) 1,
  <https://arxiv.org/abs/cond-mat/9805125> (full text, v2).
- Found: Table 8, "This work", τ column `2.18906(6)(2)`, i.e. statistical (6)
  plus systematic (2), for a combined (8).
- Literature spread: `2.186(2)` is in the same Table 8, cited to Jan and
  Stauffer, Int. J. Mod. Phys. C 9 (1998) 341. **VERIFIED via the citing
  table.** `2.1938`: Wikipedia attributes it to Borinsky, Gracey, Kompaniets,
  Schnetz (2021, field theory). **UNREACHABLE** (not opened).
- Wikipedia footnotes `2.18906(8)` to Paul, Ziff, Stanley (2001),
  arXiv:cond-mat/0101136. That abstract gives τ only for 4D and 5D, so the
  attribution looks wrong. Cite Ballesteros et al. 1999.
- Status: **VERIFIED**.

### 6b. `static_d_f` = 2.5229(1)

- Sources: Xu et al. 2014 (arXiv:1310.5399), Sec. IV.A: "yh = 2.52293(10)".
  Wang et al. 2013 (arXiv:1302.0421) gives `yh = df = 2.52295(15)`.
- Status: **VERIFIED**.

### 6c. `static_nu` = 0.8762(12)

- Sources: Xu et al. 2014, Sec. IV.A: "yt = 1.1413(15)", giving
  ν = 1/yt = 0.87620(115). Wang et al. 2013 abstract: "1/ν = 1.1410(15)", giving
  ν = 0.8764(12). Ballesteros et al. 1999, Table 5: `0.8765(16)(2)`.
- Status: **VERIFIED (derived)** as `1/yt` from Xu et al. 2014.

### 6d. `static_beta` = 0.4181(8)

- Source: Wang et al. 2013 abstract, "β/ν = 0.47705(15)" and "1/ν = 1.1410(15)".
  These give β = 0.47705/1.1410 = 0.41810, with a propagated error of about
  0.0006. Using Xu et al.: (3 − 2.52293)/1.1413 = 0.41800.
- No source I read states β directly.
- Status: **VERIFIED (derived)**. The registered (8) is slightly conservative.

### 6e. `z` = d_min = 1.3756(3)

- Source: Wang et al. 2013, Sec. IV: "we estimate dmin = 1.3756(3)". The
  abstract gives the same value.
- Cross-check: Z. Zhou, J. Yang, Y. Deng, R. M. Ziff, "Shortest-path fractal
  dimension for percolation in two and three dimensions," Phys. Rev. E 86
  (2012) 061101, <https://arxiv.org/abs/1112.3428>. Abstract:
  "1.375 6(6) in two and three dimensions, respectively" (the 3D entry).
  Xu et al. 2014 give `dmin = 1.3755(3)`.
- Note: the arXiv number in the brief, `1112.0108`, is an unrelated astronomy
  paper (NGC 1068 CO observations). The correct number is `1112.3428`.
- Status: **VERIFIED**. Wang 2013 gives (3); Zhou 2012 gives (6).

### 6f. `delta` = 0.34681 and `eta` = 0.48725 (DyP_3 spreading)

- Direct measurement: S. M. Dammer and H. Hinrichsen, "Spreading with
  immunization in high dimensions," J. Stat. Mech. (2004) P07011,
  <https://arxiv.org/abs/cond-mat/0405577> (full text). Table C1 covers
  dynamical bond percolation, d = 3: `δ = 0.346(6)`, `θ = 0.488(7)`,
  `z = 1.375(5)`. Here θ is the activity exponent, called eta in the protocol,
  and z = ν‖/ν⊥.
- Derived from primary static exponents (Wang et al. 2013):
  δ = (β/ν)/d_min = 0.47705/1.3756 = 0.34679, and
  η = d_f/d_min − 1 − δ = 2.52295/1.3756 − 1 − 0.34679 = 0.48728.
  The hyperscaling form 3/1.3756 − 2δ − 1 gives the same 0.48728.
- Source of the 5-digit figures: Wikipedia gives `0.34681` and `0.48725` with no
  citation. They agree with the derived values to within about 2e-5 and 3e-5.
- Status: **VERIFIED (derived)**. The registered values are consistent with the
  direct measurement and with the primary static exponents. No primary source
  states exactly `0.34681` or `0.48725`. Register them as derived quantities,
  with uncertainties of about ±0.0003 propagated from d_min.

---

## 7. Secondary-table exponents

### 7a. `DP_1p1` (all six)

Source: Jensen 1999 (arXiv:cond-mat/9906036), Summary section, full text.

| field | registered | found in source | status |
|---|---|---|---|
| beta | 0.276486(8) | "β = (ν‖ + ν⊥ − γ)/2 = 0.276486(8)" | VERIFIED |
| nu_perp | 1.096854(4) | "ν⊥ = 1.096854(4)" | VERIFIED |
| nu_par | 1.733847(6) | "ν‖ = 1.733847(6)" | VERIFIED |
| delta | 0.159464(6) | "δ = β/ν‖ = 0.159464(6)" | VERIFIED |
| theta | 0.313686(8) | "η = γ/ν‖ − 1 = 0.313686(8)" (Jensen calls it η) | VERIFIED |
| z | 1.580745(10) | "z = ν‖/ν⊥ = 1.580745(10)" | VERIFIED |

Convention check: Jensen's `z = ν‖/ν⊥` matches the protocol's
`R2 ~ t^(2/z)`. The hyperscaling check gives 1/1.580745 − 2(0.159464) =
0.313685, which agrees.

### 7b. `DP_3p1`

Primary sources:

- (A) J. Wang, Z. Zhou, Q. Liu, T. M. Garoni, Y. Deng, "High-precision Monte
  Carlo study of directed percolation in (d+1) dimensions," Phys. Rev. E 88
  (2013) 042102, <https://arxiv.org/abs/1201.3006> (full text, v3). Table VII,
  d = 3, "Present": β 0.818(4), ν‖ 1.106(3), ν⊥ 0.582(2), z 1.8990(4),
  θ 0.1057(3), δ 0.7398(10). It defines `z = ν‖/ν⊥` (Eq. 18). The journal
  reference was not read from the arXiv page; confirm it before freeze.
- (B) I. Jensen, "Critical behavior of the three-dimensional contact process,"
  Phys. Rev. A 45 (1992) R563, DOI 10.1103/PhysRevA.45.R563. The abstract was
  read on the Flinders University repository page
  (<https://researchnow.flinders.edu.au/en/publications/critical-behavior-of-the-three-dimensional-contact-process/>).
  Greek symbols were stripped there, so the symbol mapping comes from row [28]
  of (A)'s Table VII. Values: ν‖ 1.11 ± 0.01, θ(η) 0.114 ± 0.004,
  δ 0.732 ± 0.004, β 0.813 ± 0.011. The abstract's `z = 1.052 ± 0.003` uses the
  `R2 ~ t^z` convention; (A) lists Jensen's value as `1.901(5)` in the `ν‖/ν⊥`
  convention.
- (C) Janssen, Z. Phys. B 42 (1981) 151, as row [6] of (A)'s Table VII:
  z 1.88746, θ 0.12084, δ 0.73717. These are field-theory (ε-expansion)
  values, not numerical estimates.
- (D) Dammer and Hinrichsen 2004 (arXiv:cond-mat/0405577), Table B1, d = 3 bond
  DP: δ 0.737(5), θ 0.107(5), z 1.897(5), pc 0.1774970(5).
- (E) Hinrichsen, Adv. Phys. 49 (2000) 815, arXiv:cond-mat/0001070, Table 2,
  d = 3: β 0.81(1), ν⊥ 0.581(5), ν‖ 1.105(5), z 1.90(1), δ 0.73, θ 0.12.
  Wikipedia's "Directed percolation" table, which lists β 0.813 ± 0.009,
  ν⊥ 0.584 ± 0.005, ν‖ 1.11 ± 0.01, cites this review as its source.

| field | registered | found | status |
|---|---|---|---|
| beta | 0.813(9) | 0.813(11) Jensen 1992 (B); 0.81(1) Hinrichsen (E); 0.818(4) Wang (A) | **MISMATCH (uncertainty)**: no source read gives ±0.009 |
| nu_perp | 0.584(5) | 0.581(5) Hinrichsen (E, the source Wikipedia cites); 0.582(2) Wang (A); Jensen (B) gives none | **MISMATCH**: 0.584(5) not found in any source read |
| nu_par | 1.11(1) | 1.11 ± 0.01 Jensen 1992 (B); 1.106(3) Wang (A) | VERIFIED (Jensen 1992) |
| delta spread 0.732(4) | 0.732 | 0.732 ± 0.004 Jensen 1992 (B); in (A) row [28] | VERIFIED |
| delta spread 0.7398(10) | 0.7398 | 0.7398(10) Wang (A) | VERIFIED |
| theta spread 0.1057(3) | 0.1057 | 0.1057(3) Wang (A) | VERIFIED |
| theta spread 0.114(4) | 0.114 | 0.114 ± 0.004 Jensen 1992 (B) | VERIFIED |
| z 1.8990(4) | 1.8990 | 1.8990(4) Wang (A) | VERIFIED |
| z 1.901(5) | 1.901 | 1.901(5) Jensen 1992, via (A) Table VII; equals 2/1.052 | VERIFIED |
| z 1.88746 | 1.88746 | 1.88746 Janssen 1981 via (A) | VERIFIED, but it is an ε-expansion value, not a measurement |

Attribution problem: the registered `source` string credits
"Grassberger and Zhang (1996)" among the underlying estimates. None of the
values above traces to that paper. 0.732(4), 0.114(4) and 1.901(5) are Jensen
(1992). Wikipedia attributes 0.732(4) and 1.901(5) to Henkel, Hinrichsen and
Lübeck (2008), which is a book.

Consistency of the registered midpoints: 3/1.9 − 2(0.736) = 0.107, against
registered θ = 0.11. Wang's set gives 3/1.8990 − 2(0.7398) = 0.1002, while
Wang's own direct θ is 0.1057(3). That is a known tension in the source and is
not introduced by the protocol.

### 7c. `DyP_2` (reference only)

- `z` = 1.13077(2): Zhou, Yang, Deng, Ziff, PRE 86 (2012) 061101,
  arXiv:1112.3428, abstract: "dmin = 1.13077(2)". **VERIFIED**.
- `delta` = 0.09212, `eta` = 0.584466: no primary source was read.
  Derived from exact 2D values β/ν = 5/48 and d_f = 91/48 with d_min = 1.13077:
  δ = 0.092120 and η = 0.584466. Both match. Dammer–Hinrichsen Table C1,
  quoting their ref. [41], lists 2D δ 0.092, θ 0.586, z 1.1295.
  **VERIFIED (derived)**.

---

## 8. Qualitative claims in `literature_basis.md`

### Grassberger, Chaté, Rousseau, PRE 55 (1997) 2488

- Primary: **UNREACHABLE**. The APS page returned HTTP 403. arXiv API searches
  (author Grassberger AND Rousseau; author Grassberger AND title "memory")
  found nothing, and web search found no preprint.
- Secondary check: Dammer and Hinrichsen 2004 (arXiv:cond-mat/0405577), Sec. 1
  and Fig. 1, summarize the 2D phase diagram of [17] = Grassberger, Chaté,
  Rousseau 1997. The summary says:
  - there are three phases;
  - a horizontal DP transition line at p = pc lies along the reinfection axis;
  - below it are an absorbing phase and "a phase of annular growth" in which an
    expanding front of high activity survives with finite probability;
  - the line from the GEP point to the DP point is in the DyP class, per Janssen.
- The protocol's summary agrees with this secondary account: a DyP transition
  into fresh territory, a DP reinfection transition, and an intermediate
  surviving-front regime. Status: **VERIFIED against a secondary source only**.

### Harris criterion (`d ν⊥ > 2` for irrelevance of weak disorder)

- Harris, J. Phys. C 7 (1974) 1671: **UNREACHABLE** (not opened).
- Hinrichsen 2000 (arXiv:cond-mat/0001070), Sec. 3.7, finds spatially quenched
  disorder marginal by power counting at dc = 4. Citing Janssen, it says the
  RG flow runs away, so such disorder "is expected to crucially disturb the
  critical behavior of DP".
- This supports the design conclusion: no clean class under quenched dilution
  in 3+1. The arithmetic 3 × ν⊥ ≈ 1.75 < 2 still holds with ν⊥ = 0.581 or 0.582.
- The literal `d ν⊥ > 2` statement was not read in a source. Status:
  **design conclusion supported; criterion statement UNREACHABLE**.

---

## Proposed edits to `reference_classes.json`

These are proposals only; no file was edited.

1. `thresholds.domany_kinzel_bond_1p1.verified_against` →
   `"Jensen, J. Phys. A 32 (1999) 5233, arXiv:cond-mat/9906036 v1, Sec. 4.1 and Summary: pc = 0.644700185(5); checked 2026-10-27"`

2. `thresholds.domany_kinzel_site_1p1`: value change recommended, for precision
   only, not because of a contradiction. `p_c` 0.705485 → **0.70548522**,
   `se` 5e-06 → **4e-08**.
   `verified_against` →
   `"Jensen, J. Phys. A 32 (1999) 5233, arXiv:cond-mat/9906036, Sec. 4.2 final estimate pc = 0.70548522(4) (directed site percolation, square lattice = DK site-DP point p1 = p2); site-series-only 0.70548515(20); cf. Hinrichsen 2000 Table 1: 0.705489(4); checked 2026-10-27"`
   If the old value is kept, use the same string with "registered value is a
   rounded form".

3. `thresholds.simple_cubic_bond_percolation.verified_against` →
   `"Wang, Zhou, Zhang, Garoni, Deng, PRE 87 (2013) 052107, arXiv:1302.0421 abstract: 0.24881182(10); alternative Lorenz & Ziff PRE 57 (1998) 230, arXiv:cond-mat/9710044 abstract: 0.2488126(5); checked 2026-10-27"`
   Also replace `source` with the Wang et al. citation instead of Wikipedia.

4. `thresholds.simple_cubic_site_percolation_z6.verified_against` →
   `"Xu, Wang, Lv, Deng, Front. Phys. 9 (2014) 113, arXiv:1310.5399, Table V: 0.31160768(15); alternatives Wang et al. PRE 87 (2013) 052107 (arXiv:1302.0421): 0.3116077(2); Lorenz & Ziff J. Phys. A 31 (1998) 8147: 0.3116080(4) (read in Wang et al. Table VII); checked 2026-10-27"`
   Also replace `source` with the Xu et al. 2014 citation.

5. `thresholds.simple_cubic_site_percolation_z26`: value change recommended,
   because the registered figure is unpublished. `p_c` 0.0976445 →
   **0.0976444**, `se` 1e-06 → **6e-07**, and `alternatives` →
   `["0.0976445(10) (Ziff & Torquato, unpublished 2010, as cited by Xun-Hao-Ziff)", "0.0976(1) (Kurzawski & Malarz, arXiv:1111.3254)"]`.
   `verified_against` →
   `"Xun, Hao, Ziff, arXiv:2010.02895, 3D table row sc-1,2,3 (z=26): 0.0976444(6); repeated in Xun & Hao arXiv:2111.10975 (PRE 105 (2022) 024105); 0.0976445(10) is Ziff & Torquato unpublished; checked 2026-10-27 (journal ref of 2010.02895 to be confirmed)"`

6. `classes.DyP_3.exponents.static_tau` → add
   `"verified_against": "Ballesteros et al., J. Phys. A 32 (1999) 1, arXiv:cond-mat/9805125, Table 8: tau = 2.18906(6)(2); spread value 2.186(2) (Jan & Stauffer 1998) in same table; 2.1938 not verified"`.
   Recommend changing `literature_spread` to `[2.186, 2.18906]` or adding a note
   that 2.1938 is unverified.

7. `classes.DyP_3.verified_against` →
   `"static: Wang et al. PRE 87 (2013) 052107, arXiv:1302.0421 (beta/nu = 0.47705(15), 1/nu = 1.1410(15), d_min = 1.3756(3)); Xu et al. Front. Phys. 9 (2014) 113, arXiv:1310.5399 (yt = 1.1413(15) -> nu = 0.8762(12); yh = d_f = 2.52293(10)); beta = 0.4181 derived; tau Ballesteros et al. 1999. Dynamic: Dammer & Hinrichsen J. Stat. Mech. (2004) P07011, arXiv:cond-mat/0405577, Table C1 d=3: delta = 0.346(6), theta = 0.488(7), z = 1.375(5); 5-digit delta/eta are derived (0.34679, 0.48728 from Wang 2013), not stated in a primary; checked 2026-10-27"`
   Optionally add `"se": 0.0003` to `delta` and `eta`, and tag them `"derived": true`.

8. `classes.DP_1p1.verified_against` →
   `"Jensen, J. Phys. A 32 (1999) 5233, arXiv:cond-mat/9906036, Summary section: all six values verbatim (theta is Jensen's eta; z = nu_par/nu_perp); checked 2026-10-27"`
   Also replace `source` with the Jensen citation.

9. `classes.DP_3p1`:
   - `beta`: `se` 0.009 → **0.011**, to match Jensen 1992 0.813(11).
     Alternatively, replace with Wang et al. 2013 **0.818(4)**.
   - `nu_perp`: 0.584(5) has no source. Change to **0.582, se 0.002** (Wang et
     al. 2013, Table VII) or **0.581, se 0.005** (Hinrichsen 2000 Table 2).
     Otherwise drop it if no gate uses it.
   - `nu_par`: keep 1.11(1) (Jensen 1992). Optionally note Wang 1.106(3).
   - `z.note` → `"1.8990(4) Wang et al. 2013; 1.901(5) Jensen 1992; 1.88746 is Janssen 1981 epsilon-expansion (field theory), not a numerical estimate"`.
   - `source`: remove "Grassberger and Zhang (1996)". Replace with
     `"Jensen, Phys. Rev. A 45 (1992) R563 (abstract); Wang, Zhou, Liu, Garoni, Deng, arXiv:1201.3006 Table VII; Janssen, Z. Phys. B 42 (1981) 151 (via Wang Table VII)"`.
   - `verified_against` →
     `"arXiv:1201.3006 v3 Table VII (d=3) read in full; Jensen 1992 abstract read via Flinders repository (symbols mapped via Wang Table VII row [28]); checked 2026-10-27"`

10. `classes.DyP_2` → add
    `"verified_against": "z = d_min = 1.13077(2): Zhou, Yang, Deng, Ziff PRE 86 (2012) 061101, arXiv:1112.3428 abstract; delta, eta derived from exact 2D beta/nu = 5/48, d_f = 91/48 (0.092120, 0.584466)"`.

11. `literature_basis.md` (not part of the JSON):
    - Mark the Grassberger–Chaté–Rousseau summary "consistent with the secondary
      summary in Dammer & Hinrichsen 2004 (arXiv:cond-mat/0405577); primary not
      accessed".
    - Mark the Harris criterion "design conclusion supported by Hinrichsen 2000
      Sec. 3.7; Harris 1974 not accessed".
    - Fix the Zhou et al. 2012 arXiv id to 1112.3428 wherever 1112.0108 was used.
