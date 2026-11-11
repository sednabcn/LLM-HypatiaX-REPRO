# Core-295 candidate discovery batch 20: Biology excitable-cell and nerve membrane models

**Status:** primary-source model tracing only. No equation is accepted or counted toward the 59 Biology target.

## 1. Hodgkin–Huxley squid-axon model (1952)

**Primary source:** Hodgkin & Huxley, “A quantitative description of membrane current and its application to conduction and excitation in nerve,” *The Journal of Physiology* 117(4) (1952), 500–544, DOI [10.1113/jphysiol.1952.sp004764](https://doi.org/10.1113/jphysiol.1952.sp004764). The publisher supplies an updated original article using modern sign/unit conventions.

The membrane-current balance is conventionally written:

\[
C_m\frac{dV}{dt}
=I_{app}
-\bar g_{Na}m^3h(V-E_{Na})
-\bar g_Kn^4(V-E_K)
-g_L(V-E_L).
\]

The three gating variables obey:

\[
\frac{dx}{dt}=\alpha_x(V)(1-x)-\beta_x(V)x,
\qquad x\in\{m,h,n\}.
\]

Here \(V\) is membrane potential, \(C_m\) membrane capacitance per area, \(I_{app}\) applied current density, \(\bar g_{Na},\bar g_K,g_L\) conductance densities, \(E_{Na},E_K,E_L\) reversal potentials and \(m,h,n\) sodium activation, sodium inactivation and potassium activation gates.

**Boundary:** this is a coupled nonlinear four-state ODE model, not a single scalar equation. The rate functions \(\alpha_x(V),\beta_x(V)\) are voltage-dependent empirical functions whose units and temperature scaling must be preserved. The original squid giant axon model and its later modern-sign convention are linked representations, not independent models. Do not count the six current/gating relations as six independent equation families.

## 2. FitzHugh BVP / excitable-membrane reduction (1961)

**Primary source:** FitzHugh, “Impulses and physiological states in theoretical models of nerve membrane,” *Biophysical Journal* 1(6) (1961), 445–466, DOI [10.1016/S0006-3495(61)86902-6](https://doi.org/10.1016/S0006-3495(61)86902-6).

FitzHugh generalizes the van der Pol relaxation oscillator to a two-variable nonlinear system representing excitability and refractoriness. A commonly used dimensionless FitzHugh–Nagumo representation is:

\[
\dot v=v-\frac{v^3}{3}-w+I,
\qquad
\dot w=\epsilon(v+a-bw).
\]

**Provenance boundary:** the displayed dimensionless form is a later canonical parameterization of the FitzHugh/BVP family; do not claim it is a verbatim transcription of FitzHugh's 1961 original equations. The original paper's parameterization and sign conventions must be transcribed separately before acceptance. The reduction is related to the Hodgkin–Huxley model through a projection of its four-dimensional phase space, so it is a reduced excitable-membrane family, not an independent biological mechanism.

## 3. Morris–Lecar conductance model (1981)

**Primary source:** Morris & Lecar, “Voltage oscillations in the barnacle giant muscle fiber,” *Biophysical Journal* 35(1) (1981), 193–213, DOI [10.1016/S0006-3495(81)84782-0](https://doi.org/10.1016/S0006-3495(81)84782-0). The original model has two state variables and is represented in the Physiome Model Repository as CellML equations 1–2.

A standard form is:

\[
C\frac{dV}{dt}
=I_{app}
-g_L(V-V_L)
-g_{Ca}m_\infty(V)(V-V_{Ca})
-g_Kw(V-V_K),
\]

\[
\frac{dw}{dt}
=\lambda_w(V)\left(w_\infty(V)-w\right).
\]

The steady-state activation and recovery functions are voltage-dependent, typically sigmoidal; \(\lambda_w(V)\) controls the recovery timescale. The model uses a fast voltage/calcium activation variable treated as quasi-steady and a slower potassium recovery variable.

**Boundary:** Morris–Lecar is not merely a reparameterized FitzHugh–Nagumo system. It is a conductance-based two-variable model with explicit ionic currents, but both are members of the excitable-cell dynamical-systems family. Keep their source IDs distinct and cluster their sampling lineage. Use the exact original equations and parameter values rather than assuming every later textbook Morris–Lecar convention is identical.

## Source-family and benchmark controls

- Hodgkin–Huxley is a four-state voltage/gating ODE system. The membrane-current equation and three gate kinetics are coupled parts of one model.
- FitzHugh's BVP model is a reduced two-state excitable oscillator derived in relation to HH dynamics. The canonical dimensionless FHN form shown above is a later parameterization, not automatically the 1961 original.
- Morris–Lecar is a two-state conductance-based model with fast quasi-steady activation and slow recovery. It is distinct from HH in state dimension and ionic mechanism but remains in the same excitable-cell source cluster.
- Current sign conventions differ across original and modern papers. A positive inward current may appear with opposite signs depending on whether ionic current is defined inward-positive or outward-positive.
- Gating-rate equations are not independent of the membrane-current balance; parameter units, voltage offsets and temperature scaling must be frozen.
- Do not count a phase-plane reduction, nondimensionalization, rescaling, alternative sign convention or one ionic-current term as a separate equation family.

## Acceptance requirements

Record membrane capacitance, ionic conductances, reversal potentials, temperature, voltage reference, current sign convention, gating-rate functions, initial conditions and integration time scale. For reduced models, specify the reduction map, nondimensionalization and validity regime. The deterministic benchmark must include all coupled state equations or explicitly justify a scalar observable adapter.

All records remain candidates. No Biology entry is accepted; no experiment or workflow has been run.
