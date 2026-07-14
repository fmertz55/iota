# Primary Literature Basis

Date reviewed: `2026-07-14`

Status: **pre-outcome design evidence only**

## Active construction basis

Pablo Arrighi, Marcelo Forets, and Vincent Nesme, “The Dirac equation as a
quantum walk: higher dimensions, observational convergence,” Journal of
Physics A 47 (2014) 465302, <https://arxiv.org/abs/1307.3524>.

Design use: product-form homogeneous causal quantum walk; explicit separation
of local mass rotation and directional translation; first-order state-vector
convergence; low-pass encoding/reconstruction discipline.

Not imported: any reported trajectory, numerical error, or experiment result.

## Adversarial comparison and alternative-family basis

Alessandro Bisio, Giacomo Mauro D'Ariano, and Alessandro Tosini, “Quantum Field
as a quantum cellular automaton: the Dirac free evolution in one dimension,”
Annals of Physics 354 (2015) 244–264,
<https://arxiv.org/abs/1212.2839>.

Design use: uniform comparison of discrete and Dirac unitary channels;
small-momentum/small-mass failure boundary; a direct non-product QCA family
reserved as a genuinely different follow-up.

Not imported: its discrimination bound as the result of the active product
candidate.

Alessandro Bisio, Giacomo Mauro D'Ariano, and Alessandro Tosini, “The Dirac
Quantum Cellular Automaton in one dimension: Zitterbewegung and scattering
from potential,” Physical Review A 88 (2013) 032301,
<https://arxiv.org/abs/1305.0461>.

Design use: Zitterbewegung and scalar-potential response are required
operational witnesses rather than optional visual examples.

Not imported: reported QCA witness outcomes.

Giacomo Mauro D'Ariano and Paolo Perinotti, “Derivation of the Dirac Equation
from Principles of Information Processing,” Physical Review A 90 (2014)
062106, <https://arxiv.org/abs/1306.1934>.

Design use: explicit quantum constraints and the low-momentum/low-mass
interpretation boundary.

Not imported: a claim that generic information implies quantum theory or that
the active construction is minimal.

## Family-separation rule

The active product walk has momentum update

```text
exp(-i delta k sigma_z) exp(-i delta m sigma_x).
```

The Bisio–D'Ariano–Tosini direct QCA has momentum update

```text
[[n exp(+i k), -i m], [-i m, n exp(-i k)]],  n^2+m^2=1.
```

They agree only in an appropriate continuum regime. They are not alternate
notations for one finite update. Code, results, or symmetry statements from
one family may not be used to validate the other.
