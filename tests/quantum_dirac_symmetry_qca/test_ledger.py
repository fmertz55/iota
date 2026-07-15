from __future__ import annotations

import copy
import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from src.quantum_dirac_symmetry_qca.ledger import (
    BINDING_KEYS,
    FAILURE_CONTROL_IDS,
    FAILURE_CONTROL_METRICS,
    POTENTIAL_ACTIVE_STEPS,
    SCENARIO_CLASSES,
    build_result_ledger,
    validate_result_ledger,
    write_result_ledger,
)
from src.quantum_dirac_symmetry_qca.protocol import (
    CONFIRMATION_SCENARIOS,
    CONFIRMATION_STATES,
    DEVELOPMENT_SCENARIOS,
    DEVELOPMENT_STATES,
    DIRECT_DISTANCE_THRESHOLDS,
    PHYSICAL_HORIZON,
    PHYSICAL_LENGTH,
    POTENTIAL_DISTANCE_THRESHOLDS,
    REGISTERED_SIZES,
)
from src.quantum_dirac_symmetry_qca.spec import SymmetryQCASpecError, canonical_json


def _bindings() -> dict[str, dict[str, str]]:
    return {
        name: {"path": f"fixture/{name}.json", "sha256": f"{index:064x}"}
        for index, name in enumerate(sorted(BINDING_KEYS), start=1)
    }


def _resources(scenario_id: str, n_sites: int) -> dict[str, int]:
    macrosteps = n_sites * PHYSICAL_HORIZON // PHYSICAL_LENGTH
    active = POTENTIAL_ACTIVE_STEPS.get(scenario_id, {}).get(n_sites, 0)
    layers = 2 * macrosteps + active
    return {
        "n_sites": n_sites,
        "macrosteps": macrosteps,
        "active_potential_steps": active,
        "elementary_layers": layers,
        "gate_work": n_sites * layers,
        "occupation_qubits": 2 * n_sites,
        "ancillas": 0,
        "causal_radius_per_macrostep": 1,
    }


