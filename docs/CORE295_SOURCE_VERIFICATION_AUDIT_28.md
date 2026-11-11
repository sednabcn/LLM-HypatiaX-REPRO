# Core-295 source verification audit 28: Leslie age-structured projection and Taylor–Jonker replicator dynamics

**Date:** 2026-11-11  
**Status:** verification of discovery-batch leads only. No equation is added to the formal catalogue or counted toward 295.  
**Scope:** discovery batch 26 leads Leslie and replicator dynamics; Nicholson–Bailey is also status-checked.

## 1. Leslie 1945 age-structured projection

### Primary transcription

P. H. Leslie, *On the use of matrices in certain population mathematics*, Biometrika 33(3) (1945), 183–212, DOI 10.1093/biomet/33.3.183. The original PDF is accessible.

On printed pp. 183–184, Leslie defines:
- (n_{x,t}): number of females alive in age class (x) to (x+1) at time (t);
- (P_x): probability that a female in age class (x) survives into age class (x+1) in the next interval;
- (F_x): number of daughters born during the interval who survive into the first age class at the next time.

The one-step recurrence is
[
mathbf n_{t+1}=Mmathbf n_t,
]
where the first row of (M) is (F_0,F_1,ldots,F_m), and the subdiagonal is (P_0,P_1,ldots,P_{m-1}); all other entries are zero. Leslie states (0<P_x<1), (F_xgeq0), and that (M^tmathbf n_0) gives the age distribution after (t) intervals.

### Model and adapter boundary

The original paper assumes constant age-specific fertility and survival rates over the projection period and uses the female population. The age interval and time step are the same unit. The (F_x) quantities are not simply births per female: they are daughters born during the interval who survive to the first age class at the next census. The source derives (F_x) from maternal fertility and survivorship within the interval, with approximations that become inaccurate if the age/time interval is too coarse relative to the species' lifespan.

The matrix recurrence is one complete age-structured population system. Do not count each age-class row, fertility term, survival term, total-population sum, dominant eigenvalue or stable age distribution as an independent equation candidate. The latter are outputs/analyses of the same matrix model.

**Disposition:** primary equation and original source location verified. Retain as a complete-system Biology lead, discovery-only, pending age-structured adapter, age/time discretization and species-specific fertility/survival contract. The scalar Core-15 function interface is insufficient without an explicit vector-system extension.

## 2. Taylor–Jonker 1978 replicator dynamics

### Primary transcription

P. D. Taylor and L. B. Jonker, *Evolutionarily stable strategies and game dynamics*, Mathematical Biosciences 40 (1978), 145–156, DOI 10.1016/0025-5564(78)90077-9. The original article PDF is accessible.

The paper defines (s_i) as the population proportion using strategy (i), (F(imid s)) as the fitness of strategy (i) in population state (s), and (F(smid s)) as the mean fitness. Its continuous-time Eq. (2) is
[
dot s_i=s_i\left[F(i\mid s)-F(s\mid s)\right].
]
For a linear matrix game with payoff matrix (A), (F(imid s)=(As)_i) and (F(smid s)=s^TAs), giving
[
dot s_i=s_i\left[(As)_i-s^TAs\right].
]

The paper also gives a discrete-generation dynamic in Eq. (3), with the increment form in Eq. (4). Those are alternative time-update representations of the same evolutionary game model family, not separate entries.

### Model and adapter boundary

The state vector lies in the simplex:
[
s_i\geq0,qquad\sum_i s_i=1.
]
The simplex is invariant under the continuous and discrete dynamics described in the paper. The original model assumes a haploid population with strategy-dependent reproduction; the continuous-time derivation uses overlapping generations and exponential growth/decay, while the discrete model treats discrete generations.

A benchmark adapter must freeze strategy count, payoff matrix, fitness convention, time interpretation and initial simplex state. Do not sample each component (s_i) independently; the state must remain on the simplex. Do not count individual strategy equations, mean fitness, the continuous/discrete forms or equilibrium/ESS conditions as separate equation candidates.

**Disposition:** primary equation and source location verified. Retain as a complete-system Biology lead, discovery-only, pending simplex-constrained vector-system adapter and an explicit relationship review with other population-frequency systems.

## 3. Nicholson–Bailey status

Nicholson and Bailey (1935), *The Balance of Animal Populations—Part I*, Proceedings of the Zoological Society of London 105(3), 551–598, DOI 10.1111/j.1096-3642.1935.tb01680.x, is confirmed as the primary historical source. The classical host–parasitoid equations in discovery batch 26 are currently supported by a modern theoretical-biology lecture script and secondary ecological literature, but this check did not obtain a page-level transcription from the original 1935 article.

**Disposition:** keep the Nicholson–Bailey system discovery-only and unverified at equation level until the original source equation/page or a faithful authoritative transcription is obtained. Do not describe the equation as primary-source-verified yet.

## 4. Cross-model and catalogue decision

Leslie's model is a linear age-structured projection system; Taylor–Jonker is a nonlinear frequency-dependent system on a probability simplex. They are distinct complete model structures, but both are vector-valued population systems and cannot be represented faithfully as independent scalar equations without loss of state constraints.

The Nicholson–Bailey model is a discrete-generation host–parasitoid interaction system and is also a full coupled model. These three should not be counted by splitting component equations.

No formal source-register or equation-catalogue record was changed. The manifest remains 128 source records, 19 proposed equation records, zero accepted equations and an unfrozen sampling frame.

No experiments, solvers, validators, workflows, paid compute, API calls or biological measurements were performed. This is original-source review only.
