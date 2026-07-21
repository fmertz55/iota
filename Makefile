.PHONY: finding069-evidence finding070-evidence evidence validate validate-minimal-realization validate-minimal-realization-exact-orbit validate-quantum-dirac validate-quantum-dirac-symmetry-qca validate-quantum-dirac-symmetry-qca-archive verify validate-iota-submission iota-submission paper quantum-dirac-paper clean-paper clean-quantum-dirac-paper

PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

ifeq ($(strip $(PYTHON)),)
$(error Python 3 is required but neither python3 nor python was found)
endif

finding069-evidence:
	$(PYTHON) src/summarize_sequential_cut.py --through-depth 8 --quiet

finding070-evidence:
	$(PYTHON) src/summarize_independent_persistence.py --quiet

evidence: finding069-evidence finding070-evidence
	$(PYTHON) scripts/build_evidence.py

validate:
	$(PYTHON) scripts/validate_evidence.py

validate-minimal-realization:
	$(PYTHON) scripts/validate_minimal_realization.py \
		specs/icp_minimal_realization/v0.1-draft/lower_shell_null.json \
		specs/icp_minimal_realization/v0.2-draft/lower_shell_null.json
	$(PYTHON) -m src.minimal_realization.cli audit \
		--spec-dir specs/icp_minimal_realization/v0.2-draft
	$(PYTHON) -m src.minimal_realization.cli verify-seal \
		--seal experiments/minimal_realization/MIR-REFERENCE-SEARCH-001/outcome_sealed_manifest.json
	$(PYTHON) -m unittest discover -s tests/minimal_realization -p 'test_*.py'

validate-minimal-realization-exact-orbit:
	$(PYTHON) scripts/validate_archived_minimal_realization_exact_orbit.py
	$(PYTHON) -m unittest discover -s tests/minimal_realization_orbit -p 'test_*.py'

validate-quantum-dirac:
	$(PYTHON) scripts/validate_archived_quantum_dirac.py

validate-quantum-dirac-symmetry-qca:
	$(PYTHON) -m unittest discover -s tests/quantum_dirac_symmetry_qca -p 'test_*.py'

validate-quantum-dirac-symmetry-qca-archive:
	$(PYTHON) scripts/validate_archived_quantum_dirac_symmetry_qca.py --require-completion-tag

verify: evidence validate validate-minimal-realization validate-minimal-realization-exact-orbit validate-quantum-dirac validate-quantum-dirac-symmetry-qca

validate-iota-submission:
	$(PYTHON) scripts/validate_iota_submission.py

iota-submission:
	$(PYTHON) scripts/build_paper.py

paper: iota-submission

quantum-dirac-paper:
	$(PYTHON) scripts/build_quantum_dirac_paper.py

clean-paper:
	latexmk -C -outdir=build/paper paper/main.tex

clean-quantum-dirac-paper:
	latexmk -C -outdir=build/quantum_dirac_paper quantum_dirac_paper/main.tex
