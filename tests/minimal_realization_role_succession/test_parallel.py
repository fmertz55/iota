from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.minimal_realization_role_succession import cli, runner, verifier
from src.minimal_realization_role_succession.manifest import compile_candidates
from src.minimal_realization_role_succession.protocol import (
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
    REGISTERED_WORKER_PROCESSES,
)


def synthetic_anf_payload(
    payload: tuple[int, tuple[str, ...], int],
) -> int:
    state, rows, cycle_size = payload
    return verifier._transition(state, rows, cycle_size)


def recurrence(rows: tuple[str, ...]):
    return runner.synthetic_candidate_evaluation(
        rows,
        runner.ExactOrbitOutcome(
            "recurrence_excluded_on_fixed_orbit",
            None,
            33,
            None,
            None,
            None,
            None,
            (32, 33, 1, 0, 0),
            "a" * 64,
        ),
    )


def bindings() -> dict[str, dict[str, str]]:
    result = {
        name: {
            "path": f"synthetic/{name}.json",
            "sha256": f"{index:x}" * 64,
        }
        for index, name in enumerate(
            (
                "open_manifest_binding",
                "outcome_seal_binding",
                "candidate_manifest_binding",
                "result_schema_binding",
            ),
            start=1,
        )
    }
    result["parent_exact_result_binding"] = {
        "path": PARENT_EXACT_RESULT_REF,
        "sha256": PARENT_EXACT_RESULT_SHA256,
    }
    return result


class FakeRegisteredExecutor:
    instances: list["FakeRegisteredExecutor"] = []

    def __init__(self, *, max_workers, mp_context):
        self.max_workers = max_workers
        self.mp_context = mp_context
        self.payloads = ()
        self.chunksize = None
        type(self).instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def map(self, _function, payloads, *, chunksize):
        self.payloads = tuple(payloads)
        self.chunksize = chunksize
        return tuple(recurrence(rows) for _candidate, rows in self.payloads)


class FakeVerificationExecutor(FakeRegisteredExecutor):
    def map(self, _function, payloads, *, chunksize):
        self.payloads = tuple(payloads)
        self.chunksize = chunksize
        return (None for _payload in self.payloads)


class PartialFailureExecutor(FakeRegisteredExecutor):
    def map(self, _function, payloads, *, chunksize):
        self.payloads = tuple(payloads)
        self.chunksize = chunksize

        def partial_results():
            _candidate, rows = self.payloads[0]
            yield recurrence(rows)
            raise RuntimeError("synthetic mid-pool failure")

        return partial_results()


class RegisteredParallelismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = compile_candidates()

    def setUp(self) -> None:
        FakeRegisteredExecutor.instances.clear()
        FakeVerificationExecutor.instances.clear()

    def test_registered_runner_collects_all_workers_in_canonical_order(self) -> None:
        context = object()
        with mock.patch.object(
            runner, "ProcessPoolExecutor", FakeRegisteredExecutor
        ), mock.patch.object(runner, "get_context", return_value=context):
            search = runner.run_development_search(
                self.candidates,
                runner.evaluate_candidate_exact_orbit,
                worker_processes=REGISTERED_WORKER_PROCESSES,
            )
        executor = FakeRegisteredExecutor.instances[-1]
        self.assertEqual(executor.max_workers, REGISTERED_WORKER_PROCESSES)
        self.assertIs(executor.mp_context, context)
        self.assertEqual(executor.chunksize, 1)
        self.assertEqual(len(executor.payloads), 255)
        self.assertEqual(
            [candidate["candidate_id"] for candidate, _rows in executor.payloads],
            [candidate["candidate_id"] for candidate in self.candidates[1:]],
        )
        self.assertEqual(len(search["candidate_results"]), 256)
        self.assertEqual(
            [record["candidate_id"] for record in search["candidate_results"]],
            [candidate["candidate_id"] for candidate in self.candidates],
        )

    def test_parallel_runner_rejects_nonregistered_evaluator(self) -> None:
        with self.assertRaisesRegex(runner.RoleSuccessionRunError, "registered evaluator"):
            runner.run_development_search(
                self.candidates,
                lambda _candidate, rows: recurrence(rows),
                worker_processes=REGISTERED_WORKER_PROCESSES,
            )

    def test_independent_replay_uses_same_canonical_worker_allocation(self) -> None:
        ledger = runner.build_result_ledger(
            candidates=self.candidates,
            evaluator=lambda _candidate, rows: recurrence(rows),
            **bindings(),
        )
        context = object()
        with mock.patch.object(
            verifier, "ProcessPoolExecutor", FakeVerificationExecutor
        ), mock.patch.object(verifier, "get_context", return_value=context):
            verifier.verify_ledger_independently(
                ledger,
                self.candidates,
                worker_processes=REGISTERED_WORKER_PROCESSES,
            )
        executor = FakeVerificationExecutor.instances[-1]
        self.assertEqual(executor.max_workers, REGISTERED_WORKER_PROCESSES)
        self.assertIs(executor.mp_context, context)
        self.assertEqual(executor.chunksize, 1)
        self.assertEqual(len(executor.payloads), 255)
        self.assertEqual(
            [payload[1]["candidate_id"] for payload in executor.payloads],
            [candidate["candidate_id"] for candidate in self.candidates[1:]],
        )

    def test_worker_count_has_no_override_surface(self) -> None:
        for invalid in (0, 2, 8, True):
            with self.subTest(invalid=invalid), self.assertRaises(
                (runner.RoleSuccessionRunError, verifier.IndependentVerificationError)
            ):
                runner.run_development_search(
                    self.candidates,
                    lambda _candidate, rows: recurrence(rows),
                    worker_processes=invalid,
                )

    def test_spawn_pool_executes_only_disclosed_synthetic_states(self) -> None:
        rows = ("001", "010", "100", "111")
        payloads = (
            ((1 << 3) | (1 << 9), rows, 16),
            ((1 << 2) | (1 << 7) | (1 << 13), rows, 16),
        )
        with ProcessPoolExecutor(
            max_workers=2,
            mp_context=get_context("spawn"),
        ) as executor:
            actual = tuple(executor.map(synthetic_anf_payload, payloads, chunksize=1))
        expected = tuple(
            runner.step(state, candidate_rows, cycle_size)
            for state, candidate_rows, cycle_size in payloads
        )
        self.assertEqual(actual, expected)

    def test_actual_spawn_adapters_payloads_and_return_types_are_picklable(self) -> None:
        candidate = self.candidates[1]
        rows = tuple(law["signature"] for law in candidate["laws"])
        evaluation = recurrence(rows)
        ledger = runner.build_result_ledger(
            candidates=self.candidates,
            evaluator=lambda _candidate, candidate_rows: recurrence(candidate_rows),
            **bindings(),
        )
        runner_payload = (candidate, rows)
        verifier_payload = (
            ledger["candidate_results"][1],
            candidate,
            rows,
        )

        for value in (
            runner._registered_evaluation_payload,
            verifier._independent_verification_payload,
            runner_payload,
            verifier_payload,
            evaluation,
        ):
            with self.subTest(value_type=type(value).__name__):
                restored = pickle.loads(pickle.dumps(value))
                self.assertEqual(restored, value)

    def test_partial_worker_failure_cannot_reach_ledger_or_result_writer(self) -> None:
        with mock.patch.object(
            runner, "ProcessPoolExecutor", PartialFailureExecutor
        ), mock.patch.object(runner, "get_context", return_value=object()):
            with self.assertRaisesRegex(
                runner.RoleSuccessionRunError,
                "worker pool failed before serialization",
            ):
                runner.build_result_ledger(
                    candidates=self.candidates,
                    evaluator=runner.evaluate_candidate_exact_orbit,
                    worker_processes=REGISTERED_WORKER_PROCESSES,
                    **bindings(),
                )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            open_manifest = {
                "parent_outcome_seal": {
                    "path": "synthetic/seal.json",
                    "sha256": "1" * 64,
                },
                "candidate_manifest": {
                    "path": "synthetic/candidates.jsonl",
                    "sha256": "2" * 64,
                },
                "result_schema": {
                    "path": "synthetic/schema.json",
                    "sha256": "3" * 64,
                },
                "parent_exact_result": {
                    "path": PARENT_EXACT_RESULT_REF,
                    "sha256": PARENT_EXACT_RESULT_SHA256,
                },
            }
            pool_failure = runner.RoleSuccessionRunError(
                "registered candidate worker pool failed before serialization"
            )
            with mock.patch.object(cli, "repository_root", return_value=root), mock.patch.object(
                cli, "load_open_manifest", return_value=open_manifest
            ), mock.patch.object(
                cli, "read_jsonl", return_value=self.candidates
            ), mock.patch.object(
                cli, "_binding", return_value={"path": "synthetic", "sha256": "4" * 64}
            ), mock.patch.object(
                runner, "build_result_ledger", side_effect=pool_failure
            ), mock.patch.object(
                runner, "write_result_ledger"
            ) as writer:
                with self.assertRaisesRegex(
                    runner.RoleSuccessionRunError,
                    "worker pool failed before serialization",
                ):
                    cli.command_run(None)
            writer.assert_not_called()
            result = root / cli.RESULT_PATH_REF
            self.assertFalse(result.exists())
            self.assertFalse(result.with_name(result.name + ".tmp").exists())


if __name__ == "__main__":
    unittest.main()
