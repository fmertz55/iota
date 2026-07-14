"""Static local impossibility certificates for role succession.

The analyzer in this module is deliberately trajectory-free.  It does not read
candidate or result artifacts and it does not import the registered detector.
It works directly from one radius-one binary truth table.

For a putative formation anchor ``a``, every complete detector pass requires
the current seeded pattern ``0,1,1,0`` at offsets ``-1..+2`` and a quiescent
intervention guard at ``+3``.  Radius-one succession and the two-layer causal
endpoint can then depend only on the eight distinct offsets ``-2..+5``.  The
three unfixed bits give exactly eight contexts.

There are two exact exclusion routes:

* If row ``000`` is selected, an attributed current role forces the spatially
  homogeneous comparator to be zero.  Its next value is then one everywhere,
  so no raw seeded successor can be attributed.
* Otherwise, the comparator remains zero and exhaustive evaluation of the
  eight contexts is sufficient.  If no context has both an attributed
  successor and a sham-versus-breaking endpoint difference, no global state
  can supply a complete local witness.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Optional


CERTIFICATE_VERSION = "MIR-RS-STATIC-LOCAL-IMPOSSIBILITY-V0.1"
SIGNATURE_ORDER = tuple(f"{value:03b}" for value in range(8))
VALID_SIGNATURES = frozenset(SIGNATURE_ORDER)

CONTEXT_OFFSETS = (-2, -1, 0, 1, 2, 3, 4, 5)
FIXED_ROLE_OFFSETS = (-1, 0, 1, 2)
FIXED_ROLE_PATTERN = (0, 1, 1, 0)
ENDPOINT_GUARD_OFFSET = 3
ENDPOINT_GUARD_VALUE = 0
SUCCESSOR_DISPLACEMENTS = (0, 1)

HOMOGENEOUS_COMPARATOR_OBSTRUCTION = "homogeneous_comparator_obstruction"
EMPTY_LOCAL_PASS_CONTEXT_SET = "empty_local_pass_context_set"


def _require_bit(value: int, name: str) -> int:
    if type(value) is not int or value not in (0, 1):
        raise ValueError(f"{name} must be the integer bit zero or one")
    return value


def _normalize_rows(rows: Iterable[str]) -> tuple[str, ...]:
    if isinstance(rows, (str, bytes)):
        raise TypeError("production rows must be an iterable of signatures")
    try:
        supplied = tuple(rows)
    except TypeError as exc:
        raise TypeError("production rows must be an iterable of signatures") from exc
    unknown = {
        row
        for row in supplied
        if type(row) is not str or row not in VALID_SIGNATURES
    }
    if unknown:
        rendered = sorted(repr(row) for row in unknown)
        raise ValueError(f"unknown production signatures: {rendered}")
    selected = frozenset(supplied)
    return tuple(signature for signature in SIGNATURE_ORDER if signature in selected)


def _rule_number(rows: tuple[str, ...]) -> int:
    return sum(1 << int(signature, 2) for signature in rows)


def _truth_table_bit(
    rule_number: int,
    predecessor: int,
    self_value: int,
    successor: int,
) -> int:
    """Evaluate one truth-table entry without using the dynamic engine."""

    signature_id = (predecessor << 2) | (self_value << 1) | successor
    return (rule_number >> signature_id) & 1


def evaluate_truth_table_bit(
    rows: Iterable[str],
    predecessor: int,
    self_value: int,
    successor: int,
) -> int:
    """Return a rule's output bit for ``(predecessor,self,successor)``.

    This public evaluator is intentionally a direct bit lookup.  It shares no
    transition or detector implementation with the preregistered search.
    """

    normalized = _normalize_rows(rows)
    predecessor = _require_bit(predecessor, "predecessor")
    self_value = _require_bit(self_value, "self")
    successor = _require_bit(successor, "successor")
    return _truth_table_bit(
        _rule_number(normalized),
        predecessor,
        self_value,
        successor,
    )


@dataclass(frozen=True)
class ContextIdentity:
    """Canonical identity of one eight-bit local context."""

    context_id: int
    bitstring: str

    def to_dict(self) -> dict[str, object]:
        return {"context_id": self.context_id, "bitstring": self.bitstring}


@dataclass(frozen=True)
class LocalContextAssessment:
    """Truth-table findings for one canonical context."""

    context_id: int
    bitstring: str
    raw_seeded_successor_displacements: tuple[int, ...]
    attributed_successor_displacements: tuple[int, ...]
    sham_endpoint_bit: int
    breaking_endpoint_bit: int

    @property
    def identity(self) -> ContextIdentity:
        return ContextIdentity(self.context_id, self.bitstring)

    @property
    def raw_seeded_succession_capable(self) -> bool:
        return bool(self.raw_seeded_successor_displacements)

    @property
    def succession_capable(self) -> bool:
        return bool(self.attributed_successor_displacements)

    @property
    def causal_capable(self) -> bool:
        return self.sham_endpoint_bit != self.breaking_endpoint_bit

    @property
    def joint_pass_capable_displacements(self) -> tuple[int, ...]:
        if not self.causal_capable:
            return ()
        return self.attributed_successor_displacements

    @property
    def joint_pass_capable(self) -> bool:
        return bool(self.joint_pass_capable_displacements)

    def to_dict(self) -> dict[str, object]:
        return {
            "context_id": self.context_id,
            "bitstring": self.bitstring,
            "bits_by_offset": {
                str(offset): int(bit)
                for offset, bit in zip(CONTEXT_OFFSETS, self.bitstring)
            },
            "raw_seeded_successor_displacements": list(
                self.raw_seeded_successor_displacements
            ),
            "attributed_successor_displacements": list(
                self.attributed_successor_displacements
            ),
            "raw_seeded_succession_capable": self.raw_seeded_succession_capable,
            "succession_capable": self.succession_capable,
            "sham_endpoint_bit": self.sham_endpoint_bit,
            "breaking_endpoint_bit": self.breaking_endpoint_bit,
            "causal_capable": self.causal_capable,
            "joint_pass_capable_displacements": list(
                self.joint_pass_capable_displacements
            ),
            "joint_pass_capable": self.joint_pass_capable,
        }


@dataclass(frozen=True)
class LocalImpossibilityCertificate:
    """Auditable exhaustive certificate for one production rule."""

    production_rows: tuple[str, ...]
    rule_number: int
    formation_comparator_bit: int
    next_comparator_bit: int
    comparator_obstruction: bool
    context_universe: tuple[LocalContextAssessment, ...]

    def __post_init__(self) -> None:
        self.validate()

    @staticmethod
    def _select_contexts(
        contexts: tuple[LocalContextAssessment, ...],
        predicate: str,
    ) -> tuple[ContextIdentity, ...]:
        return tuple(
            context.identity
            for context in contexts
            if bool(getattr(context, predicate))
        )

    @property
    def raw_seeded_succession_capable_contexts(self) -> tuple[ContextIdentity, ...]:
        return self._select_contexts(
            self.context_universe,
            "raw_seeded_succession_capable",
        )

    @property
    def succession_capable_contexts(self) -> tuple[ContextIdentity, ...]:
        return self._select_contexts(self.context_universe, "succession_capable")

    @property
    def causal_capable_contexts(self) -> tuple[ContextIdentity, ...]:
        return self._select_contexts(self.context_universe, "causal_capable")

    @property
    def joint_pass_capable_contexts(self) -> tuple[ContextIdentity, ...]:
        return self._select_contexts(self.context_universe, "joint_pass_capable")

    @property
    def symbolically_unreachable(self) -> bool:
        """Whether the certificate proves all future passes unreachable."""

        return not self.joint_pass_capable_contexts

    @property
    def proof_route(self) -> Optional[str]:
        if not self.symbolically_unreachable:
            return None
        if self.comparator_obstruction:
            return HOMOGENEOUS_COMPARATOR_OBSTRUCTION
        return EMPTY_LOCAL_PASS_CONTEXT_SET

    @property
    def proof_statement(self) -> Optional[str]:
        if self.proof_route == HOMOGENEOUS_COMPARATOR_OBSTRUCTION:
            return (
                "An attributed formation role forces the homogeneous comparator "
                "bit to 0; selected row 000 maps it to 1 at the next layer, "
                "blocking attribution of every raw seeded successor."
            )
        if self.proof_route == EMPTY_LOCAL_PASS_CONTEXT_SET:
            return (
                "None of the eight exhaustive radius-one contexts jointly has "
                "an attributed next-layer successor and a two-layer matched-arm "
                "endpoint difference."
            )
        return None

    def validate(self) -> None:
        """Raise if any field or exact-certificate invariant is inconsistent."""

        normalized = _normalize_rows(self.production_rows)
        if normalized != self.production_rows:
            raise ValueError("production_rows must be unique and canonical")
        if self.rule_number != _rule_number(normalized):
            raise ValueError("rule_number does not encode production_rows")
        if self.formation_comparator_bit != 0:
            raise ValueError("attributed formation roles require comparator bit zero")
        expected_next_comparator = _truth_table_bit(self.rule_number, 0, 0, 0)
        if self.next_comparator_bit != expected_next_comparator:
            raise ValueError("next_comparator_bit is not the direct 000 evaluation")
        if self.comparator_obstruction != (self.next_comparator_bit == 1):
            raise ValueError("comparator obstruction flag is inconsistent")

        expected_bitstrings = _canonical_context_bitstrings()
        actual_bitstrings = tuple(
            context.bitstring for context in self.context_universe
        )
        if actual_bitstrings != expected_bitstrings:
            raise ValueError(
                "context universe is not the canonical eight-context order"
            )

        for context in self.context_universe:
            if context.context_id != int(context.bitstring, 2):
                raise ValueError("context ID does not encode its eight-bit string")
            if context.raw_seeded_successor_displacements not in (
                (),
                (0,),
                (1,),
                (0, 1),
            ):
                raise ValueError("raw successor displacements are not canonical")
            if context.attributed_successor_displacements not in (
                (),
                (0,),
                (1,),
                (0, 1),
            ):
                raise ValueError("attributed successor displacements are not canonical")
            if self.comparator_obstruction:
                if context.attributed_successor_displacements:
                    raise ValueError("comparator obstruction must block attribution")
            elif (
                context.attributed_successor_displacements
                != context.raw_seeded_successor_displacements
            ):
                raise ValueError("zero comparator must preserve raw attribution")
            _require_bit(context.sham_endpoint_bit, "sham_endpoint_bit")
            _require_bit(context.breaking_endpoint_bit, "breaking_endpoint_bit")

        # This is the theorem's central iff, checked on every constructed
        # certificate rather than left to a downstream consumer.
        joint_is_empty = len(self.joint_pass_capable_contexts) == 0
        if self.symbolically_unreachable != joint_is_empty:
            raise ValueError(
                "symbolic reachability is not equivalent to joint emptiness"
            )
        if self.symbolically_unreachable and self.proof_route not in (
            HOMOGENEOUS_COMPARATOR_OBSTRUCTION,
            EMPTY_LOCAL_PASS_CONTEXT_SET,
        ):
            raise ValueError("symbolic exclusion lacks a registered proof route")
        if not self.symbolically_unreachable and self.proof_route is not None:
            raise ValueError("non-exclusion certificates cannot claim a proof route")

    def to_dict(self) -> dict[str, object]:
        def identities(values: tuple[ContextIdentity, ...]) -> list[dict[str, object]]:
            return [value.to_dict() for value in values]

        return {
            "certificate_version": CERTIFICATE_VERSION,
            "production_rows": list(self.production_rows),
            "rule_number": self.rule_number,
            "context_offsets": list(CONTEXT_OFFSETS),
            "fixed_role_offsets": list(FIXED_ROLE_OFFSETS),
            "fixed_role_pattern": list(FIXED_ROLE_PATTERN),
            "endpoint_guard_offset": ENDPOINT_GUARD_OFFSET,
            "endpoint_guard_value": ENDPOINT_GUARD_VALUE,
            "successor_displacements": list(SUCCESSOR_DISPLACEMENTS),
            "formation_comparator_bit": self.formation_comparator_bit,
            "next_comparator_bit": self.next_comparator_bit,
            "comparator_obstruction": self.comparator_obstruction,
            "proof_route": self.proof_route,
            "proof_statement": self.proof_statement,
            "symbolically_unreachable": self.symbolically_unreachable,
            "context_universe": [
                context.to_dict() for context in self.context_universe
            ],
            "raw_seeded_succession_capable_contexts": identities(
                self.raw_seeded_succession_capable_contexts
            ),
            "succession_capable_contexts": identities(
                self.succession_capable_contexts
            ),
            "causal_capable_contexts": identities(self.causal_capable_contexts),
            "joint_pass_capable_contexts": identities(
                self.joint_pass_capable_contexts
            ),
        }


def _canonical_context_bitstrings() -> tuple[str, ...]:
    bitstrings = []
    for far_predecessor, far_successor, second_far_successor in product(
        (0, 1),
        repeat=3,
    ):
        values = {
            -2: far_predecessor,
            -1: 0,
            0: 1,
            1: 1,
            2: 0,
            3: 0,
            4: far_successor,
            5: second_far_successor,
        }
        bitstrings.append("".join(str(values[offset]) for offset in CONTEXT_OFFSETS))
    return tuple(bitstrings)


def _context_values(bitstring: str) -> dict[int, int]:
    return {
        offset: int(bit)
        for offset, bit in zip(CONTEXT_OFFSETS, bitstring)
    }


def _raw_successor_displacements(
    rule_number: int,
    formation: dict[int, int],
) -> tuple[int, ...]:
    def next_bit(offset: int) -> int:
        return _truth_table_bit(
            rule_number,
            formation[offset - 1],
            formation[offset],
            formation[offset + 1],
        )

    output = []
    for displacement in SUCCESSOR_DISPLACEMENTS:
        pattern = tuple(
            next_bit(displacement + relative)
            for relative in FIXED_ROLE_OFFSETS
        )
        if pattern == FIXED_ROLE_PATTERN:
            output.append(displacement)
    return tuple(output)


def _matched_arm_endpoint(
    rule_number: int,
    formation: dict[int, int],
    arm: tuple[int, int, int],
) -> int:
    arm_state = dict(formation)
    for offset, value in zip((0, 1, 2), arm):
        arm_state[offset] = value

    # The radius-one causal diamond for endpoint a+3 after two layers is
    # y[a+2], y[a+3], y[a+4], each read directly from the arm state.
    first_layer = {}
    for offset in (2, 3, 4):
        first_layer[offset] = _truth_table_bit(
            rule_number,
            arm_state[offset - 1],
            arm_state[offset],
            arm_state[offset + 1],
        )
    return _truth_table_bit(
        rule_number,
        first_layer[2],
        first_layer[3],
        first_layer[4],
    )


def analyze_local_impossibility(
    rows: Iterable[str],
) -> LocalImpossibilityCertificate:
    """Build the exact static local certificate for ``rows``.

    A false ``symbolically_unreachable`` value is deliberately not a dynamic
    existence claim.  It means only that this necessary-local-condition audit
    cannot exclude the rule; a trajectory or recurrence proof is still needed.
    """

    normalized = _normalize_rows(rows)
    rule_number = _rule_number(normalized)
    formation_comparator_bit = 0
    next_comparator_bit = _truth_table_bit(rule_number, 0, 0, 0)
    comparator_obstruction = next_comparator_bit == 1

    contexts = []
    for bitstring in _canonical_context_bitstrings():
        formation = _context_values(bitstring)
        raw_displacements = _raw_successor_displacements(rule_number, formation)
        attributed_displacements = () if comparator_obstruction else raw_displacements
        sham_endpoint = _matched_arm_endpoint(
            rule_number,
            formation,
            (0, 1, 1),
        )
        breaking_endpoint = _matched_arm_endpoint(
            rule_number,
            formation,
            (1, 0, 1),
        )
        contexts.append(
            LocalContextAssessment(
                context_id=int(bitstring, 2),
                bitstring=bitstring,
                raw_seeded_successor_displacements=raw_displacements,
                attributed_successor_displacements=attributed_displacements,
                sham_endpoint_bit=sham_endpoint,
                breaking_endpoint_bit=breaking_endpoint,
            )
        )

    return LocalImpossibilityCertificate(
        production_rows=normalized,
        rule_number=rule_number,
        formation_comparator_bit=formation_comparator_bit,
        next_comparator_bit=next_comparator_bit,
        comparator_obstruction=comparator_obstruction,
        context_universe=tuple(contexts),
    )
