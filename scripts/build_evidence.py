from __future__ import annotations

import csv
import json
from pathlib import Path

from evidence_common import (
    ROOT,
    evidence_metrics,
    load_gc001,
    load_gc002,
    load_gc003,
    load_gc004,
    load_gc005,
    load_gc006,
    load_gc008,
    load_gc009,
    load_gc010,
    load_gc011,
    load_registry,
    sha256,
    strict_events,
    tex_escape,
)


GENERATED = ROOT / "paper" / "generated"
CANONICAL_V036_CONFIG = (
    ROOT
    / "output"
    / "findings"
    / "configs"
    / (
        "v036_component_bridge_seed42_ka5_vac2_val8_n16_rpp0p02_rrp1p0_mo3_"
        "amc0p5_amr0p5_cap2_amrb2p0_cb0p25_lb0p05_ffn0p05_een0p05.yaml"
    )
)
CANONICAL_V036_VERSION = "iota-rig-v0.3.6-component-bridge-residual-recruitment"


def tex_code(value: object) -> str:
    return rf"\texttt{{{tex_escape(value)}}}"


def yes_no(value: object) -> str:
    if not isinstance(value, bool):
        raise ValueError(f"expected a boolean parameter, observed {value!r}")
    return "yes" if value else "no"


def math_range(symbol: str, bounds: object) -> str:
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError(f"expected a two-value range for {symbol}, observed {bounds!r}")
    lower, upper = bounds
    if lower == upper:
        return rf"${symbol}={lower}$"
    return rf"${symbol}\in[{lower},{upper}]$"


