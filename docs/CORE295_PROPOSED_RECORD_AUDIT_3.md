# Core-295 proposed-record audit 3: Hill muscle force–velocity source and structural review

**Date:** 2026-11-11  
**Status:** evidence and blocker audit only. No equation is accepted by this audit.

## 1. BIO-HILL-MUSCLE-001 — primary-source equation verified

The primary paper is A. V. Hill, “The heat of shortening and the dynamic constants of muscle,” *Proceedings of the Royal Society of London. Series B* 126 (1938), 136–195, DOI [10.1098/rspb.1938.0050](https://doi.org/10.1098/rspb.1938.0050). An accessible scan of the original paper is [available here](https://math.nyu.edu/~peskin/eb_lecture_notes/Hill_AV_1938.pdf).

The original paper states the characteristic relation
[
(P+a)(v+b)=\mathrm{constant}.
]
The relation is discussed in Part III, printed pp. 183–184, where Hill describes it as the relation for shortening under constant load and as governing the contractile component in the active-muscle two-component model. The paper's summary, printed p. 193, repeats the characteristic equation and says it describes shortening speed under load. At printed p. 189, Hill gives the steady-state relation
[
(P_u+a)(u+b)=(P_0+a)b,
]
which fixes the constant from the zero-shortening-velocity/isometric reference state. Thus the proposed rearrangement
[
v=b\frac{P_0-P}{P+a}
]
is algebraically consistent with Hill's stated characteristic relation when that reference-state condition is applied.

**Source finding:** the exact characteristic equation and its intended active-muscle context are directly verifiable in the primary paper. This resolves the queue's earlier “original equation page” blocker.

## 2. Unit and notation blocker

The current manifest describes (P), (P_0), and (a) as forces in N (or other force units). The primary scan reports (a) in g./sq. cm. in its worked parameter discussion (printed p. 183), while its notation and numerical examples also refer to loads/tensions in grams. The record must not silently mix force and stress conventions.

Before acceptance, choose one coherent convention:
- force convention: define (P,P_0,a) all as forces, with the muscle cross-sectional-area normalization made explicit; or
- stress convention: define (P,P_0,a) all as stresses, and preserve the source's area-normalized parameter units.

Then verify the conversion from the paper's reported quantities and document whether velocity (v,b) is absolute length/time or normalized muscle-length/time. The source uses “length/sec.” for (b) in its worked values. Do not leave the current broad “N or other force unit” wording as the final unit contract.

## 3. Validity and system-scope blocker

The relation is not a generic law for arbitrary muscle contraction. The source's simplified relation concerns active contractile-element shortening under the stated load/activation conditions; Hill's paper distinguishes the contractile element from an elastic element in series. The record should retain the isotonic/constant-load and maintained tetanic/active-state scope, identify the muscle preparation and temperature regime, and distinguish contractile-element velocity from whole-muscle velocity when series elasticity matters.

The source itself notes that the constant-load simplification removes a variable and that under changing load the characteristic relation applies to time-varying force and velocity of the contractile component. The benchmark must therefore state which observable it generates; a scalar mapping must not erase the series-elastic model context.

## 4. Core-15 structural-overlap blocker

The proposed relation is a shifted reciprocal/hyperbolic response:
[
v=b\left(\frac{P_0+a}{P+a}-1\right).
]
The excluded Core-15 Michaelis–Menten relation can also be written as a constant minus a reciprocal term:
[
v_{MM}=V_{max}-\frac{V_{max}K_m}{S+K_m}.
]
Both are one-pole rational saturation/rectangular-hyperbola forms after affine changes of input and output variables. This does not by itself prove that the two physical models are scientifically interchangeable: Hill's relation is a decreasing load–velocity law for an active contractile element, while Michaelis–Menten is a substrate-saturation rate law. It does, however, create a material structural-equivalence question under a catalogue policy that rejects cosmetic transformations and explicitly excludes Michaelis–Menten.

**Required decision:** define whether affine input/output transformations that preserve the one-pole rational functional family count as structural equivalence for Core-295. Apply the rule consistently to other domains. If yes, do not count the Hill candidate separately from the excluded Michaelis–Menten family. If no, document why the distinct physical state/observable and validity structure are sufficient, and ensure the same exception is not used selectively to pad other domains.

## 5. Required resolution before acceptance

1. Retain the original primary equation and the derived (P_0)-anchored rearrangement with exact source locations.
2. Resolve force-versus-stress units and velocity normalization.
3. Freeze muscle preparation, temperature, maintained activation/tetanus, constant-load regime, series-elastic interpretation and the generated observable.
4. Decide the affine one-pole structural-equivalence policy against the Core-15 Michaelis–Menten exclusion.
5. Only then define physically supported train/extrapolation ranges and a deterministic generator.

The manifest entry remains **proposed**. This audit does not change its status, count it toward Biology's 59, or authorize shard planning.

## 6. Audit boundary

No catalogue validator, experiment, paid compute, live API/protocol call or GitHub Actions workflow was run. No experiment results are implied by this source review.
