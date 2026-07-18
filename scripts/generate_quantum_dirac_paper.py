from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "quantum_dirac_paper"
FIGURE_DIR = PAPER / "figures" / "generated"
GENERATED_DIR = PAPER / "generated"

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402


NAVY = "#17324D"
BLUE = "#2F6690"
TEAL = "#168AAD"
ORANGE = "#D97706"
RED = "#A23E48"
GREEN = "#2A7F62"
INK = "#172026"
MID = "#5A6772"
LIGHT = "#E8EEF2"
PALE_BLUE = "#E8F1F7"
PALE_ORANGE = "#FFF1DD"
PALE_GREEN = "#E7F3EE"
PALE_RED = "#F8E7E9"


@dataclass(frozen=True)
class LedgerSpec:
    key: str
    architecture: str
    partition: str
    path: str
    sha256: str


@dataclass(frozen=True)
class RegisteredSpec:
    key: str
    architecture: str
    kind: str
    path: str
    sha256: str


LEDGER_SPECS = (
    LedgerSpec(
        "product_development",
        "Product walk",
        "Development",
        "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/development_results_v0.4.json",
        "c9f445358a7ada5d8d20208c485529e6c6da93768f2ee1c9dea76afed2baab7b",
    ),
    LedgerSpec(
        "product_confirmation",
        "Product walk",
        "Confirmation",
        "output/quantum_dirac/ICP-QUANTUM-DIRAC-ROLE-RECOVERY-001/confirmation_results_v0.4.json",
        "34c16fd959148d99a5e32c4836d69acb33794d548c11c8ac83986990742fac72",
    ),
    LedgerSpec(
        "direct_development",
        "Direct QCA",
        "Development",
        "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/development_results_v0.4.json",
        "89d7c65a37bf8d38fea3a87b7f656c02cae57664fcf6b53b725fb8ace7c228c4",
    ),
    LedgerSpec(
        "direct_confirmation",
        "Direct QCA",
        "Confirmation",
        "output/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/confirmation_results_v0.4.json",
        "be5a9f85770e1d201abbc269c26da25d821f11f67db364c434473b5c70517e65",
    ),
)


REGISTERED_SPECS = (
    RegisteredSpec(
        "product_scenarios",
        "Product walk",
        "scenario schedule",
        "specs/icp_quantum_dirac_role_recovery/v0.1-draft/scenarios.json",
        "2d583d01c356f688a8250c5137dc8b6aae646c7bfda7369d468dd13b298a7e83",
    ),
    RegisteredSpec(
        "product_states",
        "Product walk",
        "state parameters",
        "specs/icp_quantum_dirac_role_recovery/v0.1-draft/states.json",
        "c1d06069aae873bbd042c013e6a9fb7acbb7a24267eb07a3f5c1ce905fafbe86",
    ),
    RegisteredSpec(
        "direct_scenarios",
        "Direct QCA",
        "scenario schedule",
        "specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/scenarios.json",
        "f9d00c739f76ecda0081283e9349afabfc2fdadfb01e8123ec835639a699452a",
    ),
    RegisteredSpec(
        "direct_states",
        "Direct QCA",
        "state parameters",
        "specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/states.json",
        "bda3155d4fd9401b1eb26763647c3a4de68ac92a90076e93bd4d50eb681bdbcc",
    ),
)


ANALYTIC_SOURCE_PATHS = (
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/LOCALIZATION_AUDIT.md",
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/CONTINUUM_AUDIT.md",
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/GLOBAL_SPECTRUM_AUDIT.md",
    "experiments/quantum_dirac/ICP-QUANTUM-DIRAC-SYMMETRY-QCA-001/POST_RESULT_AUDIT.md",
)