def render_model_parameters(config: dict) -> str:
    version = config.get("simulation_version")
    if version != CANONICAL_V036_VERSION:
        raise ValueError(
            "canonical model-parameter source has unexpected simulation version: "
            f"{version!r}"
        )

    grid = config["grid"]
    init = config["init"]
    vectors = config["vectors"]
    constants = config["constants"]
    run = config["run"]
    if init.get("seed") != 42:
        raise ValueError(
            "canonical model-parameter source must retain reference seed 42"
        )

    behavior_bands = "; ".join(
        f"{tex_escape(name)} {bounds[0]}--{bounds[1]}"
        for name, bounds in vectors["behavior_bands"].items()
    )
    geometry_weights = constants["angular_momentum_residual_geometry_weights"]
    nonzero_weights = [
        f"{tex_escape(name.replace('_', ' '))} {weight}"
        for name, weight in geometry_weights.items()
        if float(weight) != 0.0
    ]
    zero_weight_count = sum(
        float(weight) == 0.0 for weight in geometry_weights.values()
    )
    weight_summary = "; ".join(nonzero_weights)
    if zero_weight_count:
        weight_summary += f"; remaining {zero_weight_count} classes 0"

    rows = [
        (
            "System",
            "Simulation version",
            rf"{{\scriptsize\path{{{tex_escape(version)}}}}}",
        ),
        (
            "",
            "Lattice and boundary",
            rf"${grid['size']}^3$; periodic = {yes_no(grid['wrap'])}",
        ),
        (
            "Initialization",
            "Reference realization",
            (
                f"{tex_code(init['mode'])}; seed {init['seed']}; "
                f"{init['active_iotas']} active iotas"
            ),
        ),
        (
            "",
            "Initial expression ranges",
            "; ".join(
                [
                    math_range("A", init["amplitude_range"]),
                    math_range("R", init["range_range"]),
                    math_range("P", init["payload_range"]),
                ]
            ),
        ),
        (
            "Local law",
            "Neighborhood and vectors",
            (
                f"neighbor mode {tex_code(constants['neighbor_mode'])}; "
                f"vector mode {tex_code(vectors['mode'])}; "
                f"{vectors['vector_count']} vectors"
            ),
        ),
        (
            "",
            "Vector behavior bands",
            behavior_bands,
        ),
        (
            "",
            "Transfer and conservation",
            (
                rf"$k_A={constants['amplitude_coupling']}$; "
                rf"range coupling $={constants['range_coupling']}$; "
                rf"bond probability $={constants['bond_probability']}$; "
                f"valence {constants['valence']}; "
                f"conservation {tex_code(constants['conservation'])}"
            ),
        ),
        (
            "",
            "Decay and deactivation",
            (
                f"decay {tex_code(constants['decay_mode'])}; "
                f"deactivation {tex_code(constants['deactivation'])}; "
                f"vacuum amplitude {constants['vacuum_amplitude']}"
            ),
        ),
        (
            "",
            "Payload dynamics",
            (
                rf"takeover $={constants['payload_takeover']}$; "
                rf"same/cross couplings $={constants['same_payload_coupling']}/"
                rf"{constants['cross_payload_coupling']}$"
            ),
        ),
        (
            "",
            "Residual recruitment",
            (
                rf"probability $={constants['residual_participation_probability']}$; "
                "secondary-only = "
                f"{yes_no(constants['residual_participation_secondary_only'])}"
            ),
        ),
        (
            "Angular control",
            "Received rotation",
            (
                rf"probability $={constants['received_rotation_probability']}$; "
                f"maximum offset {constants['received_rotation_max_offset']}; "
                "preserve behavior = "
                f"{yes_no(constants['received_rotation_preserve_behavior'])}"
            ),
        ),
        (
            "",
            "Angular memory",
            (
                f"enabled = {yes_no(constants['angular_momentum_enabled'])}; "
                rf"decay/coupling/retention $={constants['angular_momentum_decay']}/"
                rf"{constants['angular_momentum_coupling']}/"
                rf"{constants['angular_momentum_retention']}$; "
                rf"cap $={constants['angular_momentum_cap']}$"
            ),
        ),
        (
            "",
            "Residual angular bias",
            (
                f"enabled = {yes_no(constants['angular_momentum_residual_bias_enabled'])}; "
                rf"strength $={constants['angular_momentum_residual_bias_strength']}$; "
                f"gate {tex_code(constants['angular_momentum_residual_bias_gate'])}; "
                "mean-preserving = "
                f"{yes_no(constants['angular_momentum_residual_bias_mean_preserving'])}"
            ),
        ),
        (
            "",
            "Residual-bias score",
            tex_code(constants["angular_momentum_residual_bias_score_mode"]),
        ),
        (
            "",
            "Nonzero geometry weights",
            weight_summary,
        ),
        (
            "Run",
            "Registered horizon",
            (
                f"{run['ticks']} ticks; snapshots every {run['snapshot_every']}; "
                f"metrics every {run['metric_every']}"
            ),
        ),
    ]

    lines = [
        "% Generated by scripts/build_evidence.py. Do not edit.",
        r"\begin{table}[tbp]",
        r"\centering",
        r"\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{0.17\linewidth}>{\raggedright\arraybackslash}p{0.27\linewidth}X@{}}",
        r"\toprule",
        r"Component & Parameter & Frozen value \\",
        r"\midrule",
    ]
    previous_component = ""
    for component, parameter, value in rows:
        if component and previous_component:
            lines.append(r"\addlinespace[2pt]")
        lines.append(
            " & ".join([tex_escape(component), tex_escape(parameter), value])
            + r" \\"
        )
        if component:
            previous_component = component
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabularx}",
            r"\caption{Principal frozen parameters of the canonical v0.3.6 component-bridge reference configuration. Values are generated directly from the complete registered YAML source.}",
            r"\label{tab:model-parameters}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def render_results(
    claim: dict,
    metrics: dict,
    gc002_summary: dict,
    gc002_cases: list[dict[str, str]],
    gc003_summary: dict,
    gc003_cases: list[dict[str, str]],
    gc004_summary: dict,
    gc004_aggregate: list[dict[str, str]],
    gc005_summary: dict,
    gc006_summary: dict,
    gc008_same: dict,
    gc008_screen: dict,
    gc008_independent: dict,
    gc009_summary: dict,
    gc009_replays: list[dict[str, str]],
    gc010_summary: dict,
    gc011_summary: dict,
    gc014_screen: dict,
    gc014_summary: dict,
    gc014_results: list[dict[str, str]],
    gc015_summary: dict,
    gc015_channels: list[dict[str, str]],
    gc016_summary: dict,
    gc017_acquisition: dict,
    gc017_precursor: dict,
    gc017_donor: dict,
) -> str:
    strict_cases = [
        row for row in gc002_cases if row["finding060_constraint_transport"] == "1"
    ]
    failure_cases = [
        row for row in gc002_cases if row["finding060_constraint_transport"] == "0"
    ]
    lifetimes = ", ".join(row["continuous_relation_lifetime"] for row in strict_cases)
    gc003_strict = [
        row for row in gc003_cases if row["finding060_constraint_transport"] == "1"
    ]
    expression_lifetimes = ", ".join(
        row["expression_relation_lifetime"] for row in gc003_strict
    )
    gc004_rates = ", ".join(
        f"{100.0 * float(row['handoff_rate']):.1f}\\%"
        for row in gc004_aggregate
    )
    gc008_same_by_label = {
        row["natural_label"]: row for row in gc008_same["aggregate"]
    }
    gc009_first_same = sum(
        row["first_alternate_child_target"] != ""
        and row["first_alternate_child_target"] == row["selector_target"]
        for row in gc009_replays
    )
    gc009_capacity_retained = sum(
        int(row["source_capacity_retained_after_veto"]) for row in gc009_replays
    )
    gc010_depth_values = [
        str(gc010_summary["observed_cut_depth_counts"][str(depth)])
        for depth in range(1, int(gc010_summary["protocol_max_depth"]) + 1)
    ]
    gc010_depth_counts = (
        ", ".join(gc010_depth_values[:-1]) + ", and " + gc010_depth_values[-1]
    )
    gc011_depth_values = [
        str(gc011_summary["observed_cut_depth_counts"][str(depth)])
        for depth in range(1, int(gc011_summary["protocol_max_depth"]) + 1)
    ]
    gc011_depth_counts = (
        ", ".join(gc011_depth_values[:-1]) + ", and " + gc011_depth_values[-1]
    )
    gc014_memory_preserved = sum(
        int(row["natural_split_occurs"])
        for row in gc014_results
        if row["variant"] == "erase_inherited_memory"
    )
    gc015_natural = sum(int(row["natural_articulations"]) for row in gc015_channels)
    gc015_preserving = sum(int(row["preserving_articulations"]) for row in gc015_channels)
    gc015_breaking = sum(int(row["breaking_articulations"]) for row in gc015_channels)
    return "\n".join(
        [
            "% Generated by scripts/build_evidence.py. Do not edit.",
            rf"\newcommand{{\GCOneID}}{{{tex_escape(claim['id'])}}}",
            rf"\newcommand{{\GCOneTitle}}{{{tex_escape(claim['title'])}}}",
            rf"\newcommand{{\GCOneClassBEvents}}{{{metrics['class_b_events']}}}",
            rf"\newcommand{{\GCOneRoleBearingEvents}}{{{metrics['role_bearing_predecessor_events']}}}",
            rf"\newcommand{{\GCOneStrictEvents}}{{{metrics['strict_transport_events']}}}",
            rf"\newcommand{{\GCOneSeedCount}}{{{metrics['strict_positive_seed_count']}}}",
            rf"\newcommand{{\GCOneStatement}}{{{tex_escape(claim['statement'])}}}",
            rf"\newcommand{{\GCTwoLifetimes}}{{{lifetimes}}}",
            rf"\newcommand{{\GCTwoFailureCount}}{{{len(failure_cases)}}}",
            rf"\newcommand{{\GCTwoHorizon}}{{{max(int(row['horizon']) for row in gc002_cases)}}}",
            rf"\newcommand{{\GCTwoSecondTransportCount}}{{{gc002_summary['second_strict_transport_cases']}}}",
            rf"\newcommand{{\GCThreeLifetimes}}{{{expression_lifetimes}}}",
            rf"\newcommand{{\GCThreeSurvivalCount}}{{{gc003_summary['singleton_expression_survival_cases']}}}",
            rf"\newcommand{{\GCThreeEquivalenceEvents}}{{{gc003_summary['instrumentation_equivalence_event_count']}}}",
            rf"\newcommand{{\GCFourRates}}{{{gc004_rates}}}",
            rf"\newcommand{{\GCFourBranches}}{{{gc004_summary['samples_per_source']}}}",
            rf"\newcommand{{\GCFiveSensitivity}}{{{float(gc005_summary['held_out_metrics']['sensitivity']):.3f}}}",
            rf"\newcommand{{\GCFiveSpecificity}}{{{float(gc005_summary['held_out_metrics']['specificity']):.3f}}}",
            rf"\newcommand{{\GCFiveBalancedAccuracy}}{{{float(gc005_summary['held_out_metrics']['balanced_accuracy']):.3f}}}",
            rf"\newcommand{{\GCSixEligibleRows}}{{{gc006_summary['confirmation_eligible_single_address_rows']}}}",
            rf"\newcommand{{\GCSixBalancedAccuracy}}{{{float(gc006_summary['confirmation_metrics']['balanced_accuracy']):.3f}}}",
            rf"\newcommand{{\GCEightSameGateCases}}{{{gc008_same_by_label['gate_failed']['eligible_replays']}}}",
            rf"\newcommand{{\GCEightSameGateRescues}}{{{gc008_same_by_label['gate_failed']['eventual_handoff']}}}",
            rf"\newcommand{{\GCEightSameExhaustCases}}{{{gc008_same_by_label['source_exhausted']['eligible_replays']}}}",
            rf"\newcommand{{\GCEightSameExhaustRoutes}}{{{gc008_same_by_label['source_exhausted']['route_reopened']}}}",
            rf"\newcommand{{\GCEightSameExhaustHandoffs}}{{{gc008_same_by_label['source_exhausted']['eventual_handoff']}}}",
            rf"\newcommand{{\GCEightScreenCases}}{{{gc008_screen['cases']}}}",
            rf"\newcommand{{\GCEightIndependentSources}}{{{gc008_independent['selected_sources']}}}",
            rf"\newcommand{{\GCNineEligible}}{{{gc009_summary['eligible_vetoes']}}}",
            rf"\newcommand{{\GCNineSameTick}}{{{gc009_summary['alternate_child_timing']['same_tick']}}}",
            rf"\newcommand{{\GCNineDelayed}}{{{gc009_summary['alternate_child_timing']['delayed']}}}",
            rf"\newcommand{{\GCNineNoAlternate}}{{{gc009_summary['alternate_child_timing']['none']}}}",
            rf"\newcommand{{\GCNineHandoffs}}{{{gc009_summary['address_endpoints']['handoff_at_first_address_loss']}}}",
            rf"\newcommand{{\GCNineLosses}}{{{gc009_summary['address_endpoints']['lineage_loss_at_first_address_loss']}}}",
            rf"\newcommand{{\GCNineFirstSameTarget}}{{{gc009_first_same}}}",
            rf"\newcommand{{\GCNineFirstDifferentTarget}}{{{gc009_summary['eventual_handoffs'] - gc009_first_same}}}",
            rf"\newcommand{{\GCNineCapacityRetained}}{{{gc009_capacity_retained}}}",
            rf"\newcommand{{\GCTenInitial}}{{{gc010_summary['initial_branches']}}}",
            rf"\newcommand{{\GCTenDepthCounts}}{{{gc010_depth_counts}}}",
            rf"\newcommand{{\GCTenCutTotal}}{{{gc010_summary['observed_cuts']}}}",
            rf"\newcommand{{\GCTenAboveMax}}{{{gc010_summary['right_censored_above_protocol_max']}}}",
            rf"\newcommand{{\GCTenSourceCensored}}{{{gc010_summary['source_survival_censored']}}}",
            rf"\newcommand{{\GCTenCollisions}}{{{gc010_summary['collision_cases']}}}",
            rf"\newcommand{{\GCTenVetoEvents}}{{{gc010_summary['distinct_selector_events_vetoed']}}}",
            rf"\newcommand{{\GCTenOverrideExecutions}}{{{gc010_summary['selector_override_executions']}}}",
            rf"\newcommand{{\GCTenTargetReuseBranches}}{{{gc010_summary['branches_with_reused_selector_targets']}}}",
            rf"\newcommand{{\GCTenFixedHorizon}}{{{gc010_summary['fixed_followup_offsets']}}}",
            rf"\newcommand{{\GCElevenInitial}}{{{gc011_summary['initial_selectors']}}}",
            rf"\newcommand{{\GCElevenSources}}{{{gc011_summary['independent_initialization_seeds']}}}",
            rf"\newcommand{{\GCElevenDepthCounts}}{{{gc011_depth_counts}}}",
            rf"\newcommand{{\GCElevenCutTotal}}{{{gc011_summary['observed_cuts']}}}",
            rf"\newcommand{{\GCElevenAboveMax}}{{{gc011_summary['right_censored_above_protocol_max']}}}",
            rf"\newcommand{{\GCElevenSourceCensored}}{{{gc011_summary['source_survival_censored']}}}",
            rf"\newcommand{{\GCElevenVetoEvents}}{{{gc011_summary['distinct_selector_events_vetoed']}}}",
            rf"\newcommand{{\GCElevenOverrideExecutions}}{{{gc011_summary['selector_override_executions']}}}",
            rf"\newcommand{{\GCElevenTargetReuseBranches}}{{{gc011_summary['branches_with_reused_selector_targets']}}}",
            rf"\newcommand{{\GCElevenTransientLosses}}{{{gc011_summary['transient_child_lineage_losses']}}}",
            rf"\newcommand{{\GCFourteenStrictInputs}}{{{gc014_screen['strict_transport_events']}}}",
            rf"\newcommand{{\GCFourteenEligible}}{{{gc014_screen['eligible_channels']}}}",
            rf"\newcommand{{\GCFourteenChannels}}{{{gc014_summary['selected_channels']}}}",
            rf"\newcommand{{\GCFourteenPattern}}{{{gc014_summary['pattern_channels']}}}",
            rf"\newcommand{{\GCFourteenRequired}}{{{gc014_summary['pattern_required_two_thirds']}}}",
            rf"\newcommand{{\GCFourteenMemoryPreserved}}{{{gc014_memory_preserved}}}",
            rf"\newcommand{{\GCFourteenMemorySensitive}}{{{int(gc014_summary['selected_channels']) - gc014_memory_preserved}}}",
            rf"\newcommand{{\GCFourteenVetoExtensions}}{{{gc014_summary['vetoes_extending_natural_split_lifetime']}}}",
            rf"\newcommand{{\GCFourteenVetoes}}{{{gc014_summary['unique_rebridge_vetoes']}}}",
            rf"\newcommand{{\GCFourteenDurable}}{{{len(gc014_summary['veto_separation_at_least_128_channels'])}}}",
            rf"\newcommand{{\GCFifteenChannels}}{{{gc015_summary['channels']}}}",
            rf"\newcommand{{\GCFifteenBranches}}{{{gc015_summary['branches_per_channel_variant'] * gc015_summary['channels']}}}",
            rf"\newcommand{{\GCFifteenNatural}}{{{gc015_natural}}}",
            rf"\newcommand{{\GCFifteenPreserving}}{{{gc015_preserving}}}",
            rf"\newcommand{{\GCFifteenBreaking}}{{{gc015_breaking}}}",
            rf"\newcommand{{\GCFifteenFavor}}{{{gc015_summary['preserve_over_break_discordances']}}}",
            rf"\newcommand{{\GCFifteenReverse}}{{{gc015_summary['break_over_preserve_discordances']}}}",
            rf"\newcommand{{\GCFifteenP}}{{{float(gc015_summary['one_sided_exact_mcnemar_p']):.4f}}}",
            rf"\newcommand{{\GCFifteenInformative}}{{{gc015_summary['informative_channels']}}}",
            rf"\newcommand{{\GCFifteenHigher}}{{{gc015_summary['informative_channels_preserving_higher']}}}",
            rf"\newcommand{{\GCFifteenCloser}}{{{gc015_summary['channels_preserving_strictly_closer_to_natural']}}}",
            rf"\newcommand{{\GCFifteenCloserRequired}}{{{gc015_summary['closer_required_two_thirds']}}}",
            rf"\newcommand{{\GCSixteenChannels}}{{{gc016_summary['channels']}}}",
            rf"\newcommand{{\GCSixteenStates}}{{{gc016_summary['factorial_states']}}}",
            rf"\newcommand{{\GCSixteenIdentifiable}}{{{gc016_summary['identifiable_channels']}}}",
            rf"\newcommand{{\GCSixteenInteractions}}{{{gc016_summary['nonzero_interaction_channels']}}}",
            rf"\newcommand{{\GCSixteenPreserving}}{{{gc016_summary['receiver_selection_counts']['preserving']}}}",
            rf"\newcommand{{\GCSixteenBreaking}}{{{gc016_summary['receiver_selection_counts']['breaking']}}}",
            rf"\newcommand{{\GCSeventeenCases}}{{{gc017_acquisition['cases']}}}",
            rf"\newcommand{{\GCSeventeenStrict}}{{{gc017_acquisition['strict_transport_events']}}}",
            rf"\newcommand{{\GCSeventeenStrictSeeds}}{{{gc017_acquisition['confirmation_sources']}}}",
            rf"\newcommand{{\GCSeventeenEligible}}{{{gc017_precursor['eligible_channels']}}}",
            rf"\newcommand{{\GCSeventeenPrecursors}}{{{gc017_precursor['selected_channels']}}}",
            rf"\newcommand{{\GCSeventeenDonors}}{{{gc017_donor['selected_independent_channels']}}}",
            rf"\newcommand{{\GCSeventeenRequired}}{{{gc017_donor['minimum_independent_channels']}}}",
            "",
        ]
    )


