# Core-295 candidate discovery batch 35: quantum wave mechanics and photon–electron scattering

**Date:** 2026-11-11  
**Status:** discovery-only source leads. None is added to the formal catalogue or counted toward 295.  
**Domain focus:** Physics.

## 1. Schrödinger stationary wave equation

**Primary source:** Erwin Schrödinger (1926), *Quantisierung als Eigenwertproblem. Erste Mitteilung*, Annalen der Physik 79, 361–376, DOI 10.1002/andp.19263840404.

The stationary, nonrelativistic Schrödinger equation is:
[
-\frac{\hbar^2}{2m}\nabla^2\psi(\mathbf r)
+V(\mathbf r)\psi(\mathbf r)
=E\psi(\mathbf r).
]
It is an eigenvalue PDE for the wavefunction (psi), with potential (V), particle mass (m), and energy eigenvalue (E).

**Boundary and risks:** nonrelativistic quantum mechanics, specified potential, domain and boundary conditions, normalizable wavefunction and appropriate self-adjoint Hamiltonian. The stationary eigenvalue equation and time-dependent evolution equation are linked representations of the same Schrödinger model; do not count energy eigenstates, time evolution and coordinate-specific reductions as separate candidates.

**Initial disposition:** high-value full-system lead; hold pending primary equation-page transcription, potential/boundary contract and a complex-valued PDE/eigenvalue adapter.

## 2. Compton wavelength shift

**Primary source:** Arthur H. Compton (1923), *A Quantum Theory of the Scattering of X-rays by Light Elements*, Physical Review 21, 483–502, DOI 10.1103/PhysRev.21.483.

The original paper's abstract gives:
[
\lambda_\theta-\lambda_0
=\frac{2h}{mc}\sin^2\left(\frac{\theta}{2}\right)
=\frac{h}{mc}(1-\cos\theta),
]
where (m) is the scattering-electron mass, (c) the speed of light, (h) Planck's constant, and (	heta) the scattering angle between incident and scattered rays. The wavelength shift is independent of the incident wavelength in the ideal free-electron model.

**Boundary and risks:** scattering from an electron treated as free or weakly bound; single-photon energy/momentum transfer; electron recoil; specify angle convention and incident/scattered wavelength. Bound-electron corrections, multiple scattering, binding energy and material effects require extensions.

**Structural value:** a kinematic relation for the wavelength shift in photon–electron scattering, distinct from Planck's blackbody spectral distribution and the de Broglie matter-wave relation. It is derived from energy–momentum conservation and is not a general optical path-difference equation.

**Initial disposition:** strong scalar Physics lead; hold pending source-page equation transcription and scattering-regime/range contract.

## 3. de Broglie matter-wave wavelength–momentum relation

**Primary source lineage:** Louis de Broglie, *Recherches sur la théorie des quanta* (doctoral thesis, 1924); first published paper, *A tentative theory of light quanta*, Philosophical Magazine 47 (1924), 446–458.

The familiar relation is:
[
\lambda=\frac{h}{p}.
]
A modern historical re-examination notes that this compact formula does not appear verbatim in de Broglie's 1924 Philosophical Magazine paper; it is derived from his phase-wave frequency/velocity construction and relativistic momentum. The thesis contains the nonrelativistic relation, while the relativistic form follows from the full momentum definition.

**Boundary and risks:** specify whether (p) is relativistic momentum or the nonrelativistic approximation; distinguish phase wavelength from group velocity and matter-packet propagation. Do not treat (E=h\nu), phase velocity, group velocity and (lambda=h/p) as separate independent candidate equations if the selected unit is the de Broglie matter-wave relation.

**Structural value:** a fundamental quantum kinematic relation between particle momentum and associated matter wavelength. It is not the Compton shift equation: Compton describes a change in photon wavelength after scattering; de Broglie associates a wavelength with a particle's momentum.

**Initial disposition:** promising scalar Physics lead; hold until the thesis page-level transcription and exact relativistic/nonrelativistic convention are fixed.

## 4. Batch-level family decisions

| Lead | Structure | Main issue | Initial decision |
|---|---|---|---|
| Schrödinger stationary equation | Complex-valued linear eigenvalue PDE | Full spatial domain, potential, boundary and normalization contract | Hold; high priority |
| Compton shift | (1-cos\theta) photon–electron scattering wavelength shift | Free/weakly bound electron assumptions and angle convention | Hold; consider |
| de Broglie relation | Particle wavelength inversely proportional to momentum | Original formula provenance and relativistic momentum convention | Hold; consider |

These are three source leads, not three accepted equations. Schrödinger time-dependent/stationary forms are one wave-mechanics family; Compton shift is one scattering relation; de Broglie phase/group-wave quantities are one matter-wave family. Do not count derived forms or parameter/coordinate variants separately.

## 5. Catalogue status and work not performed

No source-register or equation-catalogue record was changed. The formal manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls, X-ray scattering measurements or quantum simulations were run. This is source discovery only.