SCENARIO_LABELS = {
    "DEV-FREE-LIGHT": "free light",
    "DEV-FREE-HEAVY": "free heavy",
    "DEV-QUENCH-UP": "mass quench",
    "DEV-POTENTIAL-EVEN": "potential even",
    "HOLDOUT-QUENCH-DOWN": "holdout quench",
    "HOLDOUT-POTENTIAL-ODD": "holdout potential",
    "DEV-DIRECT-FREE-POS": "free positive",
    "DEV-DIRECT-FREE-NEG": "free negative",
    "DEV-DIRECT-SIGN-QUENCH": "sign quench",
    "DEV-DIRECT-POTENTIAL-H2": "potential H2",
    "HOLDOUT-DIRECT-MASS-PULSE": "holdout pulse",
    "HOLDOUT-DIRECT-POTENTIAL-H3": "holdout potential H3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_ledgers() -> dict[str, dict[str, Any]]:
    ledgers: dict[str, dict[str, Any]] = {}
    for spec in LEDGER_SPECS:
        path = ROOT / spec.path
        actual = sha256(path)
        if actual != spec.sha256:
            raise RuntimeError(
                f"Content-addressed ledger hash mismatch for {spec.path}: expected {spec.sha256}, got {actual}"
            )
        ledgers[spec.key] = json.loads(path.read_text())
    expected_status = {
        "product_development": "development_passed",
        "product_confirmation": "constructive_sufficiency_passed_frozen_dirac_sector",
        "direct_development": "development_passed",
        "direct_confirmation": "constructive_sufficiency_passed_direct_symmetry_qca_sector",
    }
    for key, status in expected_status.items():
        if ledgers[key]["status"] != status:
            raise RuntimeError(f"Unexpected terminal status for {key}: {ledgers[key]['status']}")
    return ledgers


def load_registered_specs() -> dict[str, dict[str, Any]]:
    registered: dict[str, dict[str, Any]] = {}
    for spec in REGISTERED_SPECS:
        path = ROOT / spec.path
        actual = sha256(path)
        if actual != spec.sha256:
            raise RuntimeError(
                f"Frozen {spec.kind} hash mismatch for {spec.path}: "
                f"expected {spec.sha256}, got {actual}"
            )
        registered[spec.key] = json.loads(path.read_text())
    return registered


def refinement_distance(refinement: dict[str, Any]) -> Decimal:
    value = refinement.get("scenario_max_upper", refinement.get("scenario_distance_upper"))
    if value is None:
        raise KeyError("No scenario-level certified distance in refinement record")
    return Decimal(value)


def scenario_series(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in ledger["scenario_results"]:
        refinements = scenario["operator"]["refinements"]
        rows.append(
            {
                "id": scenario["scenario_id"],
                "class": scenario.get("scenario_class", "product"),
                "n": [int(item["n_sites"]) for item in refinements],
                "delta": [Decimal(16) / Decimal(item["n_sites"]) for item in refinements],
                "distance": [refinement_distance(item) for item in refinements],
                "threshold": [Decimal(item["absolute_threshold"]) for item in refinements],
            }
        )
    return rows


def product_observation_values(witness: dict[str, Any], metric: str) -> Iterable[Decimal]:
    for observation in witness["observations"]:
        if metric in observation:
            yield Decimal(observation[metric])


def witness_maxima(ledgers: Iterable[dict[str, Any]], direct: bool) -> dict[str, Decimal]:
    names = {
        "position_tv": "position_tv_max" if direct else "position_tv_upper",
        "momentum_tv": "momentum_tv_max" if direct else "momentum_tv_upper",
        "total_current": "total_current_error_max" if direct else "total_current_error_upper",
        "local_current": "local_current_l1_max" if direct else "local_current_l1_upper",
        "infidelity": "infidelity_max" if direct else "infidelity_upper",
    }
    values: dict[str, list[Decimal]] = {key: [] for key in names}
    values["zitter"] = []
    for ledger in ledgers:
        for scenario in ledger["scenario_results"]:
            for witness in scenario["witnesses"]:
                if direct:
                    for label, field in names.items():
                        if witness.get(field) is not None:
                            values[label].append(Decimal(witness[field]))
                    if witness.get("zitter_current_series_sup_error") is not None:
                        values["zitter"].append(Decimal(witness["zitter_current_series_sup_error"]))
                else:
                    for label, field in names.items():
                        values[label].extend(product_observation_values(witness, field))
                    if witness.get("zitter_sup_error_upper") is not None:
                        values["zitter"].append(Decimal(witness["zitter_sup_error_upper"]))
    return {label: max(entries) for label, entries in values.items() if entries}


def operator_max(ledgers: Iterable[dict[str, Any]], refinement_index: int | None = None) -> Decimal:
    values: list[Decimal] = []
    for ledger in ledgers:
        for row in scenario_series(ledger):
            distances = row["distance"]
            values.extend(distances if refinement_index is None else [distances[refinement_index]])
    return max(values)


def independent_state_max(ledgers: Iterable[dict[str, Any]]) -> Decimal:
    values = [
        Decimal(scenario["maximum_independent_state_disagreement_upper"])
        for ledger in ledgers
        for scenario in ledger["scenario_results"]
    ]
    return max(values)


def fmt(value: Decimal, digits: int = 7) -> str:
    if value == 0:
        return "0"
    return f"{value:.{digits}g}"


def tex_sci(value: Decimal, digits: int = 6) -> str:
    if value == 0:
        return "0"
    exponent = value.adjusted()
    if -3 <= exponent <= 1:
        return f"{value:.{digits}g}"
    coefficient = value.scaleb(-exponent)
    return rf"{coefficient:.{digits - 1}g}\times 10^{{{exponent}}}"


def tex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def tex_identifier(text: str) -> str:
    return r"\texttt{" + tex_escape(text).replace("-", r"-\allowbreak{}") + "}"


def tex_exact(value: str | int) -> str:
    text = str(value)
    integer = re.fullmatch(r"(-?)(\d+)", text)
    if integer:
        return text
    fraction = re.fullmatch(r"(-?)(\d+)/(\d+)", text)
    if fraction:
        sign, numerator, denominator = fraction.groups()
        return rf"{sign}\tfrac{{{numerator}}}{{{denominator}}}"
    pi_value = re.fullmatch(r"(-?)(\d*)pi(?:/(\d+))?", text)
    if pi_value:
        sign, coefficient, denominator = pi_value.groups()
        numerator = (coefficient if coefficient else "") + r"\pi"
        return rf"{sign}\tfrac{{{numerator}}}{{{denominator}}}" if denominator else f"{sign}{numerator}"
    raise ValueError(f"Unsupported exact registered value: {value!r}")


def schedule_interval(start: str | int, end: str | int) -> str:
    return rf"[{tex_exact(start)},{tex_exact(end)})"


def mass_schedule(segments: list[list[str | int]]) -> str:
    entries = [
        rf"{tex_exact(value)}\;{schedule_interval(start, end)}"
        for start, end, value in segments
    ]
    return r"$" + r";\;".join(entries) + r"$"


def potential_schedule(segments: list[list[str | int]], direct: bool) -> str:
    if not segments:
        return "$0$"
    entries = []
    for segment in segments:
        if direct:
            start, end, harmonic, amplitude, phase = segment
        else:
            start, end, amplitude, phase = segment
            harmonic = 1
        entries.append(
            rf"({tex_exact(harmonic)},{tex_exact(amplitude)},{tex_exact(phase)};"
            rf"{schedule_interval(start, end)})"
        )
    return r"$" + r";\;".join(entries) + r"$"


def state_parameters(state: dict[str, Any]) -> str:
    state_type = state["type"]
    if state_type == "positive_interference":
        first, second = state["packets"]
        first_values = ",".join(tex_exact(value) for value in first)
        second_values = ",".join(tex_exact(value) for value in second)
        phase = tex_exact(state["relative_phase"])
        return rf"$p_1=({first_values});\ p_2=({second_values});\ \phi={phase}$"
    values = ",".join(tex_exact(state[key]) for key in ("r0", "width", "x0"))
    if state_type == "energy_mixture":
        phase = tex_exact(state["relative_phase"])
        return rf"$p=({values});\ \phi={phase}$"
    return rf"$p=({values})$"


def write_registered_protocol_tables(registered: dict[str, dict[str, Any]]) -> None:
    scenario_lines = [
        r"% Generated from four hash-verified frozen specification files.",
        r"\begin{tabularx}{\linewidth}{@{}p{0.10\linewidth}p{0.29\linewidth}X X@{}}",
        r"\toprule",
        r"Update / split & Registered scenario & $m$: value and interval & $V$: $(h,a,\phi;[t_0,t_1))$ \\",
        r"\midrule",
    ]
    for key, update, direct in (
        ("product_scenarios", "PW", False),
        ("direct_scenarios", "DQCA", True),
    ):
        specification = registered[key]
        for partition, split in (("development", "dev."), ("confirmation", "conf.")):
            for scenario in specification[partition]:
                scenario_lines.append(
                    f"{update} / {split} & {tex_identifier(scenario['id'])} & "
                    f"{mass_schedule(scenario['mass'])} & "
                    f"{potential_schedule(scenario['potential'], direct)} \\\\"
                )
    scenario_lines += [r"\bottomrule", r"\end{tabularx}"]
    (GENERATED_DIR / "tables" / "registered_scenarios.tex").write_text(
        "\n".join(scenario_lines) + "\n"
    )

    state_lines = [
        r"% Generated from four hash-verified frozen specification files.",
        r"\begin{tabularx}{\linewidth}{@{}p{0.10\linewidth}p{0.32\linewidth}p{0.19\linewidth}X@{}}",
        r"\toprule",
        r"Update / split & Registered state & Type & Exact parameters \\",
        r"\midrule",
    ]
    type_labels = {
        "positive": "positive energy",
        "negative": "negative energy",
        "positive_interference": "positive interference",
        "energy_mixture": "energy mixture",
    }
    for key, update in (("product_states", "PW"), ("direct_states", "DQCA")):
        specification = registered[key]
        for partition, split in (("development", "dev."), ("confirmation", "conf.")):
            for state in specification[partition]:
                state_lines.append(
                    f"{update} / {split} & {tex_identifier(state['id'])} & "
                    f"{type_labels[state['type']]} & {state_parameters(state)} \\\\"
                )
    state_lines += [r"\bottomrule", r"\end{tabularx}"]
    (GENERATED_DIR / "tables" / "registered_states.tex").write_text(
        "\n".join(state_lines) + "\n"
    )


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.2,
            "axes.titlesize": 9.2,
            "axes.labelsize": 8.4,
            "xtick.labelsize": 7.4,
            "ytick.labelsize": 7.4,
            "legend.fontsize": 6.8,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.35,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    face: str = "white",
    edge: str = NAVY,
    linewidth: float = 1.0,
    fontsize: float = 8.0,
    weight: str = "normal",
    linestyle: str = "-",
    hatch: str | None = None,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        linestyle=linestyle,
        hatch=hatch,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, weight=weight, color=INK)
    return patch


def add_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = MID) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=1.0,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    pdf_metadata = {
        "Title": stem,
        "Author": "Douglas Clark",
        "Subject": "Quantum-Dirac manuscript figure",
        "Creator": "scripts/generate_quantum_dirac_paper.py",
        "Producer": f"Matplotlib {matplotlib.__version__}",
        "CreationDate": None,
        "ModDate": None,
    }
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight", metadata=pdf_metadata)
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def figure_construction_map() -> None:
    fig, ax = plt.subplots(figsize=(7.25, 4.25))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.02, 0.965, "A", weight="bold", fontsize=11, color=NAVY)
    ax.text(0.07, 0.96, "Prospective operational comparison", weight="bold", fontsize=10.5, color=INK)

    ax.text(0.09, 0.875, "SUPPLIED", ha="center", weight="bold", color=MID, fontsize=7.6)
    ax.text(0.50, 0.875, "CONSTRUCTED", ha="center", weight="bold", color=MID, fontsize=7.6)
    ax.text(0.88, 0.875, "TESTED", ha="center", weight="bold", color=MID, fontsize=7.6)

    add_box(ax, 0.02, 0.60, 0.18, 0.20, "Bounded target role\n$1+1$D Dirac; $T=2$\n" + r"$|r|\leq4$; one excitation", face=LIGHT, edge=MID, fontsize=7.5)
    add_box(ax, 0.02, 0.32, 0.18, 0.20, "Construction inputs\nperiodic lattice\nlocal clock; two modes\nprecision; fixed maps", face=LIGHT, edge=MID, fontsize=7.4)
    add_box(ax, 0.31, 0.60, 0.38, 0.20, "Product walk\n" + r"phase $\rightarrow$ mass mix $\rightarrow$ two SWAP layers", face=PALE_BLUE, edge=BLUE, weight="bold", fontsize=7.3)
    add_box(ax, 0.31, 0.32, 0.38, 0.20, "Direct symmetry QCA\n" + r"phase $\rightarrow$ edge scatter $\rightarrow$ routing SWAP", face=PALE_ORANGE, edge=ORANGE, weight="bold", fontsize=7.3)
    add_box(ax, 0.79, 0.60, 0.19, 0.20, "Uniform evolution\n18-dimensional input\nthree refinements", face=PALE_GREEN, edge=GREEN, fontsize=7.5)
    add_box(ax, 0.79, 0.32, 0.19, 0.20, "Observable witnesses\ncausality + symmetries\nresources + replay", face=PALE_GREEN, edge=GREEN, fontsize=7.5)

    add_arrow(ax, (0.205, 0.70), (0.305, 0.70), BLUE)
    add_arrow(ax, (0.205, 0.42), (0.305, 0.42), ORANGE)
    add_arrow(ax, (0.695, 0.70), (0.785, 0.70), GREEN)
    add_arrow(ax, (0.695, 0.42), (0.785, 0.42), GREEN)
    ax.text(0.255, 0.725, r"$E,\,\Phi$", ha="center", fontsize=8, color=MID)
    ax.text(0.741, 0.725, "$M$", ha="center", fontsize=8, color=MID)
    ax.text(0.255, 0.445, r"$E,\,\Phi$", ha="center", fontsize=8, color=MID)
    ax.text(0.741, 0.445, "$M$", ha="center", fontsize=8, color=MID)

    y = 0.105
    labels = ["seal", "development", "independent replay", "single-use confirmation", "independent replay"]
    widths = [0.095, 0.135, 0.17, 0.19, 0.17]
    x = 0.035
    for index, (label, width) in enumerate(zip(labels, widths)):
        face = LIGHT if index == 0 else PALE_GREEN
        edge = MID if index == 0 else GREEN
        add_box(ax, x, y, width, 0.095, label, face=face, edge=edge, fontsize=6.9, weight="bold" if index in (2, 4) else "normal")
        if index < len(labels) - 1:
            add_arrow(ax, (x + width + 0.003, y + 0.048), (x + width + 0.027, y + 0.048), MID)
        x += width + 0.035
    ax.text(0.035, 0.235, "Each registration frozen before its own outcomes; confirmation opened once", fontsize=7.25, color=MID)
    save_figure(fig, "fig01_construction_map")


