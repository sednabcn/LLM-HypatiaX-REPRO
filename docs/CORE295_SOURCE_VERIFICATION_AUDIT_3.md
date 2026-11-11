# Core-295 source verification audit 3: mechanistic and system-level candidates

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** selected records already present in the 128-source register. This audit checks source identity, equation/model structure and eligibility implications; it does not complete variable-range, generator or numerical validation.

## 1. Chemistry: Langmuir–Hinshelwood versus Eley–Rideal surface kinetics

### 1.1 Langmuir–Hinshelwood (two adsorbed reactants)

Wachs (2024), *The Conundrum of “Pair Sites” in Langmuir–Hinshelwood Reaction Kinetics in Heterogeneous Catalysis*, explicitly gives two adsorption equilibria, a surface reaction between adsorbed R1* and R2*, and the site balance
\[
[*]_o=[*]+[R_1^*]+[R_2^*].
\]
Under the paper's stated mechanism, the product-formation rate is
\[
\frac{dP}{dt}=
\frac{k_{rds}K_{R1}K_{R2}P_{R1}P_{R2}[*]_o^2}
{(1+K_{R1}P_{R1}+K_{R2}P_{R2})^2}.
\]
The exact rate expression is Equation 5 in Wachs (2024), *ACS Catalysis* 14(13), 10260–10270, DOI 10.1021/acscatal.4c02813. The source explicitly states that both reactants adsorb and the rate-determining step consumes the two adsorbed species. This is an equation-level source, but it is a modern mechanistic treatment, not the original historical derivation of all Langmuir–Hinshelwood models.

### 1.2 Eley–Rideal (one adsorbed, one gas-phase reactant)

The Eley–Rideal mechanism instead has A adsorbed on a site and gas-phase B reacting directly with A*. Under rapid adsorption equilibrium, an irreversible rate-limiting surface reaction, a single-site balance, and no competing adsorbate in the simplest case:
\[
\theta_A=\frac{K_Ap_A}{1+K_Ap_A},
\qquad
r=k\theta_Ap_B
=\frac{kK_Ap_Ap_B}{1+K_Ap_A}.
\]
The IIT/IISc NPTEL course notes show the elementary steps A + S ⇌ AS and AS + B(g) → P, then derive the coverage and rate from the vacant-site balance. The Oxford Chemistry Primers solution source also shows how competing product adsorption changes the denominator. The simple expression is therefore a specific reduced mechanism, not a universal Eley–Rideal law.

### Finding and eligibility

These are not mere algebraic rearrangements: their rate-limiting mechanisms and adsorption site balances differ. The L–H example has both reactants adsorbed and a squared competitive-coverage denominator; the simple E–R example has one adsorbed reactant and remains first order in the gas-phase collision partner under the stated assumptions.

However, they remain within one broad heterogeneous surface-catalysis source family. The catalogue must decide whether distinct mechanistic subfamilies within a domain may each contribute a separate structural unit, and must apply that decision consistently. Do not count Langmuir coverage itself, the adsorption equilibrium, and the derived rate expression as three independent equations. The candidate's kinetic scope, site density basis, adsorption convention, pressure units, product inhibition and temperature-dependent rate constant must be fixed before drafting.

**Register links:** CHEM-LH-WACHS-2024; CHEM-RIDEAL-1939; CHEM-ELEY-RIDEAL-1940; CHEM-IUPAC-LANGMUIR-RIDEAL; CHEM-ER-ENG-REACTION.

## 2. Biology: Adair binding polynomial versus Hill saturation curve

Adair (1925), *The Hemoglobin System: VI. The Oxygen Dissociation Curve of Hemoglobin*, *Journal of Biological Chemistry* 63, 529–545, DOI 10.1016/S0021-9258(18)85018-9, is a primary source in the register. A modern historical/mathematical review reproduces the Adair four-step expression:
\[
Y=
\frac{K_1x+2K_2x^2+3K_3x^3+4K_4x^4}
{4(1+K_1x+K_2x^2+K_3x^3+K_4x^4)}.
\]
Here x is oxygen pressure/concentration under the selected convention, and the K_i are macroscopic stepwise binding constants. The polynomial represents sequential occupancy states; the coefficients weight the number of bound oxygen molecules.

This is structurally different from the Hill empirical saturation form
\[
Y=\frac{x^n}{K+x^n},
\]
but both describe hemoglobin oxygen binding and belong to one source/phenomenon family. A recent review explicitly distinguishes Adair's sequential four-site treatment from Hill's empirical aggregation/cooperativity model.

### Finding and eligibility

Adair is a credible equation-level lead with an identifiable primary paper and a reproduced equation. It is not a cosmetic variant of the Hill curve. Nevertheless, the catalogue should not count both automatically: the source-family sampling rule must specify whether multiple structurally distinct models of the same biological binding system may be sampled as separate statistical units. If both are retained, their different model assumptions and parameter meanings must be explicit. A generic two- or three-site truncation must not be presented as the original four-step Adair equation.

**Register links:** BIO-ADAIR-1925; BIO-HILL-1910.

## 3. Biology: original Kermack–McKendrick age-of-infection model is not simply an SIR equation

