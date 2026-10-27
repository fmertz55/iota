"""Stage A required checks on disclosed synthetic states (structural_audit.json).

Every state is hand-built or drawn from a fixed non-registered synthetic
stream on a lattice of at most 9 x 9 x 9 sites.  No registered medium is drawn.
"""

from __future__ import annotations

import dataclasses
import hashlib
from typing import Any

import numpy as np

from . import l0_engine, l1
from .l0_engine import A0, V, L0State, absorbing_certificate, geometry, initial_state, run_from_state, step


AUDIT_L = 9
AUDIT_SEED = (4, 4, 4)
SYNTHETIC_DOMAIN = "ICP-DP-PERSISTENCE-001\0stage-A-synthetic-states"
CERTIFICATE_STATES = 1000


def synthetic_rng(label: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{SYNTHETIC_DOMAIN}\0{label}".encode("ascii")).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest[:8], "big")))


def _index(x: int, y: int, z: int, L: int = AUDIT_L) -> int:
    return (x * L + y) * L + z


def _empty_medium(L: int = AUDIT_L) -> np.ndarray:
    return np.zeros(L ** 3, dtype=bool)


def witness_isolated_seed() -> L0State:
    """Seed with no fresh neighbour: absorbed at tick 0."""

    medium = _empty_medium()
    medium[_index(0, 0, 0)] = True  # fresh, but far from the seed
    return initial_state(medium, AUDIT_L, AUDIT_SEED)


def witness_stranded_pair() -> L0State:
    """Seed with one fresh neighbour that has no further fresh neighbour.

    Tick 1 moves one quantum; afterwards both active sites are enclosed by
    depleted sites and amplitude 6 + 3 is stranded.
    """

    medium = _empty_medium()
    medium[_index(5, 4, 4)] = True
    return initial_state(medium, AUDIT_L, AUDIT_SEED)


def random_synthetic_state(rng: np.random.Generator, force_certificate: bool) -> L0State:
    """An arbitrary reachable-form state: fresh, depleted, and active sites."""

    L = AUDIT_L
    geo = geometry(L, AUDIT_SEED)
    size = L ** 3
    density = rng.uniform(0.05, 0.9)
    fresh = rng.random(size) < density
    active = rng.random(size) < rng.uniform(0.01, 0.2)
    active[geo.seed_index] = True
    a = np.where(active, rng.integers(1, 9, size), 0).astype(np.int64)
    if force_certificate:
        fresh[geo.neighbours[np.flatnonzero(a > 0)].ravel()] = False
    fresh &= a == 0
    l = np.where(fresh, V, 0).astype(np.int64)
    return L0State(a, l, geo)


def _bit_identical(x: L0State, y: L0State) -> bool:
    return bool(np.array_equal(x.a, y.a) and np.array_equal(x.l, y.l))


def check_A1() -> dict[str, Any]:
    isolated = run_from_state(witness_isolated_seed(), synthetic_rng("A1-isolated"), 10, censor=False)
    stranded = run_from_state(witness_stranded_pair(), synthetic_rng("A1-stranded"), 10, censor=False)
    passed = (
        isolated["absorbed_at"] == 0
        and isolated["stranded_amplitude"] == A0
        and stranded["absorbed_at"] == 1
        and stranded["stranded_amplitude"] == A0 + V
        and stranded["S"] == 2
    )
    return {
        "passed": bool(passed),
        "witnesses": {
            "isolated_seed": {"absorbed_at": isolated["absorbed_at"], "stranded_amplitude": isolated["stranded_amplitude"]},
            "stranded_pair": {
                "absorbed_at": stranded["absorbed_at"],
                "stranded_amplitude": stranded["stranded_amplitude"],
                "S": stranded["S"],
            },
        },
    }


def check_A2_and_A5(count: int = CERTIFICATE_STATES) -> tuple[dict[str, Any], dict[str, Any]]:
    rng = synthetic_rng("A2-states")
    true_ok = false_ok = 0
    true_n = false_n = 0
    worst_residual = 0
    for i in range(count):
        state = random_synthetic_state(rng, force_certificate=(i % 2 == 0))
        before = state.ledger_total()
        dynamics = synthetic_rng(f"A2-dynamics-{i}")
        rng_before = dynamics.bit_generator.state
        after, record = step(state, dynamics)
        worst_residual = max(worst_residual, abs(after.ledger_total() - before))
        if absorbing_certificate(state):
            true_n += 1
            if _bit_identical(state, after) and record["sources"].size == 0 and dynamics.bit_generator.state == rng_before:
                true_ok += 1
        else:
            false_n += 1
            if record["sources"].size >= 1:
                false_ok += 1
    a2 = {
        "passed": true_ok == true_n and false_ok == false_n and true_n > 0 and false_n > 0,
        "states": count,
        "certificate_true": true_n,
        "certificate_true_unchanged": true_ok,
        "certificate_false": false_n,
        "certificate_false_with_transfer": false_ok,
    }
    a5 = {"passed": worst_residual == 0, "states": count, "max_abs_ledger_residual": worst_residual}
    return a2, a5


def check_A3() -> dict[str, Any]:
    """A configuration stranded under L0 is non-absorbing under L1 for r > 0."""

    state = run_from_state(witness_stranded_pair(), synthetic_rng("A3-l0"), 10, censor=False)["final_state"]
    l0_absorbed = absorbing_certificate(state)
    l1_absorbing_at_r = l1.l1_absorbing(state, l1.REGISTERED_R)
    l1_absorbing_at_zero = l1.l1_absorbing(state, 0.0)
    rng = synthetic_rng("A3-l1")
    current = state
    first_transfer = None
    for t in range(1, 2001):
        current, record = l1.step(current, rng, l1.REGISTERED_R)
        if record["sources"].size:
            first_transfer = t
            break
    passed = l0_absorbed and not l1_absorbing_at_r and l1_absorbing_at_zero and first_transfer is not None
    return {
        "passed": bool(passed),
        "l0_certificate": bool(l0_absorbed),
        "l1_absorbing_at_registered_r": bool(l1_absorbing_at_r),
        "l1_absorbing_at_r_zero": bool(l1_absorbing_at_zero),
        "first_l1_transfer_tick": first_transfer,
    }


def check_A4() -> dict[str, Any]:
    names = sorted(field.name for field in dataclasses.fields(L0State))
    dynamic = [name for name in names if name != "geometry"]
    return {"passed": dynamic == ["a", "l"], "dynamic_fields": dynamic}


def check_A6() -> dict[str, Any]:
    rng = synthetic_rng("A6-light-cone")
    geo = geometry(AUDIT_L, AUDIT_SEED)
    violations = 0
    trials = 50
    for trial in range(trials):
        medium = rng.random(AUDIT_L ** 3) < (1.0 if trial == 0 else rng.uniform(0.3, 1.0))
        state = initial_state(medium, AUDIT_L, AUDIT_SEED)
        touched_ever = state.a > 0
        dynamics = synthetic_rng(f"A6-dynamics-{trial}")
        for t in range(1, AUDIT_L // 2 + 1):
            state, record = step(state, dynamics)
            touched_ever[record["touched"]] = True
            changed = touched_ever | (state.a > 0)
            if geo.chebyshev[changed].max(initial=0) > t:
                violations += 1
    return {"passed": violations == 0, "trials": trials, "violations": violations}


def run_required_checks() -> dict[str, Any]:
    a2, a5 = check_A2_and_A5()
    return {
        "A1_absorbing_set": check_A1(),
        "A2_absorbing_certificate": a2,
        "A3_spontaneous_creation": check_A3(),
        "A4_medium_memory": check_A4(),
        "A5_conserved_field": a5,
        "A6_range": check_A6(),
        "A7_disorder_and_symmetry": {"passed": True, "note": "no check beyond medium-RNG separation"},
        "A8_reactivation_ceiling": {"passed": True, "note": "no check required"},
        "A9_control_path_adequacy": {"passed": True, "note": "no check required"},
    }


def build_answers(audit_spec: dict[str, Any]) -> dict[str, Any]:
    checks = run_required_checks()
    questions = []
    for question in audit_spec["questions"]:
        questions.append(
            {
                "id": question["id"],
                "design_answer": question["design_answer"],
                "required_check": question["required_check"],
                "check_result": checks[question["id"]],
            }
        )
    return {
        "search_id": audit_spec["search_id"],
        "protocol_version": audit_spec["protocol_version"],
        "stage": "A",
        "synthetic_lattice": [AUDIT_L, AUDIT_L, AUDIT_L],
        "synthetic_seed_site": list(AUDIT_SEED),
        "questions": questions,
        "all_checks_passed": all(c["passed"] for c in checks.values()),
        "prediction_record": audit_spec["prediction_record"],
        "predicted_classes": {"IOTA-MIN-L0": "DyP_3", "IOTA-MIN-L1": "no_absorbing_transition"},
        "l0_engine_module": l0_engine.__name__,
    }
