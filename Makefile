.PHONY: finding069-evidence evidence validate verify paper clean-paper

finding069-evidence:
	python3 src/summarize_sequential_cut.py --through-depth 8 --quiet

evidence: finding069-evidence
	python3 scripts/build_evidence.py

validate:
	python3 scripts/validate_evidence.py

verify: evidence validate

paper:
	python3 scripts/build_paper.py

clean-paper:
	latexmk -C -outdir=build/paper paper/main.tex