def render_event_table(events: list[dict[str, str]]) -> str:
    lines = [
        "% Generated by scripts/build_evidence.py. Do not edit.",
        r"\begin{table}[ht]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{rrrrlll}",
        r"\hline",
        r"Seed & Sample & Start & Rebridge & Predecessor & Successor & $J$ \\",
        r"\hline",
    ]
    for row in strict_events(events):
        lines.append(
            " & ".join(
                [
                    row["init_seed"],
                    row["sample_index"],
                    row["start_offset"],
                    row["rebridge_offset"],
                    tex_escape(row["original_bridge_cells"]),
                    tex_escape(row["successor_bridge_cells"]),
                    row["bridge_path_jaccard"],
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\caption{Strict constraint-transport events in Finding 060. $J$ is bridge-path Jaccard overlap.}",
            r"\label{tab:gc001-events}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def render_gc010_depth_table(depths: list[dict[str, str]]) -> str:
    lines = [
        "% Generated by scripts/build_evidence.py. Do not edit.",
        r"\begin{table}[ht]",
        r"\centering",
        r"\small",
        r"\begin{tabular}{rrrrr}",
        r"\toprule",
        r"Depth & Risk set & New cuts & Handoffs & Source-censored \\",
        r"\midrule",
    ]
    for row in depths:
        lines.append(
            " & ".join(
                [
                    row["depth"],
                    row["risk_set"],
                    row["cuts"],
                    row["handoffs"],
                    row["source_survival_censored"],
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Finding 069 ordered realization cut outcomes. Each depth's risk set is the preceding depth's confirmed handoffs.}",
            r"\label{tab:gc010-depths}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def render_gc011_depth_table(depths: list[dict[str, str]]) -> str:
    table = render_gc010_depth_table(depths)
    return table.replace(
        "Finding 069 ordered realization cut outcomes",
        "Finding 070 independent ordered-cut replication",
    ).replace("tab:gc010-depths", "tab:gc011-depths")


def render_definitions_tex(registry: dict) -> str:
    lines = [
        "% Generated by scripts/build_evidence.py. Do not edit.",
        r"\begin{description}",
    ]
    for item in registry["definitions"]:
        symbol = rf" ($ {item['symbol']} $)" if item.get("symbol") else ""
        lines.append(
            rf"\item[{tex_escape(item['term'])}{symbol}] {tex_escape(item['definition'])}"
        )
    lines.extend([r"\end{description}", ""])
    return "\n".join(lines)


def render_definitions_md(registry: dict) -> str:
    lines = [
        "# Iota Definitions",
        "",
        "This document is generated from `evidence/definitions.yaml`. Do not edit it directly.",
        "",
    ]
    for item in registry["definitions"]:
        lines.extend(
            [
                f"## {item['term']}",
                "",
                f"- ID: `{item['id']}`",
                f"- Kind: {item['kind']}",
                f"- Status: {item['status']}",
                f"- Symbol: `{item['symbol']}`" if item.get("symbol") else "- Symbol: none",
                "",
                item["definition"],
                "",
            ]
        )
    return "\n".join(lines)


def render_manifest(claim: dict) -> str:
    paths = [*claim["evidence"], claim["analysis"]]
    paths.extend(claim.get("supporting_analysis", []))
    if claim.get("instrumentation"):
        paths.append(claim["instrumentation"])
    paths.extend(["evidence/claims.yaml", "evidence/definitions.yaml"])
    manifest = {
        "schema_version": 1,
        "claim_id": claim["id"],
        "artifacts": [
            {
                "path": path,
                "bytes": (ROOT / path).stat().st_size,
                "sha256": sha256(ROOT / path),
            }
            for path in paths
        ],
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def outputs() -> dict[Path, str]:
    claim, summary, events = load_gc001()
    _, gc002_summary, gc002_cases = load_gc002()
    _, gc003_summary, gc003_cases = load_gc003()
    _, gc004_summary, gc004_aggregate = load_gc004()
    _, gc005_summary = load_gc005()
    _, gc006_summary = load_gc006()
    _, gc008_same, gc008_screen, gc008_independent = load_gc008()
    _, _, gc009_summary, gc009_replays = load_gc009()
    _, gc010_summary, _, gc010_depths, _, _ = load_gc010()
    _, gc011_summary, _, gc011_depths, _, _ = load_gc011()
    with (ROOT / "output/findings/finding074/pre_articulation_channel_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc014_screen = json.load(handle)
    with (ROOT / "output/findings/finding074/pre_articulation_channel_replay_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc014_summary = json.load(handle)
    with (ROOT / "output/findings/finding074/pre_articulation_channel_replay_results.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        gc014_results = list(csv.DictReader(handle))
    with (ROOT / "output/findings/finding075/successor_graph_susceptibility_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc015_summary = json.load(handle)
    with (ROOT / "output/findings/finding075/successor_graph_susceptibility_channels.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        gc015_channels = list(csv.DictReader(handle))
    with (ROOT / "output/findings/finding078/factorial_successor_accessibility_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc016_summary = json.load(handle)
    with (ROOT / "output/findings/finding079/factorial_acquisition_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc017_acquisition = json.load(handle)
    with (ROOT / "output/findings/finding079/factorial_channel_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc017_precursor = json.load(handle)
    with (ROOT / "output/findings/finding079/factorial_common_donor_summary.json").open(
        encoding="utf-8"
    ) as handle:
        gc017_donor = json.load(handle)
    claims_registry = load_registry(ROOT / "evidence" / "claims.yaml")
    definitions = load_registry(ROOT / "evidence" / "definitions.yaml")
    canonical_v036 = load_registry(CANONICAL_V036_CONFIG)
    metrics = evidence_metrics(summary, events)
    rendered = {
        GENERATED / "results.tex": render_results(
            claim,
            metrics,
            gc002_summary,
            gc002_cases,
            gc003_summary,
            gc003_cases,
            gc004_summary,
            gc004_aggregate,
            gc005_summary,
            gc006_summary,
            gc008_same,
            gc008_screen,
            gc008_independent,
            gc009_summary,
            gc009_replays,
            gc010_summary,
            gc011_summary,
            gc014_screen,
            gc014_summary,
            gc014_results,
            gc015_summary,
            gc015_channels,
            gc016_summary,
            gc017_acquisition,
            gc017_precursor,
            gc017_donor,
        ),
        GENERATED / "tables" / "gc001_events.tex": render_event_table(events),
        GENERATED / "tables" / "gc010_depths.tex": render_gc010_depth_table(
            gc010_depths
        ),
        GENERATED / "tables" / "gc011_depths.tex": render_gc011_depth_table(
            gc011_depths
        ),
        GENERATED / "definitions.tex": render_definitions_tex(definitions),
        GENERATED / "model_parameters.tex": render_model_parameters(
            canonical_v036
        ),
        ROOT / "docs" / "definitions.md": render_definitions_md(definitions),
    }
    for registered_claim in claims_registry["claims"]:
        rendered[
            ROOT / "evidence" / "manifests" / f"{registered_claim['id']}.json"
        ] = render_manifest(registered_claim)
    return rendered


def main() -> None:
    for path, content in outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