def draw_timeline_panel(
    ax: plt.Axes,
    title: str,
    layers: list[tuple[str, str, str]],
    free_depth: int,
    active_depth: int,
    gate_work: str,
    note: str,
) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.93, title, weight="bold", fontsize=9.3, color=INK)
    ax.text(0.02, 0.855, note, fontsize=7.0, color=MID)
    final_x = 0.79 if len(layers) == 4 else 0.75
    x_positions = np.linspace(0.04, final_x, len(layers))
    y = 0.51
    for index, (label, face, hatch) in enumerate(layers):
        x = float(x_positions[index])
        width = 0.17 if len(layers) == 4 else 0.21
        add_box(ax, x, y, width, 0.18, label, face=face, edge=NAVY, fontsize=7.2, hatch=hatch)
        ax.text(x + width / 2, 0.75, f"layer {index + 1}", ha="center", fontsize=6.6, color=MID)
        if index < len(layers) - 1:
            add_arrow(ax, (x + width + 0.006, y + 0.09), (float(x_positions[index + 1]) - 0.01, y + 0.09), MID)
    ax.add_patch(Rectangle((0.04, 0.33), 0.92, 0.055, facecolor=NAVY, edgecolor="none"))
    ax.text(0.50, 0.357, r"one physical macrostep  $\Delta t=\Delta x$", ha="center", va="center", fontsize=7.2, color="white")
    ax.text(
        0.04,
        0.17,
        f"free depth {free_depth}  |  active depth {active_depth}  |  gate-work {gate_work}  |  storage $2N$  |  ancillas 0  |  radius 1",
        fontsize=7.05,
        color=INK,
    )


