from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from src.minimal_realization_role_succession.protocol import (
    BASE_CONTRACT_VERSION,
    CANONICAL_ORIGIN,
    CANDIDATE_COUNT,
    CAUSAL_ENDPOINT_LAG,
    DETECTOR_ID,
    DYNAMIC_CANDIDATE_COUNT,
    EMBEDDING_CYCLE_SIZES,
    FORMATION_HORIZON,
    GRAMMAR_ID,
    INPUT_PORTS,
    MAX_LAYERS_PER_CANDIDATE,
    PARENT_EXACT_RESULT_SHA256,
    PRIMARY_CONE_SATURATION_LAYER,
    PRIMARY_CYCLE_SIZE,
    PROTOCOL_VERSION,
    RESULT_PATH_REF,
    SEARCH_ID,
    SHELL_SIZES,
    SIGNATURE_ORDER,
    strict_pre_wrap_horizon,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC_ROOT = (
    ROOT / "specs" / "icp_minimal_realization_role_succession" / "v0.1-draft"
)


def load_spec(name: str) -> dict[str, object]:
    return json.loads((SPEC_ROOT / name).read_text(encoding="ascii"))


class FrozenSpecContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.protocol = load_spec("protocol.json")
        cls.grammar = load_spec("grammar.json")
        cls.topology = load_spec("topology.json")
        cls.detector = load_spec("detector.json")
        cls.partitions = load_spec("partitions.json")
        cls.fixtures = load_spec("development_fixtures.json")
        cls.result_schema = load_spec("result.schema.json")

    def test_versions_and_registered_identities_do_not_drift(self) -> None:
        for name, document in (
            ("protocol", self.protocol),
            ("grammar", self.grammar),
            ("topology", self.topology),
            ("detector", self.detector),
            ("partitions", self.partitions),
            ("fixtures", self.fixtures),
        ):
            with self.subTest(document=name):
                self.assertEqual(document["protocol_version"], PROTOCOL_VERSION)

        properties = self.result_schema["properties"]
        self.assertEqual(properties["protocol_version"]["const"], PROTOCOL_VERSION)
        self.assertEqual(
            properties["base_contract_version"]["const"], BASE_CONTRACT_VERSION
        )
        self.assertEqual(self.protocol["base_contract_version"], BASE_CONTRACT_VERSION)
        self.assertEqual(self.protocol["search_id"], SEARCH_ID)
        self.assertEqual(self.partitions["search_id"], SEARCH_ID)
        self.assertEqual(properties["search_id"]["const"], SEARCH_ID)
        self.assertEqual(self.grammar["grammar_id"], GRAMMAR_ID)
        self.assertEqual(properties["grammar_id"]["const"], GRAMMAR_ID)
        self.assertEqual(self.detector["detector_id"], DETECTOR_ID)
        self.assertEqual(properties["detector"]["const"], DETECTOR_ID)
        self.assertEqual(self.protocol["registered_result_path"], RESULT_PATH_REF)
        self.assertEqual(
            self.protocol["parent_result_sha256"], PARENT_EXACT_RESULT_SHA256
        )

    def test_candidate_allocation_is_identical_in_every_frozen_surface(self) -> None:
        shell_mapping = self.grammar["candidate_space"]["shell_sizes_by_n_l"]
        grammar_shells = tuple(shell_mapping[str(index)] for index in range(9))
        allocation = self.result_schema["properties"]["candidate_allocation"][
            "properties"
        ]
        primary = self.partitions["primary"]

        self.assertEqual(len(SIGNATURE_ORDER), 8)
        self.assertEqual(SHELL_SIZES, tuple(math.comb(8, index) for index in range(9)))
        self.assertEqual(grammar_shells, SHELL_SIZES)
        self.assertEqual(self.protocol["candidate_count"], CANDIDATE_COUNT)
        self.assertEqual(
            self.grammar["candidate_space"]["candidate_count"], CANDIDATE_COUNT
        )
        self.assertEqual(primary["candidate_rule_numbers"]["count"], CANDIDATE_COUNT)
        self.assertEqual(allocation["candidate_count"]["const"], CANDIDATE_COUNT)
        self.assertEqual(
            self.protocol["dynamic_candidate_count"], DYNAMIC_CANDIDATE_COUNT
        )
        self.assertEqual(
            self.grammar["candidate_space"]["dynamic_candidate_count"],
            DYNAMIC_CANDIDATE_COUNT,
        )
        self.assertEqual(primary["dynamic_candidate_count"], DYNAMIC_CANDIDATE_COUNT)
        self.assertEqual(
            allocation["dynamic_candidate_count"]["const"],
            DYNAMIC_CANDIDATE_COUNT,
        )
        self.assertEqual(tuple(allocation["shell_sizes"]["const"]), SHELL_SIZES)

    def test_topology_horizons_and_size_panel_do_not_drift(self) -> None:
        properties = self.result_schema["properties"]
        boundary_fixture = next(
            fixture
            for fixture in self.fixtures["fixtures"]
            if fixture["id"] == "primary_cone_strict_pre_wrap_boundary"
        )

        self.assertEqual(self.protocol["primary_cycle_size"], PRIMARY_CYCLE_SIZE)
        self.assertEqual(self.topology["primary_cycle_size"], PRIMARY_CYCLE_SIZE)
        self.assertEqual(self.partitions["primary"]["cycle_size"], PRIMARY_CYCLE_SIZE)
        self.assertEqual(properties["primary_cycle_size"]["const"], PRIMARY_CYCLE_SIZE)
        self.assertEqual(self.protocol["canonical_origin"], CANONICAL_ORIGIN)
        self.assertEqual(
            self.topology["canonical_seed"]["origin"], CANONICAL_ORIGIN
        )
        self.assertEqual(properties["canonical_origin"]["const"], CANONICAL_ORIGIN)
        self.assertEqual(
            tuple(self.protocol["cross_size_controls"]), EMBEDDING_CYCLE_SIZES
        )
        self.assertEqual(
            tuple(self.partitions["conditional_size_controls"]["cycle_sizes"]),
            EMBEDDING_CYCLE_SIZES,
        )
        self.assertEqual(
            tuple(properties["embedding_cycle_sizes"]["const"]),
            EMBEDDING_CYCLE_SIZES,
        )
        self.assertEqual(
            self.protocol["pre_wrap_formation_horizon"], FORMATION_HORIZON
        )
        self.assertEqual(
            self.detector["pre_wrap"]["maximum_formation_layer"],
            FORMATION_HORIZON,
        )
        self.assertEqual(properties["formation_horizon"]["const"], FORMATION_HORIZON)
        self.assertEqual(
            boundary_fixture["last_pre_wrap_formation_layer"], FORMATION_HORIZON
        )
        self.assertEqual(
            boundary_fixture["last_pre_wrap_endpoint_layer"],
            FORMATION_HORIZON + CAUSAL_ENDPOINT_LAG,
        )
        self.assertLess(
            2 * (FORMATION_HORIZON + CAUSAL_ENDPOINT_LAG), PRIMARY_CYCLE_SIZE
        )
        self.assertGreaterEqual(
            2 * (FORMATION_HORIZON + 1 + CAUSAL_ENDPOINT_LAG), PRIMARY_CYCLE_SIZE
        )
        self.assertEqual(
            self.protocol["cone_saturation_layer"], PRIMARY_CONE_SATURATION_LAYER
        )
        self.assertEqual(
            self.topology["centered_cone"]["saturation_layer_primary"],
            PRIMARY_CONE_SATURATION_LAYER,
        )
        self.assertEqual(
            properties["cone_saturation_layer"]["const"],
            PRIMARY_CONE_SATURATION_LAYER,
        )
        self.assertEqual(
            self.protocol["max_layers_per_dynamic_candidate"],
            MAX_LAYERS_PER_CANDIDATE,
        )
        self.assertEqual(
            properties["max_layers_per_candidate"]["const"],
            MAX_LAYERS_PER_CANDIDATE,
        )

    def test_strict_pre_wrap_horizon_handles_odd_cycle_without_even_rounding(self) -> None:
        cycle_size = 65
        horizon = strict_pre_wrap_horizon(cycle_size)
        self.assertEqual(horizon, 30)
        self.assertLess(2 * (horizon + CAUSAL_ENDPOINT_LAG), cycle_size)
        self.assertGreaterEqual(
            2 * (horizon + 1 + CAUSAL_ENDPOINT_LAG),
            cycle_size,
        )

    def test_grammar_ports_resources_and_detector_intervention_do_not_drift(self) -> None:
        primitive = self.result_schema["properties"]["primitive_capacity"][
            "properties"
        ]
        properties = self.result_schema["properties"]
        resources = self.topology["resource_envelope"]
        intervention = self.detector["matched_interventions"]

        self.assertEqual(tuple(self.grammar["input_order"]), INPUT_PORTS)
        self.assertEqual(tuple(primitive["input_ports"]["const"]), INPUT_PORTS)
        self.assertEqual(self.grammar["fan_in"], len(INPUT_PORTS))
        self.assertEqual(resources["event_reads_per_site_tick"], len(INPUT_PORTS))
        self.assertEqual(primitive["local_signature_fan_in"]["const"], len(INPUT_PORTS))
        self.assertEqual(self.grammar["relation_incidence_reads_per_site_tick"], 2)
        self.assertEqual(resources["relation_incidence_reads_per_site_tick"], 2)
        self.assertEqual(primitive["relation_incidence_reads_per_site"]["const"], 2)
        self.assertEqual(
            self.grammar["candidate_space"]["definition"],
            "power set of the eight exact signatures",
        )
        self.assertEqual(primitive["truth_table_row_capacity"]["const"], 8)
        self.assertEqual(intervention["window_offsets"], [0, 1, 2])
        self.assertEqual(intervention["natural"], [1, 1, 0])
        self.assertEqual(intervention["role_preserving_sham"], [0, 1, 1])
        self.assertEqual(intervention["role_breaking"], [1, 0, 1])
        self.assertEqual(intervention["normal_evolution_ticks"], CAUSAL_ENDPOINT_LAG)
        self.assertEqual(
            self.detector["reachable_future"]["observation_layer"], "t+2"
        )
        self.assertEqual(properties["causal_endpoint_lag"]["const"], CAUSAL_ENDPOINT_LAG)


if __name__ == "__main__":
    unittest.main()
