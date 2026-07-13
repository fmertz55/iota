.PHONY: finding069-evidence finding070-evidence evidence validate validate-minimal-realization validate-minimal-realization-exact-orbit verify paper clean-paper

finding069-evidence:
	python3 src/summarize_sequential_cut.py --through-depth 8 --quiet

finding070-evidence:
	python3 src/summarize_independent_persistence.py --quiet

evidence: finding069-evidence finding070-evidence
	python3 scripts/build_evidence.py

validate:
	python3 scripts/validate_evidence.py

validate-minimal-realization:
	python3 scripts/validate_minimal_realization.py \
		specs/icp_minimal_realization/v0.1-draft/lower_shell_null.json \
		specs/icp_minimal_realization/v0.2-draft/lower_shell_null.json
	python3 -m src.minimal_realization.cli audit \
		--spec-dir specs/icp_minimal_realization/v0.2-draft
	python3 -m src.minimal_realization.cli verify-seal \
		--seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/outcome_sealed_manifest.json
	python3 -m unittest discover -s tests/minimal_realization -p 'test_*.py'

validate-minimal-realization-exact-orbit:
	python3 scripts/validate_minimal_realization_exact_orbit.py
	python3 -m unittest discover -s tests/minimal_realization_orbit -p 'test_*.py'

verify: evidence validate validate-minimal-realization validate-minimal-realization-exact-orbit

paper:
	python3 scripts/build_paper.py

clean-paper:
	latexmk -C -outdir=build/paper paper/main.tex
