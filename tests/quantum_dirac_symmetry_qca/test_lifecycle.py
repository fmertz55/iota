from __future__ import annotations

import unittest
import subprocess
import tempfile
import inspect
from pathlib import Path

from src.quantum_dirac_symmetry_qca.authorization import (
    RegisteredEvaluationPermit,
    authorization_status,
    issue_registered_permit,
    issue_verification_permit,
    validate_registered_permit,
)
from src.quantum_dirac_symmetry_qca import cli
from src.quantum_dirac_symmetry_qca.cli import build_parser
from src.quantum_dirac_symmetry_qca.lifecycle import expected_open_manifest
from src.quantum_dirac_symmetry_qca.protocol import (
    CONFIRMATION_OPEN_REF,
    CONFIRMATION_RESULT_REF,
    CONTRACT_REF,
    DEVELOPMENT_OPEN_REF,
    DEVELOPMENT_RESULT_REF,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    SPEC_DIR_REF,
)
from src.quantum_dirac_symmetry_qca.seal import verify_outcome_seal
from src.quantum_dirac_symmetry_qca.spec import (
    SymmetryQCASpecError,
    write_canonical_json_once,
)
from src.quantum_dirac_symmetry_qca.states import build_certified_state
from src.quantum_dirac_symmetry_qca.independent_states import build_independent_state


ROOT = Path(__file__).resolve().parents[2]


class DisabledLifecycleTests(unittest.TestCase):
    def test_current_checkout_has_no_authorization_or_stage_opening(self) -> None:
        status = authorization_status(ROOT)
        self.assertFalse(status["registered_outcomes_authorized"])
        self.assertFalse(status["evaluation_permit_issued"])
        self.assertFalse(status["verification_permit_issued"])
        seal_path = ROOT / OUTCOME_SEAL_REF
        if seal_path.exists():
            seal = verify_outcome_seal(ROOT)
            self.assertFalse(seal["run_command_enabled"])
        for relative in (
            DEVELOPMENT_OPEN_REF,
            DEVELOPMENT_RESULT_REF,
            CONFIRMATION_OPEN_REF,
            CONFIRMATION_RESULT_REF,
        ):
            self.assertFalse((ROOT / relative).exists())

    def test_permit_dataclass_cannot_be_forged(self) -> None:
        forged = RegisteredEvaluationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="1" * 40,
            opening_sha256="2" * 64,
            _nonce=object(),
        )
        with self.assertRaises(SymmetryQCASpecError):
            validate_registered_permit(forged)
        with self.assertRaises(SymmetryQCASpecError):
            build_certified_state(
                forged,
                state_id="DEV-DIRECT-STATE-POS",
                initial_mass=__import__("fractions").Fraction(1, 3),
            )
        with self.assertRaises(SymmetryQCASpecError):
            build_independent_state(
                forged,
                state_id="DEV-DIRECT-STATE-POS",
                initial_mass=__import__("fractions").Fraction(1, 3),
            )

    def test_cli_exposes_only_permit_gated_registered_commands(self) -> None:
        commands = set(build_parser()._subparsers._group_actions[0].choices)
        self.assertEqual(
            commands,
            {
                "audit-design",
                "validate-manifests",
                "preview-disabled-seal",
                "authorization-status",
                "seal-outcomes",
                "verify-seal",
                "open-stage",
                "authorize-stage",
                "run-stage",
                "verify-result",
            },
        )
        self.assertIn("run-stage", commands)
        self.assertIn("verify-result", commands)
        source = inspect.getsource(cli._run)
        self.assertLess(
            source.index("issue_registered_permit"),
            source.index("from .runner import build_stage_ledger"),
        )


class GitLinearPermitTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def _commit(self, root: Path, message: str) -> str:
        self._git(root, "add", "--all")
        self._git(
            root,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-m",
            message,
        )
        return self._git(root, "rev-parse", "HEAD")

    def test_development_evaluation_and_verification_permits_follow_exact_commits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            contract = root / CONTRACT_REF
            contract.parent.mkdir(parents=True)
            contract.write_text("fixture contract\n", encoding="utf-8")
            spec_dir = root / SPEC_DIR_REF
            spec_dir.mkdir(parents=True)
            for filename in (
                "protocol.json",
                "candidate.json",
                "target.json",
                "maps.json",
                "scenarios.json",
                "states.json",
                "partitions.json",
                "result.schema.json",
            ):
                (spec_dir / filename).write_text("{}\n", encoding="ascii")
            implementation = self._commit(root, "fixture implementation")

            write_canonical_json_once(
                root / OUTCOME_SEAL_REF,
                {
                    "freeze_parent_commit": implementation,
                    "required_freeze_tag": FREEZE_TAG,
                    "run_command_enabled": False,
                },
            )
            freeze = self._commit(root, "fixture freeze")
            self._git(
                root,
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "tag",
                "-a",
                FREEZE_TAG,
                "-m",
                "fixture freeze tag",
            )
            write_canonical_json_once(
                root / DEVELOPMENT_OPEN_REF,
                expected_open_manifest(
                    root,
                    stage="development",
                    freeze=freeze,
                    stage_parent=freeze,
                ),
            )
            opening = self._commit(root, "fixture development opening")
            evaluation = issue_registered_permit(stage="development", root=root)
            self.assertEqual(evaluation.freeze_commit, freeze)
            self.assertEqual(evaluation.opening_commit, opening)

            result = root / DEVELOPMENT_RESULT_REF
            result.parent.mkdir(parents=True)
            result.write_text("{}\n", encoding="ascii")
            result_commit = self._commit(root, "fixture development result")
            verification = issue_verification_permit(stage="development", root=root)
            self.assertEqual(verification.result_commit, result_commit)
            result.write_text('{"tampered":true}\n', encoding="ascii")
            with self.assertRaises(SymmetryQCASpecError):
                issue_verification_permit(stage="development", root=root)


if __name__ == "__main__":
    unittest.main()