def figure_architectures() -> None:
    fig, axes = plt.subplots(2, 1, figsize=(7.25, 5.0))
    fig.subplots_adjust(hspace=0.14)
    fig.text(0.015, 0.975, "B", weight="bold", fontsize=11, color=NAVY)
    draw_timeline_panel(
        axes[0],
        "Product walk: declared ordered decomposition",
        [
            ("potential phase\n(optional)", LIGHT, "//"),
            ("mass mix*", PALE_BLUE, ""),
            ("on-site SWAP", "white", ".."),
            ("directed edge SWAP", "white", "xx"),
        ],
        3,
        4,
        "$3N$ / $4N$",
        r"$U_{\mathrm{PW}}=S\,C_m\,V$; *$C_m$ frozen only at one excitation; $|00\rangle,|11\rangle$ phases unfrozen",
    )
    draw_timeline_panel(
        axes[1],
        "Direct QCA: registered edge-scatter/routing clock",
        [
            ("potential phase\n(optional)", LIGHT, "//"),
            ("edge scatter\n" + r"$nX-i\mu I$", PALE_ORANGE, ""),
            ("routing SWAP", "white", "xx"),
        ],
        2,
        3,
        "$2N$ / $3N$",
        r"$U_{\mathrm{D}}=K^{1/2}C_{\arcsin\mu}K^{1/2}$; registered edge-scatter/routing clock shown",
    )
    save_figure(fig, "fig02_architecture_comparison")


