# Fresh PySR search inside training-only validation folds

**Status:** implementation primitive; not yet connected to the production
HybridDiscovery retry selector.  
**Implementation:** hypatiax/tools/symbolic/pysr_training_search.py  
**Regression source:** tests/test_pysr_training_search.py

## Why a second validation mode is needed

The earlier fold-validation helpers refit floating-point coefficients while
holding one discovered symbolic structure fixed. That measures coefficient
refit robustness, but it does not measure whether PySR rediscovers the same
structure from different training partitions.

This module adds the stronger mode: each fold gets a fresh PySR search. The
model is fitted only on that fold's fitting rows, chooses its own best equation,
and predicts the fold's held-out training rows.

## API and lifecycle

The public entry point is
evaluate_pysr_search_on_training_folds(searcher_factory, X_train, y_train, folds).

The factory receives a deterministic fold seed and must return a new,
unfitted PySRRegressor-compatible model. The required public interface is:

- fit(X_fit, y_fit)
- get_best(), returning an equation under the equation field
- predict(X_validation)

A typical factory looks like this (use the same declared search configuration
as the production arm; the example is intentionally not executed here):

\`\`\`python
def make_searcher(fold_seed):
    from pysr import PySRRegressor

    return PySRRegressor(
        niterations=50,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sqrt", "exp", "log"],
        maxsize=20,
        random_state=fold_seed,
        deterministic=True,
        parallelism="serial",
    )

folds = make_training_folds(
    len(y_train), n_splits=4, n_repeats=2, seed=42
)
summary = evaluate_pysr_search_on_training_folds(
    make_searcher, X_train, y_train, folds, seed=42
)
audit = summary.to_dict()
\`\`\`

The exact operator grammar, iteration count, population, timeout, and
complexity budget must come from the declared domain/DiscoveryConfig rather
than being copied blindly from this illustrative example. PySR construction
is lazy, so importing the validation module does not initialize Julia.

The evaluator rejects a factory that returns the same model object twice.
Each successful fold records its seed, model class, selected equation,
fitting-row count, and validation-row count. The aggregated validation
summary reports fold RMSE, normalized RMSE, spread, worst-fold error, and
expression recurrence.

## Leakage boundary

- The only dataset inputs are X_train and y_train.
- A fresh model is fitted on X_fit and y_fit only.
- Held-out training rows are passed only to predict after fitting.
- The factory must fit every data-dependent preprocessing step and target
  transform on the fitting partition only, then freeze it for validation.
- Do not pass far/test arrays, metrics, or metadata into the factory.
- Do not use far/test results for early stopping, search configuration,
  operator selection, retry policy, candidate selection, or tie-breaking.

For data requiring signed-log transforms, engineered geometric means/ratios,
or target scaling, the factory must wrap PySR in a fold-local adapter. The
existing FoldFeaturePipeline and FoldTargetScaler are useful primitives,
but this PR does not claim that they reproduce every heuristic in the
production SymbolicEngine preprocessing path.

## How it differs from coefficient refitting

| Mode | Per-fold work | What it measures |
|---|---|---|
| Fixed-expression refit | Refit float coefficients; keep equation structure fixed | Stability of a chosen structure under coefficient refitting |
| Fresh PySR search | Re-run symbolic evolution from scratch; select a fold-specific equation | Reproducibility of symbolic structure and predictive performance |

Fresh search is substantially more expensive. The number of folds, repeats,
PySR iterations, population size, timeout, and number of search strategies
must be budgeted before enabling it in a benchmark.

## Current integration boundary and next steps

This is an offline evaluation primitive. It is intentionally not invoked from
HybridDiscoverySystem._discover_with_retry() yet: production integration
must first pass raw training-region arrays before global preprocessing,
recreate the exact engine feature/operator contract inside each fold, and
define how candidates with fold-specific feature schemas are compared. The
current production retry path receives arrays already transformed by the
outer discovery adapter, so wiring this helper directly there would create
a misleading claim of leakage-safe validation.

The next integration phase should:

1. Capture immutable raw X_train/y_train before global data-dependent
   transforms; never include the far/test partition.
2. Build a typed fold-search configuration from the same domain and
   DiscoveryConfig used by production discovery.
3. Refit preprocessing, engineered features, target scaling, and PySR search
   independently in each fold.
4. Compare fold-specific equations using training-only predictive evidence,
   symbolic complexity, scientific hard gates, and conservative structural
   stability. Do not require literal equation identity where feature schemas
   legitimately differ.
5. Make validation-enabled selection fail closed when too few folds produce
   valid evidence; do not silently fall back to full-training R².
6. Add selector integration and provenance tests before enabling it in Exp2.

Regression tests were added but not run. No CI, manual workflow dispatch,
experiments, smoke runs, workers, benchmarks, or LLM API calls were launched.

## Selecting among PySR search configurations

The companion API
\`select_pysr_search_strategy_on_training_folds\` compares multiple named
searcher factories using the same internal folds and seed schedule. It ranks
them by mean normalized RMSE, then worst-fold normalized RMSE and score
dispersion. Expression recurrence is retained as a diagnostic; expression
length is only a final tie-break proxy, not symbolic complexity.

This selector chooses a **search configuration**, not an equation. Once a
configuration wins, perform a fresh final PySR fit on all available training
rows. Do not choose one fold's equation as the final equation, and do not use
far/test results to select the strategy or tune its settings.

If every strategy fails the minimum fold-evidence requirement (or an optional
quality ceiling), the selector returns \`NO_CREDIBLE_CANDIDATE\`. It never
falls back to full-training R². See Section 18 of
\`docs/hybrid_discovery_physics_informed_architecture.md\` for the design log
and the remaining Exp2 integration requirements.

## Exp2 Hybrid production adapter

The fold-local PySR evaluator and strategy selector are now connected to the Exp2 Hybrid worker through hypatiax/tools/symbolic/hybrid_fold_search.py. Each fold uses a fresh pure-PySR SymbolicEngine, learns the Hybrid outer signed-log flags and engine-local feature transforms on fitting rows only, and applies the frozen transform plan to held-out training rows. The selector compares baseline, lower-parsimony, and higher-parsimony configurations on identical folds.

The selected configuration is then used for one ordinary final full-training-region HybridDiscovery search. LLM guidance is disabled inside fold searches and remains enabled only for the final configured Hybrid arm. The Exp2 worker records the fold-selection audit and reserves a bounded time budget for it. If all configurations fail the required fold evidence, the worker returns NO_CREDIBLE_CANDIDATE rather than falling back to full-data training R².

This is a bounded integration: two random holdouts, three parsimony settings, 20 search iterations, and a 20-second per-fold timeout. It does not claim continuous-domain physical proof, and it does not use far/test metrics for configuration selection. Regression source was added but not run; no CI or experiment was launched.