The 1927 Kermack–McKendrick paper is already registered as BIO-KERMACK-MCKENDRICK-1927. A mathematical review of the original model states that it was formulated through a convolution equation, not originally as the later age-structured PDE. The review gives an equivalent age-of-infection formulation:
\[
\partial_t n(t,a)+\partial_a n(t,a)=0,
\]
with an infection boundary condition driven by the infectiousness kernel \(\tau(a)\), susceptible population S(t), and initial infection-age density. It also derives the convolution equation for incidence:
\[
b(t)=c(t)\int_0^t b(t-a)\tau(a)\,da
+c(t)\int_t^\infty g(a-t)\tau(a)\,da.
\]
The review explicitly notes that this PDE and convolution representation are equivalent. It further derives the standard SIR ODE only after choosing an exponential infectiousness kernel and defining aggregate I(t), R(t) accordingly.

### Finding and eligibility

The age-structured model is a strong system-level candidate and is mathematically distinct from a bare SIR incidence expression. The PDE and convolution equation are two representations of the same model, not two separate entries. The SIR reduction is a special case and should not be counted as an independent equation from this parent model without a defensible structural policy.

This is not a scalar equation. A catalogue entry would need to preserve the kernel, initial age distribution, susceptible coupling, boundary condition and complete output contract. A single incidence projection is not a faithful replacement for the system.

**Register link:** BIO-KERMACK-MCKENDRICK-1927.

## 4. Biology: Turing reaction–diffusion model must remain a coupled system

Turing's 1952 paper, *The Chemical Basis of Morphogenesis*, is verified as *Philosophical Transactions of the Royal Society B* 237(641), 37–72. Its abstract and bibliographic record describe reacting and diffusing morphogens, instability of a homogeneous equilibrium, and distinct geometries including a ring of cells, a sphere and a two-dimensional tissue.

### Finding and eligibility

The source supports a coupled reaction–diffusion model family, not a single standalone scalar equation. The discrete-cell ring and continuous-tissue representations are linked model geometries; they must not be counted as separate entries merely because their coordinates or discretizations differ. A usable benchmark record requires the selected reaction scheme, number of species, diffusion coefficients, spatial domain, boundary conditions, initial conditions and deterministic numerical adapter. The source record alone does not identify a single universal Turing equation.

**Register link:** BIO-TURING-1952.

## 5. Physics: Euler column-buckling attribution requires historical precision

The existing source register includes Euler's 1759 *Sur la force des colonnes*. A historical review of column buckling distinguishes Euler's 1744 elastic-column result from later developments: the 1744 formula is presented for a cantilevered elastic column, while the familiar modern pinned–pinned form
\[
P_{cr}=\frac{\pi^2EI}{L_k^2}
\]
is attributed in that review to Lagrange's 1770–1773 solution, expressed in modern notation. The review also explains that the modern EI notation is later than Euler's original coefficient convention.

### Finding and eligibility

Do not cite “Euler 1759” as though it were the source of the modern pinned–pinned formula without checking the exact original text and historical derivation. The Euler–Lagrange column stability family is a legitimate physics/engineering lead, but boundary conditions and effective length are essential. Cantilever, pinned–pinned, fixed-fixed and other end conditions are not automatically separate structural equations: they are boundary-condition variants of the same beam stability eigenproblem unless the catalogue explicitly treats the boundary-value problem as the unit.

**Register link:** PHYS-EULER-COLUMN-1759; compare PHYS-EULER-ELASTICA-1744.

## 6. Updated screening decisions

| Lead | Source status | Structural assessment | Current decision |
|---|---|---|---|
| Langmuir–Hinshelwood two-adsorbate rate | Exact modern equation located (Wachs 2024, Eq. 5) | Distinct from Eley–Rideal mechanism; same broad surface-catalysis family | Hold for family policy and full assumptions/ranges |
| Eley–Rideal one-adsorbate rate | Mechanism and reduced rate derivation located in authoritative teaching source; historical source lineage already registered | Distinct mechanism from L–H; simplified expression is conditional | Hold for exact primary/versioned equation source and family policy |
| Adair four-step binding polynomial | Primary 1925 paper identified; equation reproduced in modern review | Structurally distinct from Hill empirical curve; same hemoglobin binding family | Hold for primary equation-page transcription and family policy |
| Kermack–McKendrick age-structured model | Original 1927 source registered; later mathematical review gives PDE/convolution equivalence | Whole system; SIR is a special reduction | Hold for original equation transcription and system adapter |
| Turing reaction–diffusion model | Primary 1952 paper identity and scope verified | Coupled PDE family; multiple geometries are not independent entries | Hold for exact selected reaction system and adapter |
| Euler column stability | Historical attribution and modern boundary-condition form cross-checked | Boundary-condition variants of one stability problem | Hold for exact primary-source and boundary-condition mapping |

## 7. Consequences for the Core-295 design

1. The source register already contains several promising model families whose full mathematical structures are not represented by the scalar assistant-authored pool. They should be developed from their primary sources rather than simplified into convenient single-output formulas.
2. Source-family membership and structural equivalence are separate fields. Different mechanisms may be structurally distinct within a common scientific family; the sampling design must state whether multiple entries from one family are allowed and how dependence is handled.
3. Coupled ODE/PDE/integral models need a predeclared system-level equation unit and deterministic adapter. Do not count their component equations, alternate representations, reductions or numerical discretizations separately.
4. Historical attribution is not enough. A modern formula can be a valid candidate only if the modern derivation/source is cited and its assumptions are preserved; do not imply it appears verbatim in an earlier paper.
5. None of these findings changes the formal accepted count or resolves the catalogue's cross-domain structural-equivalence policy.

## 8. Work not performed

No equation was added to the formal catalogue. No source status was upgraded. No candidate was accepted. No script, validator, solver, experiment, workflow, paid compute or live protocol/API call was run.