def plot_architecture_convergence(
    ax: plt.Axes,
    rows: list[tuple[dict[str, Any], str]],
    title: str,
    panel: str,
    direct: bool,
) -> None:
    styles = ["-", "--", "-.", ":", (0, (4, 1, 1, 1)), (0, (1, 1))]
    markers = {"Development": "o", "Confirmation": "D"}
    colors = {"Development": BLUE, "Confirmation": ORANGE}
    for index, (row, partition) in enumerate(rows):
        xs = np.array([float(value) for value in row["delta"]])
        ys = np.array([float(value) for value in row["distance"]])
        order = np.argsort(xs)
        ax.loglog(
            xs[order],
            ys[order],
            linestyle=styles[index],
            marker=markers[partition],
            markersize=4.1,
            markerfacecolor="white" if partition == "Development" else colors[partition],
            markeredgewidth=0.8,
            color=colors[partition],
            label=SCENARIO_LABELS[row["id"]],
        )

    if direct:
        direct_row = next(row for row, _ in rows if row["class"] == "direct_only")
        potential_row = next(row for row, _ in rows if row["class"] == "potential_split")
        for row, label, line in ((direct_row, "direct-only gate", "--"), (potential_row, "potential-split gate", ":")):
            xs = np.array([float(value) for value in row["delta"]])
            ys = np.array([float(value) for value in row["threshold"]])
            order = np.argsort(xs)
            ax.loglog(xs[order], ys[order], color=INK, linewidth=1.0, linestyle=line, label=label)
        anchor_x = np.array([1 / 80, 1 / 20])
        ax.loglog(anchor_x, 0.0002 * (anchor_x / anchor_x[0]) ** 2, color=MID, linewidth=0.9)
        ax.text(0.016, 0.00043, r"$O(\Delta^2)$", fontsize=7.0, color=MID)
        ax.loglog(anchor_x, 0.0011 * (anchor_x / anchor_x[0]), color=MID, linewidth=0.9, linestyle="--")
        ax.text(0.016, 0.0017, r"$O(\Delta)$", fontsize=7.0, color=MID)
    else:
        gate_row = rows[0][0]
        xs = np.array([float(value) for value in gate_row["delta"]])
        ys = np.array([float(value) for value in gate_row["threshold"]])
        order = np.argsort(xs)
        ax.loglog(xs[order], ys[order], color=INK, linewidth=1.0, linestyle=":", label="absolute gate")
        anchor_x = np.array([1 / 64, 1 / 16])
        ax.loglog(anchor_x, 0.0032 * (anchor_x / anchor_x[0]), color=MID, linewidth=0.9)
        ax.text(0.022, 0.0062, r"$O(\Delta)$", fontsize=7.0, color=MID)

    ax.set_title(f"{panel}  {title}", loc="left", weight="bold")
    ax.set_xlabel(r"lattice step $\Delta=L/N$")
    ax.set_ylabel(r"certified scenario distance $d_N$")
    ax.grid(True, which="both", color="#D6DEE3", linewidth=0.45)
    ax.legend(frameon=False, ncol=2, handlelength=2.2, columnspacing=0.9, loc="upper left")


def figure_convergence(ledgers: dict[str, dict[str, Any]]) -> None:
    product_rows = [(row, "Development") for row in scenario_series(ledgers["product_development"])]
    product_rows += [(row, "Confirmation") for row in scenario_series(ledgers["product_confirmation"])]
    direct_rows = [(row, "Development") for row in scenario_series(ledgers["direct_development"])]
    direct_rows += [(row, "Confirmation") for row in scenario_series(ledgers["direct_confirmation"])]

    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.55), sharey=True)
    plot_architecture_convergence(axes[0], product_rows, "Product walk", "C1", False)
    plot_architecture_convergence(axes[1], direct_rows, "Direct QCA", "C2", True)
    fig.subplots_adjust(wspace=0.31)
    save_figure(fig, "fig03_certified_convergence")


