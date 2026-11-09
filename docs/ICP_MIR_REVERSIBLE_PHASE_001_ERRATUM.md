# MIR-REVERSIBLE-PHASE-001 erratum (2026-11-09)

Validity control V2 ("the nulls have no residue and n_shapes = 0") was mis-specified. SHADOW-009 stored data already
show 64 residue runs in null rule 5 (only = 0.625 at T in SHADOW-009's convention; reproduced here, V0 passes). The
premise was knowable before freezing and was not checked. Under the frozen rules the run is **invalid**. V2 is not
corrected and the test is not re-run, because all outcomes have now been seen. Rule 5's two residue shapes move
rigidly at +-0.33 (the carrier speed). They are carriers that `shadow.objects` does not recognise, not domains.
