from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_COMMIT = "0795a6efa0252411c66479cb87863349e20ec886"
DEFAULT_SOURCE_DATE_EPOCH = "1784353304"  # RESULT_COMMIT author timestamp
TECHNICAL_STEM = "quantum_dirac_operational_role_manuscript"
LAY_STEM = "quantum_dirac_layperson_companion"


def run(*arguments: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_version(command: str, *arguments: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        return "unavailable"
    completed = run(executable, *arguments, capture=True)
    output = completed.stdout or completed.stderr
    return next((line.strip() for line in output.splitlines() if line.strip()), "unknown")


def python_tool_versions(python: str) -> dict[str, str]:
    probe = """
import json
import platform
from importlib import metadata

def version(distribution):
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "unavailable"

print(json.dumps({
    "python": platform.python_version(),
    "python_implementation": platform.python_implementation(),
    "numpy": version("numpy"),
    "matplotlib": version("matplotlib"),
    "mpmath": version("mpmath"),
    "python-flint": version("python-flint"),
}, sort_keys=True))
"""
    return json.loads(run(python, "-c", probe, capture=True).stdout)


def write_build_manifest(
    final_path: Path,
    artifact_stem: str,
    artifact_inputs: list[Path],
    audit_path: Path,
    source_date_epoch: str,
    python_versions: dict[str, str],
) -> tuple[Path, Path]:
    artifact_digest = sha256(final_path)
    digest_path = final_path.with_suffix(final_path.suffix + ".sha256")
    digest_path.write_text(f"{artifact_digest}  {final_path.name}\n")

    manifest_path = final_path.with_name(f"{artifact_stem}.build.json")
    source_date = datetime.fromtimestamp(
        int(source_date_epoch), tz=timezone.utc
    ).isoformat().replace("+00:00", "Z")
    input_paths = [
        *artifact_inputs,
        ROOT / "quantum_dirac_paper/bibliography.bib",
        ROOT / "quantum_dirac_paper/requirements.txt",
        ROOT / "quantum_dirac_paper/generated/results_summary.json",
        ROOT
        / "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/independent_verification_receipt_v0.4.json",
        ROOT
        / "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/POST_RESULT_AUDIT.md",
        ROOT / "scripts/audit_direct_qca_pi_sector.py",
        ROOT / "scripts/build_quantum_dirac_paper.py",
        ROOT / "scripts/generate_quantum_dirac_paper.py",
        ROOT / "scripts/validate_archived_quantum_dirac_symmetry_qca.py",
    ]
    inputs = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in input_paths
    }
    manifest = {
        "schema_version": "1.0",
        "artifact": {
            "path": str(final_path.relative_to(ROOT)),
            "sha256": artifact_digest,
            "sha256_file": str(digest_path.relative_to(ROOT)),
            "size_bytes": final_path.stat().st_size,
        },
        "build": {
            "source_date_epoch": source_date_epoch,
            "source_date_utc": source_date,
            "content_addressed_result_commit": RESULT_COMMIT,
            "direct_pi_sector_audit": {
                "path": str(audit_path.relative_to(ROOT)),
                "sha256": sha256(audit_path),
                "status": json.loads(audit_path.read_text())["status"],
            },
            "inputs_sha256": inputs,
        },
        "tool_versions": {
            **python_versions,
            "latexmk": command_version("latexmk", "-version"),
            "pdftex": command_version("pdflatex", "--version"),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return digest_path, manifest_path


def main() -> int:
    source_date_epoch = os.environ.setdefault(
        "SOURCE_DATE_EPOCH", DEFAULT_SOURCE_DATE_EPOCH
    )
    try:
        int(source_date_epoch)
    except ValueError as error:
        raise RuntimeError("SOURCE_DATE_EPOCH must be an integer Unix timestamp") from error
    os.environ.setdefault("FORCE_SOURCE_DATE", "1")
    os.environ.setdefault("TZ", "UTC")

    environment_python = ROOT / ".venv" / "bin" / "python"
    python = str(
        environment_python if environment_python.is_file() else Path(sys.executable)
    )
    python_versions = python_tool_versions(python)
    run(python, "scripts/generate_quantum_dirac_paper.py")
    run(python, "scripts/validate_archived_quantum_dirac_symmetry_qca.py")

    build_dir = ROOT / "build" / "quantum_dirac_paper"
    build_dir.mkdir(parents=True, exist_ok=True)
    final_dir = ROOT / "output" / "pdf"
    final_dir.mkdir(parents=True, exist_ok=True)
    audit_result = run(python, "scripts/audit_direct_qca_pi_sector.py", capture=True)
    audit_payload = json.loads(audit_result.stdout)
    if audit_payload.get("status") != "post_result_pi_sector_defect_reproduced":
        raise RuntimeError("direct-QCA pi-sector audit returned an unexpected status")
    audit_path = final_dir / f"{TECHNICAL_STEM}.pi_sector_audit.json"
    audit_path.write_text(json.dumps(audit_payload, indent=2, sort_keys=True) + "\n")
    print(audit_result.stdout, end="")

    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print(
            "Figures, tables, archived evidence, and the pi-sector audit validated; "
            "latexmk is unavailable, so technical and lay PDF compilation was skipped."
        )
        return 0
    artifacts = [
        {
            "source": ROOT / "quantum_dirac_paper/main.tex",
            "built_pdf": build_dir / "main.pdf",
            "stem": TECHNICAL_STEM,
            "label": "Quantum-Dirac technical paper",
            "inputs": [
                ROOT / "quantum_dirac_paper/main.tex",
                *sorted((ROOT / "quantum_dirac_paper/sections").glob("*.tex")),
                ROOT / "quantum_dirac_paper/generated/figure_manifest.json",
                ROOT / "quantum_dirac_paper/generated/results.tex",
            ],
        },
        {
            "source": ROOT / "quantum_dirac_paper/lay_main.tex",
            "built_pdf": build_dir / "lay_main.pdf",
            "stem": LAY_STEM,
            "label": "Quantum-Dirac lay companion",
            "inputs": [
                ROOT / "quantum_dirac_paper/lay_main.tex",
                ROOT / "quantum_dirac_paper/generated/results.tex",
            ],
        },
    ]
    for artifact in artifacts:
        source_path = artifact["source"]
        run(
            latexmk,
            "-g",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-outdir=build/quantum_dirac_paper",
            str(source_path.relative_to(ROOT)),
        )
        final_path = final_dir / f"{artifact['stem']}.pdf"
        shutil.copy2(artifact["built_pdf"], final_path)
        digest_path, manifest_path = write_build_manifest(
            final_path,
            artifact["stem"],
            artifact["inputs"],
            audit_path,
            source_date_epoch,
            python_versions,
        )
        print(f"{artifact['label']} built: {final_path.relative_to(ROOT)}")
        print(f"SHA-256: {digest_path.relative_to(ROOT)}")
        print(f"Build manifest: {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