def figure_spectrum_boundary() -> None:
    mu = 0.4
    q = np.linspace(-math.pi, math.pi, 1400)
    omega = np.arccos(np.sqrt(1 - mu**2) * np.cos(q))
    low_edge = 1 / 40

    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.5), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    ax.plot(q / math.pi, omega / math.pi, color=BLUE, label=r"$+\omega$")
    ax.plot(q / math.pi, -omega / math.pi, color=ORANGE, linestyle="--", label=r"$-\omega$")
    ax.axvspan(-low_edge, low_edge, facecolor=GREEN, alpha=0.18, hatch="//", edgecolor=GREEN, linewidth=0.0, label="registered low-$q$ window")
    ax.axvspan(-1, -0.75, facecolor="none", hatch="xx", edgecolor=RED, linewidth=0.0, label=r"intended $\pi$ sector")
    ax.axvspan(0.75, 1, facecolor="none", hatch="xx", edgecolor=RED, linewidth=0.0)
    ax.axhline(1, color=MID, linewidth=0.7, linestyle=":")
    ax.axhline(-1, color=MID, linewidth=0.7, linestyle=":")
    alpha = math.asin(abs(mu)) / math.pi
    ax.annotate("zero gap", xy=(0, alpha), xytext=(0.18, 0.18), arrowprops={"arrowstyle": "->", "color": MID}, fontsize=7.1, color=MID)
    ax.annotate(r"$\pi$ gap", xy=(-1, 1 - alpha), xytext=(-0.76, 0.68), arrowprops={"arrowstyle": "->", "color": MID}, fontsize=7.1, color=MID)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel(r"dimensionless momentum $q/\pi$")
    ax.set_ylabel(r"principal quasienergy $\omega/\pi$")
    ax.set_title(r"D1  Complete Brillouin zone ($\mu=2/5$)", loc="left", weight="bold")
    ax.grid(True, color="#D6DEE3", linewidth=0.45)
    ax.legend(frameon=False, loc="lower center", ncol=2)

    ax = axes[1]
    p = np.linspace(-0.16 * math.pi, 0.16 * math.pi, 500)
    low = np.arccos(np.sqrt(1 - mu**2) * np.cos(p))
    zone = math.pi - np.arccos(np.sqrt(1 - mu**2) * np.cos(-math.pi + p))
    ax.plot(p / math.pi, low / math.pi, color=BLUE, label=r"low-$q$ cone, mass $-\mu$")
    ax.plot(p / math.pi, zone / math.pi, color=ORANGE, linestyle="--", label=r"$\pi$ partner, mass $+\mu$")
    ax.axvspan(-low_edge, low_edge, facecolor=GREEN, alpha=0.18, hatch="//", edgecolor=GREEN, linewidth=0.0)
    ax.text(
        0.5,
        0.93,
        r"$U_{\mu}(-\pi+p)=-U_{-\mu}(p)$",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8.3,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": MID, "linewidth": 0.7},
    )
    ax.annotate("same dispersion;\nopposite mass axis", xy=(0.105, low[np.abs(p / math.pi - 0.105).argmin()] / math.pi), xytext=(0.035, 0.14), arrowprops={"arrowstyle": "->", "color": MID}, fontsize=7.0, color=MID)
    ax.set_xlim(-0.16, 0.16)
    ax.set_ylim(0, 0.20)
    ax.set_xlabel(r"local displacement $p/\pi$")
    ax.set_ylabel("energy from local gap")
    ax.set_title("D2  Exact zone-edge partner", loc="left", weight="bold")
    ax.grid(True, color="#D6DEE3", linewidth=0.45)
    ax.legend(frameon=False, loc="lower center", fontsize=6.7)
    fig.subplots_adjust(wspace=0.31)
    save_figure(fig, "fig04_spectrum_domain")


