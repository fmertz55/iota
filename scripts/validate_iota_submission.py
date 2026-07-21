from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_DIR = ROOT / "submission" / "biosystems"
PDF_PATH = ROOT / "output" / "pdf" / "iota_constraint_transport_biosystems.pdf"
PDF_CHECKSUM_PATH = PDF_PATH.with_name(PDF_PATH.name + ".sha256")
MANIFEST_PATH = PDF_PATH.with_name("iota_constraint_transport_biosystems.build.json")
SOURCE_ZIP_PATH = (
    ROOT / "output" / "submission" / "iota_constraint_transport_biosystems_sources.zip"
)
SOURCE_ZIP_CHECKSUM_PATH = SOURCE_ZIP_PATH.with_name(
    SOURCE_ZIP_PATH.name + ".sha256"
)
LATEX_LOG_PATH = ROOT / "build" / "paper" / "main.log"

CURATED_EXACT_PATHS = (
    "paper/main.tex",
    "paper/bibliography.bib",
    "submission/biosystems/README.md",
    "submission/biosystems/highlights.txt",
    "submission/biosystems/cover_letter.md",
    "submission/biosystems/checklist.md",
)
CURATED_GLOBS = (
    "paper/generated/*.tex",
    "paper/generated/tables/*.tex",
    "paper/sections/*.tex",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def curated_source_paths() -> list[Path]:
    paths = {ROOT / relative for relative in CURATED_EXACT_PATHS}
    for pattern in CURATED_GLOBS:
        paths.update(ROOT.glob(pattern))
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def strip_tex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        for index, character in enumerate(line):
            if character != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                line = line[:index]
                break
        lines.append(line)
    return "\n".join(lines)


def tex_word_count(text: str) -> int:
    text = re.sub(r"\$[^$]*\$", " ", text, flags=re.DOTALL)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\s*\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ").replace("~", " ")
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def manuscript_tex_paths() -> list[Path]:
    paths = [ROOT / "paper" / "main.tex"]
    paths.extend(sorted((ROOT / "paper" / "sections").glob("*.tex")))
    paths.extend(sorted((ROOT / "paper" / "generated").glob("*.tex")))
    paths.extend(sorted((ROOT / "paper" / "generated" / "tables").glob("*.tex")))
    return paths


def validate_tex_dependencies(start: Path) -> list[str]:
    failures: list[str] = []
    pending = [start]
    visited: set[Path] = set()
    input_pattern = re.compile(r"\\input\s*\{([^}]+)\}")
    bibliography_pattern = re.compile(r"\\bibliography\s*\{([^}]+)\}")

    while pending:
        path = pending.pop()
        if path in visited:
            continue
        visited.add(path)
        if not path.is_file():
            failures.append(f"missing TeX dependency: {path.relative_to(ROOT)}")
            continue
        source = strip_tex_comments(path.read_text(encoding="utf-8"))
        for match in input_pattern.finditer(source):
            dependency = ROOT / match.group(1)
            if dependency.suffix == "":
                dependency = dependency.with_suffix(".tex")
            if not dependency.is_file():
                failures.append(
                    f"{path.relative_to(ROOT)} references missing input {dependency.relative_to(ROOT)}"
                )
            else:
                pending.append(dependency)
        for match in bibliography_pattern.finditer(source):
            for name in match.group(1).split(","):
                dependency = ROOT / name.strip()
                if dependency.suffix == "":
                    dependency = dependency.with_suffix(".bib")
                if not dependency.is_file():
                    failures.append(
                        f"{path.relative_to(ROOT)} references missing bibliography "
                        f"{dependency.relative_to(ROOT)}"
                    )
    return failures


def validate_source() -> tuple[list[str], dict[str, object]]:
    failures: list[str] = []
    details: dict[str, object] = {}
    sources = curated_source_paths()
    missing = [path for path in sources if not path.is_file()]
    failures.extend(
        f"missing curated source: {path.relative_to(ROOT)}" for path in missing
    )

    main_path = ROOT / "paper" / "main.tex"
    if not main_path.is_file():
        failures.append("missing manuscript: paper/main.tex")
        return failures, details

    failures.extend(validate_tex_dependencies(main_path))
    main = strip_tex_comments(main_path.read_text(encoding="utf-8"))

    abstract_match = re.search(
        r"\\begin\s*\{abstract\}(.*?)\\end\s*\{abstract\}",
        main,
        flags=re.DOTALL,
    )
    if abstract_match is None:
        failures.append("paper/main.tex has no abstract environment")
    else:
        abstract_words = tex_word_count(abstract_match.group(1))
        details["abstract_words"] = abstract_words
        if not 1 <= abstract_words <= 250:
            failures.append(
                f"abstract has {abstract_words} words; BioSystems maximum is 250"
            )

    keywords_match = re.search(
        r"\\textbf\s*\{Keywords:\}(.*?)(?:\\linenumbers|\n\s*\n)",
        main,
        flags=re.DOTALL,
    )
    if keywords_match is None:
        failures.append("paper/main.tex has no Keywords field")
    else:
        keywords_text = re.sub(r"\s+", " ", keywords_match.group(1)).strip()
        keywords = [item.strip() for item in keywords_text.split(";") if item.strip()]
        details["keywords"] = keywords
        if not 1 <= len(keywords) <= 7:
            failures.append(
                f"manuscript has {len(keywords)} keywords; BioSystems permits 1--7"
            )

    includegraphics = re.compile(r"\\includegraphics\*?(?:\s*\[[^\]]*\])?\s*\{")
    figure_hits: list[str] = []
    for path in manuscript_tex_paths():
        if not path.is_file():
            continue
        source = strip_tex_comments(path.read_text(encoding="utf-8"))
        if includegraphics.search(source):
            figure_hits.append(path.relative_to(ROOT).as_posix())
    details["includegraphics_files"] = figure_hits
    if figure_hits:
        failures.append(
            "BioSystems manuscript must remain figure-free; \\includegraphics found in "
            + ", ".join(figure_hits)
        )

    combined_source = "\n".join(
        strip_tex_comments(path.read_text(encoding="utf-8"))
        for path in manuscript_tex_paths()
        if path.is_file()
    )
    if re.search(r"working\s+draft", combined_source, flags=re.IGNORECASE):
        failures.append("manuscript still contains a 'working draft' label")

    labels = re.findall(r"\\label\s*\{([^}]+)\}", combined_source)
    label_counts = {label: labels.count(label) for label in set(labels)}
    duplicate_labels = sorted(
        label for label, count in label_counts.items() if count > 1
    )
    if duplicate_labels:
        failures.append("duplicate TeX labels: " + ", ".join(duplicate_labels))

    reference_groups = re.findall(
        r"\\(?:ref|pageref|eqref|autoref|cref|Cref|vref|Vref)\*?"
        r"(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}",
        combined_source,
    )
    references = {
        label.strip()
        for group in reference_groups
        for label in group.split(",")
        if label.strip()
    }
    unresolved_references = sorted(references - set(labels))
    if unresolved_references:
        failures.append("unresolved TeX references: " + ", ".join(unresolved_references))
    unreferenced_tables = sorted(
        label
        for label in labels
        if label.startswith("tab:") and label not in references
    )
    details["table_labels"] = sorted(
        label for label in labels if label.startswith("tab:")
    )
    if unreferenced_tables:
        failures.append(
            "table labels without a manuscript callout: "
            + ", ".join(unreferenced_tables)
        )

    citation_groups = re.findall(
        r"\\cite[A-Za-z]*\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]+)\}",
        combined_source,
    )
    citation_keys = {
        key.strip()
        for group in citation_groups
        for key in group.split(",")
        if key.strip()
    }
    bibliography_path = ROOT / "paper" / "bibliography.bib"
    if bibliography_path.is_file():
        bibliography = strip_tex_comments(bibliography_path.read_text(encoding="utf-8"))
        bibliography_keys = set(
            re.findall(r"@[A-Za-z]+\s*\{\s*([^,\s]+)\s*,", bibliography)
        )
        unresolved_citations = sorted(citation_keys - bibliography_keys)
        details["citation_keys"] = sorted(citation_keys)
        if unresolved_citations:
            failures.append(
                "citation keys absent from bibliography: "
                + ", ".join(unresolved_citations)
            )

    placeholder_paths = manuscript_tex_paths() + [
        SUBMISSION_DIR / "cover_letter.md",
        SUBMISSION_DIR / "highlights.txt",
    ]
    placeholder_patterns = (
        (
            "TODO/TBD marker",
            re.compile(r"\b(?:TODO|TBD|FIXME|PLACEHOLDER|TK)\b", re.IGNORECASE),
        ),
        ("double-bracket token", re.compile(r"\[\[[^\]]+\]\]")),
        (
            "double-brace token",
            re.compile(
                r"\{\{\s*(?:TODO|TBD|INSERT|REPLACE|[A-Z][A-Z0-9_ -]{2,})\s*\}\}"
            ),
        ),
        (
            "named bracket token",
            re.compile(
                r"\[(?:DATE|EDITOR|AFFILIATION|ADDRESS|PHONE|EMAIL|DOI|INSERT[^\]]*)\]",
                re.IGNORECASE,
            ),
        ),
        (
            "angle-bracket token",
            re.compile(r"<(?:insert|replace|todo)[^>]*>", re.IGNORECASE),
        ),
        (
            "unresolved archive instruction",
            re.compile(
                r"\bshould(?:\s+\w+){0,2}\s+be\s+(?:minted|deposited)\b",
                re.IGNORECASE,
            ),
        ),
    )
    placeholder_hits: list[str] = []
    for path in placeholder_paths:
        if not path.is_file():
            continue
        text = strip_tex_comments(path.read_text(encoding="utf-8"))
        for description, pattern in placeholder_patterns:
            if pattern.search(text):
                placeholder_hits.append(f"{path.relative_to(ROOT)} ({description})")
    details["placeholder_hits"] = placeholder_hits
    if placeholder_hits:
        failures.append("unresolved submission placeholders: " + ", ".join(placeholder_hits))

    highlights_path = SUBMISSION_DIR / "highlights.txt"
    if highlights_path.is_file():
        raw_lines = [
            line.strip()
            for line in highlights_path.read_text(encoding="utf-8").splitlines()
        ]
        nonempty = [line for line in raw_lines if line]
        malformed = [line for line in nonempty if not line.startswith("- ")]
        highlights = [line[2:].strip() for line in nonempty if line.startswith("- ")]
        details["highlight_lengths"] = [len(item) for item in highlights]
        if malformed:
            failures.append("highlights.txt must contain only '- ' bullet lines")
        if not 3 <= len(highlights) <= 5:
            failures.append(
                f"highlights.txt has {len(highlights)} highlights; "
                "BioSystems requires 3--5"
            )
        for index, highlight in enumerate(highlights, start=1):
            if len(highlight) > 85:
                failures.append(
                    f"highlight {index} has {len(highlight)} characters; BioSystems maximum is 85"
                )
    else:
        failures.append("missing submission/biosystems/highlights.txt")

    for name in ("README.md", "cover_letter.md", "checklist.md"):
        path = SUBMISSION_DIR / name
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            failures.append(f"missing or empty submission/biosystems/{name}")

    details["curated_sources"] = [path.relative_to(ROOT).as_posix() for path in sources]
    return failures, details


def read_checksum(checksum_path: Path, target: Path) -> str | None:
    if not checksum_path.is_file():
        return None
    fields = checksum_path.read_text(encoding="utf-8").strip().split()
    if len(fields) < 2:
        return None
    expected_name = target.relative_to(ROOT).as_posix()
    if fields[1].lstrip("*") != expected_name:
        return None
    return fields[0]


def validate_artifacts() -> list[str]:
    failures: list[str] = []
    required = (
        PDF_PATH,
        PDF_CHECKSUM_PATH,
        MANIFEST_PATH,
        SOURCE_ZIP_PATH,
        SOURCE_ZIP_CHECKSUM_PATH,
    )
    for path in required:
        if not path.is_file():
            failures.append(f"missing build artifact: {path.relative_to(ROOT)}")
    if failures:
        return failures

    if not PDF_PATH.read_bytes().startswith(b"%PDF-"):
        failures.append("stable PDF does not have a PDF header")

    if not LATEX_LOG_PATH.is_file():
        failures.append("missing LaTeX build log: build/paper/main.log")
    else:
        latex_log = LATEX_LOG_PATH.read_text(encoding="utf-8", errors="replace")
        unresolved_patterns = (
            r"Citation [`'][^\n]+ undefined",
            r"Reference [`'][^\n]+ undefined",
            r"There were undefined citations",
            r"There were undefined references",
        )
        if any(
            re.search(pattern, latex_log, flags=re.IGNORECASE)
            for pattern in unresolved_patterns
        ):
            failures.append("LaTeX build log contains unresolved citations or references")
        if re.search(r"Overfull \\[hv]box", latex_log):
            failures.append("LaTeX build log contains an overfull box")

    for target, checksum_path in (
        (PDF_PATH, PDF_CHECKSUM_PATH),
        (SOURCE_ZIP_PATH, SOURCE_ZIP_CHECKSUM_PATH),
    ):
        recorded = read_checksum(checksum_path, target)
        if recorded is None:
            failures.append(f"malformed checksum file: {checksum_path.relative_to(ROOT)}")
        elif recorded != sha256(target):
            failures.append(f"checksum mismatch: {target.relative_to(ROOT)}")

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        failures.append(f"invalid build manifest JSON: {exc}")
        return failures

    if manifest.get("schema_version") != 1:
        failures.append("build manifest schema_version must be 1")
    for key, target in (("pdf", PDF_PATH), ("source_archive", SOURCE_ZIP_PATH)):
        record = manifest.get(key)
        if not isinstance(record, dict):
            failures.append(f"build manifest has no {key} record")
            continue
        relative = target.relative_to(ROOT).as_posix()
        if record.get("path") != relative:
            failures.append(f"build manifest {key} path mismatch")
        if record.get("bytes") != target.stat().st_size:
            failures.append(f"build manifest {key} byte count mismatch")
        if record.get("sha256") != sha256(target):
            failures.append(f"build manifest {key} digest mismatch")

    sources = curated_source_paths()
    expected_names = [path.relative_to(ROOT).as_posix() for path in sources]
    input_records = manifest.get("inputs")
    if not isinstance(input_records, dict) or sorted(input_records) != expected_names:
        failures.append("build manifest input list does not match curated source list")
    else:
        for source in sources:
            relative = source.relative_to(ROOT).as_posix()
            record = input_records.get(relative)
            if not isinstance(record, dict):
                failures.append(f"build manifest input record is invalid: {relative}")
                continue
            if record.get("bytes") != source.stat().st_size or record.get(
                "sha256"
            ) != sha256(source):
                failures.append(f"build manifest input digest mismatch: {relative}")

    try:
        with zipfile.ZipFile(SOURCE_ZIP_PATH) as archive:
            members = archive.infolist()
            member_names = [member.filename for member in members]
            if member_names != expected_names:
                failures.append("source ZIP member list/order does not match curated source list")
            if len(member_names) != len(set(member_names)):
                failures.append("source ZIP contains duplicate member names")
            source_epoch = manifest.get("source_date_epoch")
            expected_zip_time: tuple[int, int, int, int, int, int] | None = None
            if isinstance(source_epoch, int):
                stamp = datetime.fromtimestamp(
                    min(max(source_epoch, 315532800), 4354819198),
                    tz=timezone.utc,
                )
                expected_zip_time = (
                    stamp.year,
                    stamp.month,
                    stamp.day,
                    stamp.hour,
                    stamp.minute,
                    stamp.second // 2 * 2,
                )
            else:
                failures.append("build manifest source_date_epoch must be an integer")
            for member in members:
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    failures.append(f"source ZIP contains unsafe member: {member.filename}")
                    continue
                source = ROOT / member.filename
                if source.is_file() and sha256_bytes(archive.read(member)) != sha256(
                    source
                ):
                    failures.append(f"source ZIP content mismatch: {member.filename}")
                if member.compress_type != zipfile.ZIP_DEFLATED:
                    failures.append(f"source ZIP member is not deflated: {member.filename}")
                if (
                    member.create_system != 3
                    or (member.external_attr >> 16) & 0o777 != 0o644
                ):
                    failures.append(f"source ZIP member mode is not 0644: {member.filename}")
                if expected_zip_time is not None and member.date_time != expected_zip_time:
                    failures.append(f"source ZIP timestamp mismatch: {member.filename}")
    except (OSError, zipfile.BadZipFile) as exc:
        failures.append(f"invalid source ZIP: {exc}")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the IOTA BioSystems submission package."
    )
    parser.add_argument(
        "--artifacts",
        action="store_true",
        help="also require and verify the built PDF, checksums, manifest, and source ZIP",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures, details = validate_source()
    if args.artifacts:
        failures.extend(validate_artifacts())

    if failures:
        for failure in failures:
            print(f"FAIL iota submission validation: {failure}", file=sys.stderr)
        return 2

    print(
        "PASS iota submission validation: "
        f"abstract_words={details.get('abstract_words')}, "
        f"keywords={len(details.get('keywords', []))}, "
        f"highlights={len(details.get('highlight_lengths', []))}, "
        "includegraphics=0"
    )
    if args.artifacts:
        print("PASS iota submission artifacts: PDF, checksums, manifest, and source ZIP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