def _zitter_series() -> list[dict[str, object]]:
    delta = Fraction(PHYSICAL_LENGTH, REGISTERED_SIZES[-1])
    records = []
    for step in range(1, REGISTERED_SIZES[-1] * PHYSICAL_HORIZON // PHYSICAL_LENGTH + 1):
        time = step * delta
        records.append(
            {
                "step": step,
                "time": str(time.numerator)
                if time.denominator == 1
                else f"{time.numerator}/{time.denominator}",
                "candidate_current_lower": "0",
                "candidate_current_upper": "0",
                "target_current_lower": "0",
                "target_current_upper": "0",
                "error_upper": "0",
            }
        )
    return records


def _scenario(scenario_id: str, state_ids: tuple[str, ...]) -> dict[str, object]:
    scenario_class = SCENARIO_CLASSES[scenario_id]
    thresholds = (
        DIRECT_DISTANCE_THRESHOLDS
        if scenario_class == "direct_only"
        else POTENTIAL_DISTANCE_THRESHOLDS
    )
    witnesses = []
    for state_id in state_ids:
        zitter = _zitter_series() if state_id.endswith("ZITTER") else []
        witnesses.append(
            {
                "state_id": state_id,
                "position_tv_max": "0",
                "momentum_tv_max": "0",
                "total_current_error_max": "0",
                "local_current_l1_max": "0",
                "infidelity_max": "0",
                "zitter_current_series": zitter,
                "zitter_current_series_sup_error": "0" if zitter else None,
                "pass": True,
            }
        )
    return {
        "scenario_id": scenario_id,
        "scenario_class": scenario_class,
        "operator": {
            "refinements": [
                {
                    "n_sites": n_sites,
                    "observation_distance_uppers": ["0"] * 5,
                    "scenario_distance_upper": "0",
                    "target_tail_upper": "0",
                    "numerical_enclosure_upper": "0",
                    "absolute_threshold": thresholds[n_sites],
                    "absolute_pass": True,
                    "resources": _resources(scenario_id, n_sites),
                }
                for n_sites in REGISTERED_SIZES
            ],
            "refinement_gates_pass": True,
            "pass": True,
        },
        "witnesses": witnesses,
        "pi_sector": {
            "analytic_probability_upper": "0",
            "candidate_probability_upper": "0",
            "threshold": "1e-24",
            "pass": True,
        },
        "maximum_independent_state_disagreement_upper": "0",
        "symmetry_and_structure": {
            "unitarity_residual_upper": "0",
            "unitarity_pass": True,
            "causality_pass": True,
            "parity_residual_upper": "0",
            "parity_pass": True,
            "time_reversal_role_residual_uppers": ["0", "0", "0"],
            "time_reversal_role_refinement_pass": True,
            "time_reversal_role_fine_pass": True,
            "time_reversal_role_pass": True,
            "architecture_integrity_pass": True,
        },
        "pass": True,
    }


def fixture_ledger(stage: str = "development") -> dict[str, object]:
    scenarios = DEVELOPMENT_SCENARIOS if stage == "development" else CONFIRMATION_SCENARIOS
    states = DEVELOPMENT_STATES if stage == "development" else CONFIRMATION_STATES
    controls = None
    if stage == "confirmation":
        controls = [
            {
                "id": control_id,
                "metric": FAILURE_CONTROL_METRICS[control_id],
                "value": "2" if control_id == "FERMIONIC-LIFT" else "0",
            }
            for control_id in FAILURE_CONTROL_IDS
        ]
    return build_result_ledger(
        stage=stage,
        bindings=_bindings(),
        scenario_results=[_scenario(scenario_id, states) for scenario_id in scenarios],
        failure_controls=controls,
    )


class CanonicalLedgerTests(unittest.TestCase):
    def test_builds_both_complete_stage_shapes(self) -> None:
        development = fixture_ledger("development")
        confirmation = fixture_ledger("confirmation")
        self.assertEqual(development["status"], "development_passed")
        self.assertEqual(
            confirmation["status"],
            "constructive_sufficiency_passed_direct_symmetry_qca_sector",
        )

    def test_rejects_noncanonical_maximum_resource_and_series(self) -> None:
        ledger = fixture_ledger()
        bad_maximum = copy.deepcopy(ledger)
        bad_maximum["scenario_results"][0]["operator"]["refinements"][0][
            "scenario_distance_upper"
        ] = "1e-80"
        with self.assertRaises(SymmetryQCASpecError):
            validate_result_ledger(bad_maximum)

        bad_resource = copy.deepcopy(ledger)
        bad_resource["scenario_results"][0]["operator"]["refinements"][0][
            "resources"
        ]["elementary_layers"] += 1
        with self.assertRaises(SymmetryQCASpecError):
            validate_result_ledger(bad_resource)

        bad_series = copy.deepcopy(ledger)
        bad_series["scenario_results"][0]["witnesses"][-1][
            "zitter_current_series"
        ].pop()
        with self.assertRaises(SymmetryQCASpecError):
            validate_result_ledger(bad_series)

    def test_rejects_gate_and_control_reclassification(self) -> None:
        ledger = fixture_ledger("confirmation")
        bad_pi = copy.deepcopy(ledger)
        bad_pi["scenario_results"][1]["pi_sector"]["candidate_probability_upper"] = "1e-2"
        with self.assertRaises(SymmetryQCASpecError):
            validate_result_ledger(bad_pi)

        bad_control = copy.deepcopy(ledger)
        bad_control["aggregate"]["failure_controls"][0]["id"] = "HIGH-Q"
        with self.assertRaises(SymmetryQCASpecError):
            validate_result_ledger(bad_control)

    def test_atomic_writer_is_canonical_and_refuses_clobber(self) -> None:
        ledger = fixture_ledger()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "result.json"
            write_result_ledger(path, ledger, stage="development")
            self.assertEqual(
                path.read_text(encoding="ascii"), canonical_json(ledger) + "\n"
            )
            self.assertEqual(json.loads(path.read_text()), ledger)
            with self.assertRaises(SymmetryQCASpecError):
                write_result_ledger(path, ledger, stage="development")


if __name__ == "__main__":
    unittest.main()
