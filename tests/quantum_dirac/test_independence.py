from __future__ import annotations

import inspect
import subprocess
import sys
import unittest

from mpmath import mp

from src.quantum_dirac import independent_registered, independent_verifier
from src.quantum_dirac.independent_registered import _SparseOperator


class IndependentImplementationTests(unittest.TestCase):
    def test_registered_replay_imports_no_production_matrix_constructor(self) -> None:
        source = inspect.getsource(independent_registered)
        self.assertNotIn("from .candidate", source)
        self.assertNotIn("from .target", source)
        self.assertNotIn("from .production", source)

    def test_clean_checkpoint_verifier_imports_no_primary_engine(self) -> None:
        source = inspect.getsource(independent_verifier)
        self.assertNotIn("from .certified", source)
        self.assertNotIn("from .runner", source)
        self.assertNotIn("from .production", source)

    def test_clean_checkpoint_verifier_import_graph_is_primary_free(self) -> None:
        script = """
import sys
import src.quantum_dirac.independent_verifier
for name in (
    'src.quantum_dirac.candidate',
    'src.quantum_dirac.certified',
    'src.quantum_dirac.production',
    'src.quantum_dirac.reducers',
    'src.quantum_dirac.runner',
    'src.quantum_dirac.target',
):
    if name in sys.modules:
        raise SystemExit('primary module loaded: ' + name)
"""
        subprocess.run([sys.executable, "-c", script], check=True)

    def test_sparse_operator_applies_declared_entries(self) -> None:
        operator = _SparseOperator(3, ((0, 1, 2), (1, 2, -1), (2, 0, 3)))
        value = mp.matrix([[5], [7], [11]])
        result = operator.apply(value)
        self.assertEqual([result[index] for index in range(3)], [14, -11, 15])


if __name__ == "__main__":
    unittest.main()
