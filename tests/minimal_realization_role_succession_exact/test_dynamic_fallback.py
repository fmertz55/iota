from __future__ import annotations

import unittest
from unittest import mock

from src.minimal_realization_role_succession.detector import assess_layer
from src.minimal_realization_role_succession.dynamics import canonical_initial_state, step
from src.minimal_realization_role_succession.manifest import (
    build_candidate,
    candidate_sha256,
    canonical_json,
    sha256_bytes,
)
from src.minimal_realization_role_succession.runner import (
    candidate_trace_domain,
    trace_joint_orbit,
)
from src.minimal_realization_role_succession_exact import runner, verifier


COPY_PREDECESSOR_ROWS = ("100", "101", "110", "111")
SYNTHETIC_BOUNDARY = 40


def role_record(value: tuple[int, int] | None) -> dict[str, int] | None:
    return None if value is None else {"layer": value[0], "anchor": value[1]}


def successor_record(
    value: tuple[int, int, int] | None,
) -> dict[str, int] | None:
    return (
        None
        if value is None
        else {"layer": value[0], "anchor": value[1], "successor_anchor": value[2]}
    )


class SyntheticDynamicFallbackTests(unittest.TestCase):
    def test_prefix_schedule_continues_without_reset_and_verifies_independently(self) -> None:
        # Copy-predecessor is a disclosed synthetic development rule, not one
        # selected from the registered ten-candidate continuation allocation.
        candidate = build_candidate(COPY_PREDECESSOR_ROWS)

        def transition(state: tuple[int, int]) -> tuple[int, int]:
            return (
                step(state[0], COPY_PREDECESSOR_ROWS, 64),
                step(state[1], COPY_PREDECESSOR_ROWS, 64),
            )

        def assessor(state: tuple[int, int], layer: int):
            return assess_layer(
                state[0],
                state[1],
                COPY_PREDECESSOR_ROWS,
                layer=layer,
                origin=0,
                cycle_size=64,
            )

        prefix = trace_joint_orbit(
            (canonical_initial_state(0, 64), 0),
            transition,
            assessor,
            saturation_layer=32,
            max_layers=SYNTHETIC_BOUNDARY,
            trace_domain=candidate_trace_domain(candidate),
            cycle_size=64,
        )
        self.assertEqual(prefix.status, "resource_censored_before_recurrence")
        parent_record = {
            "candidate_id": candidate["candidate_id"],
            "candidate_sha256": candidate_sha256(candidate),
            "evaluation_status": "resource_censored_before_recurrence",
            "last_assessed_layer": SYNTHETIC_BOUNDARY,
            "resource_limit": SYNTHETIC_BOUNDARY,
            "first_role": role_record(prefix.first_role),
            "first_successor": successor_record(prefix.first_successor),
            "first_intervention_eligible": successor_record(
                prefix.first_intervention_eligible
            ),
            "first_complete_pass": None,
            "recurrence": None,
            "trace_sha256": prefix.trace_sha256,
        }
        parent_record_hash = sha256_bytes(
            canonical_json(parent_record).encode("ascii")
        )
        continuation = {
            "candidate_id": candidate["candidate_id"],
            "candidate_sha256": candidate_sha256(candidate),
            "parent_record_sha256": parent_record_hash,
            "production_rows": list(COPY_PREDECESSOR_ROWS),
            "parent_prefix_trace_sha256": prefix.trace_sha256,
        }
        with mock.patch.object(runner, "PARENT_RESOURCE_BOUNDARY", SYNTHETIC_BOUNDARY):
            outcome = runner.evaluate_uncapped_continuation(
                continuation,
                parent_record,
                candidate,
            )
        self.assertEqual(outcome["classification"], "recurrence_excluded_on_fixed_orbit")
        self.assertGreater(outcome["last_assessed_layer"], SYNTHETIC_BOUNDARY)
        self.assertEqual(outcome["prefix_replay"]["boundary_layer"], SYNTHETIC_BOUNDARY)
        self.assertEqual(
            outcome["prefix_replay"]["brent_checkpoint_layer"]
            + outcome["prefix_replay"]["brent_distance"],
            SYNTHETIC_BOUNDARY,
        )
        with mock.patch.object(verifier, "PARENT_RESOURCE_BOUNDARY", SYNTHETIC_BOUNDARY):
            verifier._independent_dynamic(
                continuation,
                parent_record,
                candidate,
                outcome,
            )


if __name__ == "__main__":
    unittest.main()