def figure_claim_boundary() -> None:
    fig, ax = plt.subplots(figsize=(7.25, 4.1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.02, 0.955, "E", weight="bold", fontsize=11, color=NAVY)
    ax.text(0.07, 0.95, "Evidence and claim boundary", weight="bold", fontsize=10.5, color=INK)

    ax.add_patch(Rectangle((0.035, 0.14), 0.93, 0.73, facecolor=PALE_RED, edgecolor=RED, linewidth=1.0, linestyle="--"))
    ax.text(0.055, 0.825, "NOT ESTABLISHED", fontsize=7.4, weight="bold", color=RED)
    ax.text(
        0.50,
        0.785,
        "architecture-class breadth  ·  whole-zone equivalence  ·  canonical fermionic or interacting QFT",
        ha="center",
        va="center",
        fontsize=6.7,
        color=RED,
    )
    ax.text(0.50, 0.752, "necessity  ·  uniqueness  ·  minimality  ·  ontology", ha="center", va="center", fontsize=6.7, color=RED)

    ax.add_patch(Rectangle((0.07, 0.22), 0.86, 0.49, facecolor="#F3F5F6", edgecolor=MID, linewidth=1.0))
    ax.text(0.09, 0.675, "ANALYTIC INTERPRETATION BOUNDARY", fontsize=7.2, weight="bold", color=MID)
    ax.text(
        0.50,
        0.638,
        r"exact time-frame conjugacy  ·  nonminimal clocks  ·  product full-space lift under-specified",
        ha="center",
        fontsize=6.65,
        color=MID,
    )
    ax.text(0.50, 0.605, r"$\pi$ pseudodoubler  ·  empirical $\pi$ reducer withdrawn  ·  hard-core lift $\ne$ fermionic lift", ha="center", fontsize=6.45, color=MID)

    ax.add_patch(Rectangle((0.105, 0.32), 0.79, 0.24, facecolor=PALE_GREEN, edgecolor=GREEN, linewidth=1.2))
    ax.text(0.125, 0.525, "REGISTERED LEDGERS + QUALIFIED ALGORITHMIC REPLAY", fontsize=7.0, weight="bold", color=GREEN)
    ax.text(
        0.50,
        0.478,
        "Two separately registered local updates support the shared frozen core\n"
        "of a bounded $1+1$D Dirac operational role",
        ha="center",
        va="center",
        fontsize=7.05,
        weight="bold",
        color=INK,
    )

    add_box(ax, 0.14, 0.34, 0.30, 0.085, "Product walk\nledger: 4/4 dev · 2/2 conf", face=PALE_BLUE, edge=BLUE, fontsize=6.15)
    add_box(ax, 0.56, 0.34, 0.30, 0.085, "Direct symmetry QCA\nledger: 4/4 dev · 2/2 conf*", face=PALE_ORANGE, edge=ORANGE, fontsize=6.15)
    add_arrow(ax, (0.445, 0.3825), (0.555, 0.3825), MID)
    ax.text(0.50, 0.402, "same role", ha="center", fontsize=6.1, color=MID)

    ax.text(
        0.50,
        0.266,
        r"$L=16$  ·  $|r|\leq4$ (18 dimensions)  ·  $T\leq2$  ·  fixed $E,\Phi,M$ per registration  ·  one excitation",
        ha="center",
        fontsize=6.5,
        color=INK,
    )
    ax.text(0.50, 0.238, r"evolution, witness, causal, symmetry, and analytic $\pi$ bounds supported  ·  *direct empirical $\pi$ reducer withdrawn", ha="center", fontsize=6.0, color=INK)
    ax.text(0.50, 0.085, "The lattice, quantum primitive, clock, constants, maps, and intervention class remain supplied construction inputs.", ha="center", fontsize=7.35, color=MID)
    save_figure(fig, "fig05_claim_boundary")


def write_results(ledgers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    product = [ledgers["product_development"], ledgers["product_confirmation"]]
    direct = [ledgers["direct_development"], ledgers["direct_confirmation"]]
    product_witness = witness_maxima(product, direct=False)
    direct_witness = witness_maxima(direct, direct=True)
    summary = {
        "product": {
            "scenario_count": sum(len(item["scenario_results"]) for item in product),
            "operator_max": str(operator_max(product)),
            "fine_operator_max": str(operator_max(product, 2)),
            "witness_maxima": {key: str(value) for key, value in product_witness.items()},
            "independent_state_max": str(independent_state_max(product)),
        },
        "direct": {
            "scenario_count": sum(len(item["scenario_results"]) for item in direct),
            "operator_max": str(operator_max(direct)),
            "fine_operator_max": str(operator_max(direct, 2)),
            "witness_maxima": {key: str(value) for key, value in direct_witness.items()},
            "independent_state_max": str(independent_state_max(direct)),
        },
    }
    (GENERATED_DIR / "results_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    macros = [
        "% Generated from content-addressed v0.4 ledgers; do not edit by hand.",
        rf"\newcommand{{\ProductOperatorMax}}{{{fmt(operator_max(product))}}}",
        rf"\newcommand{{\ProductFineOperatorMax}}{{{fmt(operator_max(product, 2))}}}",
        rf"\newcommand{{\DirectOperatorMax}}{{{fmt(operator_max(direct))}}}",
        rf"\newcommand{{\DirectFineOperatorMax}}{{{fmt(operator_max(direct, 2))}}}",
        rf"\newcommand{{\DirectIndependentMax}}{{{tex_sci(independent_state_max(direct))}}}",
        rf"\newcommand{{\ProductDevHash}}{{\texttt{{{LEDGER_SPECS[0].sha256}}}}}",
        rf"\newcommand{{\ProductConfirmHash}}{{\texttt{{{LEDGER_SPECS[1].sha256}}}}}",
        rf"\newcommand{{\DirectDevHash}}{{\texttt{{{LEDGER_SPECS[2].sha256}}}}}",
        rf"\newcommand{{\DirectConfirmHash}}{{\texttt{{{LEDGER_SPECS[3].sha256}}}}}",
    ]
    for prefix, values in (("Product", product_witness), ("Direct", direct_witness)):
        for label, value in values.items():
            command = "".join(part.title() for part in label.split("_"))
            macros.append(rf"\newcommand{{\{prefix}{command}Max}}{{{tex_sci(value)}}}")
    (GENERATED_DIR / "results.tex").write_text("\n".join(macros) + "\n")

    architecture_table = r"""% Generated table.
\begin{tabular}{@{}p{0.28\linewidth}p{0.32\linewidth}p{0.32\linewidth}@{}}
\toprule
Coordinate & Product walk & Direct symmetry QCA \\
\midrule
Free update & Ordered mass mix and transport & Single normalized QCA block \\
Declared localization & Mass mix; on-site and edge SWAPs & Edge scatter; on-site routing SWAP \\
Full-space scope & Mixer collision phase not frozen & Explicit hard-core $+1$ collision phase \\
Declared free / active depth & $3$ / $4$ layers & $2$ / $3$ layers \\
Declared free / active gate-work & $3N$ / $4N$ & $2N$ / $3N$ \\
Storage; ancillas & $2N$ mode labels; $0$ & $2N$ qubits; $0$ \\
Causal radius & one cell per macrostep & one cell per macrostep \\
Leading free correction & first-order global, Lie--Trotter & second-order global, symmetric time frame \\
Registered refinements & $N=256,512,1024$ & $N=320,640,1280$ \\
\bottomrule
\end{tabular}
"""
    (GENERATED_DIR / "tables" / "architecture_comparison.tex").write_text(architecture_table)

    gates = {
        "position_tv": (Decimal("0.05"), Decimal("0.010"), "Position TV"),
        "momentum_tv": (Decimal("0.05"), Decimal("0.010"), "Momentum TV"),
        "total_current": (Decimal("0.10"), Decimal("0.020"), "Total-current error"),
        "local_current": (Decimal("0.10"), Decimal("0.020"), "Local-current $L_1$"),
        "infidelity": (Decimal("0.0025"), Decimal("0.0001"), "Infidelity"),
        "zitter": (Decimal("0.10"), Decimal("0.020"), r"Zitterbewegung series $L_\infty$"),
    }
    witness_lines = [
        r"% Generated table.",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Metric & Product max & Gate & Direct max & Gate \\",
        r"\midrule",
    ]
    for key, (product_gate, direct_gate, label) in gates.items():
        witness_lines.append(
            f"{label} & ${tex_sci(product_witness[key])}$ & ${fmt(product_gate)}$ & "
            f"${tex_sci(direct_witness[key])}$ & ${fmt(direct_gate)}$ \\\\"
        )
    witness_lines += [r"\bottomrule", r"\end{tabular}"]
    (GENERATED_DIR / "tables" / "witness_maxima.tex").write_text("\n".join(witness_lines) + "\n")

    scenario_lines = [
        r"% Generated table.",
        r"\begin{tabular}{@{}llrrr@{}}",
        r"\toprule",
        r"Architecture / partition & Scenario & Coarse & Middle & Fine \\",
        r"\midrule",
    ]
    for spec in LEDGER_SPECS:
        ledger = ledgers[spec.key]
        for row in scenario_series(ledger):
            distances = [tex_sci(value) for value in row["distance"]]
            scenario_lines.append(
                f"{spec.architecture} / {spec.partition.lower()} & {tex_escape(SCENARIO_LABELS[row['id']])} & "
                f"${distances[0]}$ & ${distances[1]}$ & ${distances[2]}$ \\\\"
            )
    scenario_lines += [r"\bottomrule", r"\end{tabular}"]
    (GENERATED_DIR / "tables" / "scenario_distances.tex").write_text("\n".join(scenario_lines) + "\n")

    provenance_lines = [
        r"% Generated table.",
        r"\begin{tabular}{@{}llll@{}}",
        r"\toprule",
        r"Architecture & Partition & Classification & Ledger SHA-256 \\",
        r"\midrule",
    ]
    for spec in LEDGER_SPECS:
        status = tex_escape(ledgers[spec.key]["status"])
        provenance_lines.append(
            rf"{spec.architecture} & {spec.partition} & \texttt{{{status}}} & \texttt{{{spec.sha256[:12]}\ldots}}" + r" \\"
        )
    provenance_lines += [r"\bottomrule", r"\end{tabular}"]
    (GENERATED_DIR / "tables" / "provenance.tex").write_text("\n".join(provenance_lines) + "\n")
    return summary


def write_manifest() -> None:
    outputs = sorted(
        path
        for path in [*FIGURE_DIR.glob("*.pdf"), *FIGURE_DIR.glob("*.png"), *GENERATED_DIR.glob("*.tex"), *GENERATED_DIR.glob("*.json"), *(GENERATED_DIR / "tables").glob("*.tex")]
        if path.name != "figure_manifest.json"
    )
    generator_path = ROOT / "scripts" / "generate_quantum_dirac_paper.py"
    manifest = {
        "generator": "scripts/generate_quantum_dirac_paper.py",
        "generator_sha256": sha256(generator_path),
        "inputs": [
            {
                "key": spec.key,
                "path": spec.path,
                "sha256": spec.sha256,
                "status": "content-addressed registered result",
            }
            for spec in LEDGER_SPECS
        ],
        "registered_spec_inputs": [
            {
                "key": spec.key,
                "architecture": spec.architecture,
                "kind": spec.kind,
                "path": spec.path,
                "sha256": spec.sha256,
                "status": "frozen registered specification",
            }
            for spec in REGISTERED_SPECS
        ],
        "analytic_sources": [
            {"path": path, "sha256": sha256(ROOT / path)}
            for path in ANALYTIC_SOURCE_PATHS
        ],
        "software_versions": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "figure_classes": {
            "fig01_construction_map": "conceptual",
            "fig02_architecture_comparison": "analytic",
            "fig03_certified_convergence": "registered result",
            "fig04_spectrum_domain": "analytic",
            "fig05_claim_boundary": "conceptual synthesis",
        },
        "outputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for path in outputs
        ],
    }
    (GENERATED_DIR / "figure_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main() -> int:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    (GENERATED_DIR / "tables").mkdir(parents=True, exist_ok=True)
    setup_style()
    ledgers = load_ledgers()
    registered = load_registered_specs()
    write_results(ledgers)
    write_registered_protocol_tables(registered)
    figure_construction_map()
    figure_architectures()
    figure_convergence(ledgers)
    figure_spectrum_boundary()
    figure_claim_boundary()
    write_manifest()
    print("Generated quantum-Dirac manuscript figures and tables from verified ledger hashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
