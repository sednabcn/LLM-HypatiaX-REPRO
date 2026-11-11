# Core-295 candidate discovery batch 22: Chemistry Marcus electron-transfer kinetics

**Status:** primary-source and authoritative-definition tracing only. No equation is accepted or counted toward the 59 Chemistry target.

## 1. Marcus outer-sphere electron-transfer relation

**Primary sources:**
- Marcus, “On the theory of oxidation-reduction reactions involving electron transfer. I,” *The Journal of Chemical Physics* 24(5) (1956), 966–978, DOI [10.1063/1.1742723](https://doi.org/10.1063/1.1742723).
- Marcus, “On the theory of electron-transfer reactions. VI. Unified treatment for homogeneous and electrode reactions,” *The Journal of Chemical Physics* 43(2) (1965), 679–701, DOI [10.1063/1.1696792).
- Modern authoritative definition: [IUPAC Gold Book, Marcus equation](https://goldbook.iupac.org/terms/view/M03702).

In the classical high-temperature nonadiabatic limit, the electron-transfer rate is:

\[
k_{ET}=
\frac{2\pi}{\hbar}|V|^2
\frac{1}{\sqrt{4\pi\lambda k_BT}}
\exp\left[-\frac{(\lambda+\Delta G^\circ)^2}{4\lambda k_BT}\right],
\]

where \(V\) is electronic coupling, \(\lambda\) the total reorganization energy, \(\Delta G^\circ\) the reaction Gibbs energy, \(k_B\) Boltzmann's constant, \(T\) absolute temperature and \(\hbar\) reduced Planck's constant.

The same model is often expressed through an activation free energy:

\[
\Delta G^\ddagger=
\frac{(\lambda+\Delta G^\circ)^2}{4\lambda},
\qquad
k_{ET}=\kappa\frac{k_BT}{h}
\exp\left(-\frac{\Delta G^\ddagger}{RT}\right),
\]

with transmission coefficient \(\kappa\) and Planck constant \(h\). The first expression is the nonadiabatic golden-rule form; the second is the transition-state-style form used in the IUPAC definition. They are related formulations, not independent equations.

## 2. Electrochemical extension and historical scope

Marcus's 1965 Part VI develops a unified treatment of homogeneous and electrode electron-transfer rates. It is a primary extension of the 1956 outer-sphere theory, not a separate independent equation family. The electrochemical context introduces electrode potential, interfacial reorganization, electronic coupling and solvent response; the applicable form depends on the model and reaction regime.

**Boundary:** do not treat Marcus theory as merely a reparameterized Arrhenius equation. Its activation barrier depends quadratically on the reaction free-energy change and the reorganization energy, yielding the normal and inverted regions. Nevertheless, Arrhenius is a Core-15 exclusion; acceptance must explicitly demonstrate structural distinction from the excluded rate law and preserve the electron-transfer-specific state variables and assumptions.

## 3. Relation to Butler–Volmer and Nernst families

- Nernst gives the equilibrium potential/thermodynamic relation; Butler–Volmer gives current-overpotential kinetics near an electrode; Marcus theory describes electron-transfer rates through reorganization energy and electronic coupling.
- The Marcus 1965 electrochemical extension can inform electrode rate constants, but it is not automatically identical to the Butler–Volmer law. The latter often assumes exponential activation dependence on overpotential with transfer coefficients; Marcus includes a parabolic free-energy surface and may predict inverted-region behaviour.
- The Marcus activation-free-energy expression and nonadiabatic rate form are linked representations. Do not count them separately.
- Do not count each choice of donor/acceptor, solvent, reorganization energy or electronic coupling as a new equation.

## Acceptance requirements

Specify outer-sphere versus inner-sphere transfer, adiabatic/nonadiabatic regime, electronic coupling, inner/outer-sphere reorganization energies, standard Gibbs energy, temperature, solvent dielectric response, electrode potential if applicable, and valid driving-force range. Verify the exact equation and approximation regime in the primary paper before acceptance. Distinguish Marcus's original derivation from modern IUPAC notation and later quantum-vibrational corrections in the inverted region.

All records remain candidates. No Chemistry entry is accepted; no experiment or workflow has been run.
