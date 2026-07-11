.PHONY: evidence validate verify paper clean-paper

evidence:
	python3 scripts/build_evidence.py

validate:
	python3 scripts/validate_evidence.py

verify: evidence validate

paper:
	python3 scripts/build_paper.py

clean-paper:
	latexmk -C -outdir=build/paper paper/main.tex
