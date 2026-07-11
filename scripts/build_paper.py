from __future__ import annotations

import shutil
import subprocess
import sys

from evidence_common import ROOT


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    run(sys.executable, "scripts/build_evidence.py")
    run(sys.executable, "scripts/validate_evidence.py")
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print("Evidence built and validated; latexmk is not installed, so PDF compilation was skipped.")
        return 0
    run(latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=build/paper", "paper/main.tex")
    print("Paper built: build/paper/main.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
