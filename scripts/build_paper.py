from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from evidence_common import ROOT
from validate_iota_submission import (
    MANIFEST_PATH,
    PDF_CHECKSUM_PATH,
    PDF_PATH,
    SOURCE_ZIP_CHECKSUM_PATH,
    SOURCE_ZIP_PATH,
    curated_source_paths,
)


def run(*args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(args, cwd=ROOT, check=True, env=env)


def capture(*args: str) -> str:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return completed.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_date_epoch() -> int:
    configured = os.environ.get("SOURCE_DATE_EPOCH")
    if configured is not None:
        try:
            epoch = int(configured)
        except ValueError as exc:
            raise ValueError("SOURCE_DATE_EPOCH must be an integer") from exc
        if epoch < 0:
            raise ValueError("SOURCE_DATE_EPOCH must be non-negative")
        return epoch

    try:
        return int(capture("git", "show", "-s", "--format=%ct", "HEAD"))
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        # A fixed fallback keeps source archives reproducible outside a Git checkout.
        return 315532800  # 1980-01-01T00:00:00Z, the ZIP timestamp floor.


def write_checksum(path: Path, checksum_path: Path) -> None:
    relative = path.relative_to(ROOT).as_posix()
    checksum_path.write_text(f"{sha256(path)}  {relative}\n", encoding="utf-8")


def zip_timestamp(epoch: int) -> tuple[int, int, int, int, int, int]:
    # ZIP stores local timestamps from 1980 through 2107 at two-second resolution.
    floor = 315532800
    ceiling = 4354819198
    stamp = datetime.fromtimestamp(min(max(epoch, floor), ceiling), tz=timezone.utc)
    return (
        stamp.year,
        stamp.month,
        stamp.day,
        stamp.hour,
        stamp.minute,
        stamp.second // 2 * 2,
    )


def build_source_zip(path: Path, sources: list[Path], epoch: int) -> None:
    timestamp = zip_timestamp(epoch)
    with zipfile.ZipFile(
        path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for source in sources:
            relative = source.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                source.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def first_line(*args: str) -> str:
    try:
        output = capture(*args)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unavailable"
    return output.splitlines()[0] if output else "unavailable"


def git_metadata() -> dict[str, object]:
    try:
        commit = capture("git", "rev-parse", "HEAD")
        dirty = bool(capture("git", "status", "--porcelain", "--untracked-files=no"))
    except (FileNotFoundError, subprocess.CalledProcessError):
        commit = "unavailable"
        dirty = None
    return {"commit": commit, "tracked_files_dirty": dirty}


def build_manifest(
    sources: list[Path], epoch: int, git: dict[str, object]
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "package": "IOTA BioSystems full-length article",
        "source_date_epoch": epoch,
        "source_date_utc": datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "git": git,
        "pdf": {
            "path": PDF_PATH.relative_to(ROOT).as_posix(),
            "bytes": PDF_PATH.stat().st_size,
            "sha256": sha256(PDF_PATH),
        },
        "source_archive": {
            "path": SOURCE_ZIP_PATH.relative_to(ROOT).as_posix(),
            "bytes": SOURCE_ZIP_PATH.stat().st_size,
            "sha256": sha256(SOURCE_ZIP_PATH),
        },
        "inputs": {
            source.relative_to(ROOT).as_posix(): {
                "bytes": source.stat().st_size,
                "sha256": sha256(source),
            }
            for source in sources
        },
        "toolchain": {
            "python": platform.python_version(),
            "latexmk": first_line("latexmk", "-v"),
            "pdflatex": first_line("pdflatex", "--version"),
        },
    }


def main() -> int:
    epoch = source_date_epoch()
    build_env = os.environ.copy()
    build_env.update(
        {
            "FORCE_SOURCE_DATE": "1",
            "SOURCE_DATE_EPOCH": str(epoch),
            "TZ": "UTC",
        }
    )

    run(sys.executable, "scripts/build_evidence.py")
    run(sys.executable, "scripts/validate_evidence.py")
    run(sys.executable, "scripts/validate_iota_submission.py")

    latexmk = shutil.which("latexmk")
    if latexmk is None:
        print("ERROR: latexmk is required to build the BioSystems submission PDF.", file=sys.stderr)
        return 2

    build_dir = ROOT / "build" / "paper"
    build_dir.mkdir(parents=True, exist_ok=True)
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)

    git = git_metadata()
    run(
        latexmk,
        "-pdf",
        "-g",
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-outdir=build/paper",
        "paper/main.tex",
        env=build_env,
    )

    compiled_pdf = build_dir / "main.pdf"
    if not compiled_pdf.is_file():
        print(f"ERROR: expected compiled PDF was not created: {compiled_pdf}", file=sys.stderr)
        return 2
    shutil.copyfile(compiled_pdf, PDF_PATH)
    os.utime(PDF_PATH, (epoch, epoch))
    write_checksum(PDF_PATH, PDF_CHECKSUM_PATH)

    sources = curated_source_paths()
    build_source_zip(SOURCE_ZIP_PATH, sources, epoch)
    os.utime(SOURCE_ZIP_PATH, (epoch, epoch))
    write_checksum(SOURCE_ZIP_PATH, SOURCE_ZIP_CHECKSUM_PATH)

    manifest = build_manifest(sources, epoch, git)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    run(sys.executable, "scripts/validate_iota_submission.py", "--artifacts")
    print(f"BioSystems PDF: {PDF_PATH.relative_to(ROOT)}")
    print(f"Source archive: {SOURCE_ZIP_PATH.relative_to(ROOT)}")
    print(f"Build manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
