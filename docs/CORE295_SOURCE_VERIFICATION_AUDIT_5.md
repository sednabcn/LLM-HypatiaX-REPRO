# Core-295 source verification audit 5: Fick cardiac-output balance and Timoshenko beam provenance

**Date:** 2026-11-11  
**Status:** source-screening findings only. No equation is accepted, imported or promoted by this audit.  
**Scope:** two existing source-register leads. The review separates a source-verified principle from an incomplete primary-equation transcription.

## 1. Biology: Fick's cardiac-output principle

### 1.1 Primary-source identity and equation

The source register contains BIO-FICK-1870, Adolf Eugen Fick's *Ueber die Messung des Blutquantums in den Herzventrikeln*, published in *Sitzungsberichte der Physikalisch-Medicinischen Gesellschaft zu Würzburg*, Neue Folge 2, pp. XVI–XVII (1870). The Garrison–Morton–Norman bibliographic record identifies the original item and links a HathiTrust digital facsimile. The facsimile endpoint was not accessible during this review, so the exact original-page equation has not been independently transcribed.

A modern pharmacology review (Geerts, Aarts and Jansen, 2011) states the direct-Fick mass balance: oxygen uptake by the lungs is transferred to blood, and under steady conditions the body's oxygen consumption equals blood flow multiplied by the arterial–mixed-venous oxygen-content difference. It gives cardiac output as

\[
Q=\frac{\dot V_{O_2}}{C_{aO_2}-C_{vO_2}}.
\]

Here \(\dot V_{O_2}\) is oxygen uptake per unit time and \(C_{aO_2}\), \(C_{vO_2}\) are arterial and mixed-venous oxygen contents per unit blood volume. With \(\dot V_{O_2}\) in mL O2/min and contents in mL O2/L blood, Q is L blood/min. If content is expressed per dL, the corresponding factor-of-10 unit conversion must be explicit.

### 1.2 Assumptions and classification

The direct-Fick calculation requires:
- steady-state oxygen uptake and blood flow over the measurement interval;
- oxygen uptake measured accurately and transferred from lungs into blood;
- arterial and representative mixed-venous oxygen **content** measurements, not partial pressures;
- no material oxygen consumption within the lungs under the stated simplification;
- a declared unit convention for gas volume, blood volume and time.

The equation is a conservation-of-mass measurement relation, not a time-evolution law for a physiological state. It estimates flow from an independently measured flux and a concentration/content difference. That distinction matters for the Core-295 domain contract: the team must decide whether measurement/diagnostic equations are in scope alongside constitutive and dynamical models.

### Finding and eligibility

Fick's principle is a credible, historically important physiological measurement relation with a registered primary source and an exact modern statement of the balance. The original 1870 page-level equation transcription remains outstanding. Its equation should be kept as one mass-balance relation; alternative unit conventions, rearrangements, or applications to other transported gases are not independent entries without a structural policy decision.

Hold pending primary-page transcription, the declared scope for measurement equations, steady-state/data-generation contract, and unit-safe input ranges. Do not confuse oxygen content with oxygen partial pressure or count a unit conversion as a new equation.

**Register link:** BIO-FICK-1870.

## 2. Physics: Timoshenko's 1921 shear-correction paper

### 2.1 What the primary record establishes

The source register contains PHYS-TIMOSHENKO-1921, S. P. Timoshenko's “On the correction for shear of the differential equation for transverse vibrations of prismatic bars,” *Philosophical Magazine*, Series 6, volume 41 (1921), pp. 744–746, DOI 10.1080/14786442108636264. The journal and National Diet Library records confirm the title, author, year, volume and pages. The accessible journal record exposes bibliographic metadata but not the paper's equation text; the full primary equation has therefore not been transcribed in this audit.

A 2019 historical review of first-order shear-deformable beam and plate models reports that Bresse had already derived two-field shear-deformable beam equations in 1859, and that Timoshenko's 1913–1922 work generalized this line by modifying shear stiffness and introducing a shear-correction factor. The review distinguishes shear deformation and rotary inertia from the classical Euler–Bernoulli beam assumptions.

### 2.2 Provenance and structural implications

Do not treat “Timoshenko beam equation” as one uniquely authored modern formula. The family has a longer Bresse–Timoshenko–Ehrenfest lineage, and the 1921 paper's specific shear correction must be distinguished from:
- Bresse's earlier two-field beam kinematics;
- later Timoshenko beam formulations and calibrated shear-correction factors;
- Euler–Bernoulli as a limiting model that neglects transverse shear deformation (and, in the usual form, rotary inertia);
- later plate theories and higher-order shear-deformation models.

A usable candidate must specify whether the benchmark targets the 1921 transverse-vibration correction, the later coupled displacement/rotation beam system, or another dated formulation. It must also freeze cross-section geometry, shear-correction factor, material assumptions, rotary inertia treatment, boundary conditions and the observable/solution contract.

### Finding and eligibility

The primary source identity is verified, but the exact primary equation and notation are not available in the accessible record used here. The historical review also makes clear that a modern general Timoshenko beam system cannot be attributed wholesale to the 1921 note without tracing its precise lineage.

Hold as a source lead only. Do not draft or accept a formula from a secondary textbook and label it verbatim as Timoshenko (1921). Obtain the primary paper text and compare its equation with the Bresse and later Timoshenko formulations before assigning a structural fingerprint or source-family/statistical-unit identity.

**Register link:** PHYS-TIMOSHENKO-1921.

## 3. Updated screening decisions

| Lead | Source status | Structural assessment | Current decision |
|---|---|---|---|
| Fick 1870 cardiac-output principle | Primary bibliographic record and facsimile link identified; exact balance reproduced in a modern review | Steady oxygen mass-balance measurement relation; not a dynamic state equation | Hold for original-page transcription, measurement-equation scope and unit contract |
| Timoshenko 1921 shear correction | Primary article metadata verified; full text/equation not accessible; later historical review clarifies lineage | Shear-deformable beam theory with Bresse antecedents and later Timoshenko generalizations | Source lead only; no equation-level candidate drafted |

## 4. Consequences for Core-295

1. Decide explicitly whether the Biology domain includes measurement equations such as Fick's principle, or is restricted to dynamical/constitutive biological models.
2. Require primary-page transcription before assigning source-verified status; a bibliographic record plus modern reproduction is not a verbatim primary transcription.
3. Treat Fick's relation as one mass-balance equation; unit conversions and alternative notations are not extra structures.
4. For Timoshenko, preserve the dated formulation and derivation lineage. Do not substitute a later generic beam system for the 1921 source.
5. Neither lead is accepted or counted toward a 59-per-domain target by this audit.

## 5. Work not performed

No formal catalogue entry was changed. No source status was upgraded. No candidate was accepted. No script, validator, solver, experiment, workflow, paid compute or live protocol/API call was run.
