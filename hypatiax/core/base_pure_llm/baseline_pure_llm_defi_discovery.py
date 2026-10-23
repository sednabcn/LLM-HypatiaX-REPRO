"""
Pure LLM baseline for the DeFi / Feynman formula-discovery benchmark.

INPUT-PARITY POLICY (release version)
  The prompt contains only: the task description, domain, variable names and
  the protocol's physical constants (task spec). It contains NO target
  formula, NO code template, NO per-equation sign/form corrections and NO
  statistics derived from the data. All former equation-specific hint blocks
  (Nernst, Clausius-Mossotti, Fourier, Gaussian, the specialized
  liquidation/Kelly/leverage/collateral/ES/logistic/Michaelis-Menten/
  allometric/Arrhenius prompts, and the generic normalisation hint) were
  DELETED, not gated, so no flag value can re-enable them. Earlier
  exploratory runs contained them; see the audit notes.
"""

import inspect
import hashlib
import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from anthropic import Anthropic
from dotenv import load_dotenv

from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol

# Reproducibility seeds (added for JMLR submission)
random.seed(42)
np.random.seed(42)

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _flag(name: str) -> bool:
    """True when env var `name` is set to 1/true/yes.

    B2 switches:
      HYPATIAX_DISABLE_HARDCODED=1     -> no hardcoded / OLS-fitted formula return
      HYPATIAX_DISABLE_PROMPT_HINTS=1  -> no ground-truth formula/code embedded in
                                          prompts, no data-derived parameter hints
    Set BOTH for a clean live-LLM run.
    """
    # FAIL-CLOSED: an unset variable means "clean run" (flag ON). The old
    # behaviour (unset -> False) silently re-enabled prompt hints whenever this
    # module ran outside run_all.sh. Legacy behaviour needs an explicit opt-in:
    #   HYPATIAX_ALLOW_LEGACY=1  and  <flag>=0
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return os.environ.get("HYPATIAX_ALLOW_LEGACY", "0") != "1"
    return raw.strip().lower() in ("1", "true", "yes")


_DEFAULT_MODEL = "claude-sonnet-4-6"


def resolve_model(explicit: str | None = None) -> tuple[str, str]:
    """Single source of truth for the model id. Returns (model, source).

    Precedence: explicit ctor arg > env HYPATIAX_LLM_MODEL >
    config/repro.yaml `llm_model` (path from env REPRO_CFG, else searched
    upward from this file) > _DEFAULT_MODEL. The source is stored in every
    result row so drift between arms is auditable.
    """
    if explicit:
        return explicit, "ctor_arg"
    env = os.environ.get("HYPATIAX_LLM_MODEL", "").strip()
    if env:
        return env, "env:HYPATIAX_LLM_MODEL"
    cfg = os.environ.get("REPRO_CFG", "").strip()
    cands = [Path(cfg)] if cfg else [d / "config" / "repro.yaml" for d in Path(__file__).resolve().parents]
    for c in cands:
        try:
            if c.is_file():
                import yaml
                m = (yaml.safe_load(c.read_text()) or {}).get("llm_model")
                if m:
                    return str(m), f"repro.yaml:{c}"
        except Exception:
            continue
    return _DEFAULT_MODEL, "code_default"


def _json_safe(o):
    """Replace non-finite floats with None so json.dump(allow_nan=False) emits
    strict JSON. Rows keep an explicit status field (e.g. r2_status), so the
    information is not lost."""
    if isinstance(o, float):
        return o if np.isfinite(o) else None
    if isinstance(o, (np.floating,)):
        return _json_safe(float(o))
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.ndarray):
        return _json_safe(o.tolist())
    if isinstance(o, dict):
        return {str(k): _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    return o


def _create_message(client, **kwargs):
    """Make one direct Anthropic API call (single attempt, no retry/cache).

    NOTE: despite the legacy alias name `_create_message_deterministic`, this is
    NOT deterministic: the Anthropic SDK >= 1.0 no longer accepts `temperature`,
    so no sampling control is sent. Results carry `temperature_sent: False`;
    use llm_k_runs (repro.yaml) to quantify run-to-run variance.


    Diagnostic/JMLR reproducibility mode: pass through whatever kwargs the
    caller supplies (including ``temperature`` when the caller sets it —
    see FIX-ISSUE2B-LLM-TEMPERATURE at the generate_formula() call site)
    with no retry-on-error logic, so a failure can't be obscured by a
    silent retry.

    CORRECTED (previously claimed "Claude 4.6 models reject
    `temperature`" and said this function deliberately omitted it — a
    live smoke test against model="claude-sonnet-4-6" confirmed
    `temperature=0.0` is accepted, so that claim was wrong and the
    generate_formula() call site now sends it).

    The function deliberately has no cache, memoization, retry, or fallback.
    Every invocation reaches ``client.messages.create`` exactly once unless
    the client raises before returning.
    """
    t0 = time.perf_counter()
    print(
        "API_ENTER "
        f"model={kwargs.get('model')!r} "
        f"max_tokens={kwargs.get('max_tokens')!r} "
        f"messages={len(kwargs.get('messages', []))}"
    )
    try:
        response = client.messages.create(**kwargs)
    except Exception as e:
        dt = time.perf_counter() - t0
        print(
            "API_ERROR "
            f"dt={dt:.6f}s "
            f"type={type(e).__name__} "
            f"message={str(e)!r}"
        )
        raise
    dt = time.perf_counter() - t0
    block_types = [
        getattr(b, "type", type(b).__name__)
        for b in getattr(response, "content", [])
    ]
    print(
        "API_EXIT "
        f"dt={dt:.6f}s "
        f"response_type={type(response).__name__} "
        f"block_types={block_types!r}"
    )
    return response


_create_message_deterministic = _create_message  # backward-compatible alias


class PureLLMBaseline:
    """Fixed Pure LLM baseline with liquidation domain corrections."""

    # FIX-ITEM1-MODEL-MISMATCH (consolidation report §4 item 1): this
    # default was an unrelated "sonnet-5" string — a different, unrelated model string
    # from the one the hybrid arm's own inline LLM call uses
    # (_HYBRID_LLM_MODEL_NAME / model="claude-sonnet-4-6" in both
    # hypatiax_defi_benchmark_v4.py and hypatiax_defi_benchmark_v4_pca.py).
    # When the old Sonnet 4.5 id -> the Sonnet 4.6 id (Fix 13) was applied,
    # it only touched the two benchmark scripts' inline hybrid call sites —
    # this module's own default was never part of that change and drifted.
    # An invalid/unavailable model string causes the API to reject the
    # request immediately (no tokens generated), which _create_message_
    # deterministic() re-raises and generate_formula()'s broad except
    # catches, returning a dict with no "python_code" key at all. Downstream,
    # that empty code is misclassified by _is_truncated_formula() as
    # "truncated_formula: no valid return statement" even though nothing was
    # generated or truncated. This is the confirmed root cause of the
    # universal pure_llm near-instant failure (100% of non-PCA calls,
    # 4/5 seeds of PCA calls). Aligning the default here with the model the
    # working hybrid path actually uses closes the gap.
    def __init__(self, model: str | None = None):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic(api_key=api_key)
        self.model, self.model_source = resolve_model(model)
        self.results = []
        # No per-instance cache: each benchmark case owns a fresh baseline.

    @staticmethod
    def evaluate_function(func, X, var_names=None):
        """
        Evaluate LLM-generated formula safely with comprehensive fallback strategies.
        """
        X = np.asarray(X)
        n_samples, n_features = X.shape

        # Get function signature
        sig = inspect.signature(func)
        n_params = len(sig.parameters)
        param_names = list(sig.parameters.keys())

        # ============================================================
        # STRATEGY 1: Direct positional arguments (most common)
        # ============================================================
        if n_params == n_features:
            try:
                # Try vectorized
                y = func(*[X[:, i] for i in range(n_features)])
                y = np.asarray(y)
                if y.shape[0] == n_samples:
                    return y.flatten()
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

            try:
                # Try row-by-row
                y = np.empty(n_samples, dtype=float)
                for i in range(n_samples):
                    y[i] = func(*[X[i, j] for j in range(n_features)])
                return y
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

        # ============================================================
        # STRATEGY 2: Single dict parameter
        # ============================================================
        if n_params == 1 and var_names is not None:
            try:
                # Try vectorized dict
                params = {name: X[:, i] for i, name in enumerate(var_names)}
                y = func(params)
                y = np.asarray(y)
                if y.shape[0] == n_samples:
                    return y.flatten()
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

            try:
                # Try row-by-row dict
                y = np.empty(n_samples, dtype=float)
                for i in range(n_samples):
                    params = {name: float(X[i, j]) for j, name in enumerate(var_names)}
                    y[i] = func(params)
                return y
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

        # ============================================================
        # STRATEGY 3: Named parameters matching var_names
        # ============================================================
        if var_names is not None and len(var_names) == n_features:
            try:
                # Try vectorized with **kwargs
                kwargs = {name: X[:, i] for i, name in enumerate(var_names)}
                y = func(**kwargs)
                y = np.asarray(y)
                if y.shape[0] == n_samples:
                    return y.flatten()
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

            try:
                # Try row-by-row with **kwargs
                y = np.empty(n_samples, dtype=float)
                for i in range(n_samples):
                    kwargs = {name: float(X[i, j]) for j, name in enumerate(var_names)}
                    y[i] = func(**kwargs)
                return y
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

        # ============================================================
        # STRATEGY 4: Try to match param names to var_names
        # ============================================================
        if var_names is not None and param_names:
            try:
                # Create mapping from param_names to var_names indices
                param_to_idx = {}
                for param_name in param_names:
                    for idx, var_name in enumerate(var_names):
                        if (
                            param_name.lower() in var_name.lower()
                            or var_name.lower() in param_name.lower()
                        ):
                            param_to_idx[param_name] = idx
                            break

                if len(param_to_idx) == n_params:
                    # Try vectorized with matched params
                    kwargs = {param: X[:, param_to_idx[param]] for param in param_names}
                    y = func(**kwargs)
                    y = np.asarray(y)
                    if y.shape[0] == n_samples:
                        return y.flatten()
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)
                if _os.environ.get('HYPATIAX_STRICT') == '1': raise

        # ============================================================
        # STRATEGY 5: Match param names to var_names, allowing extra
        # unmatched (placeholder) parameters
        # ============================================================
        # FIX-SIGNATURE-MATCHING: Strategy 4 requires *every* function
        # parameter to be matched to a variable (len(param_to_idx) ==
        # n_params). This fails whenever the LLM's generated signature
        # includes an extra parameter that has no corresponding data
        # column — most commonly an implicit "t" for time in an ODE rate
        # law, e.g. def formula(N, t) when var_names=["N"] (see the
        # documented logistic-growth workaround above, which currently
        # sidesteps this by hardcoding the formula instead of fixing
        # evaluation). That extra parameter isn't actually used to look up
        # data we have, so instead of giving up, this strategy matches
        # whatever parameters DO correspond to real variables (fuzzy match,
        # same rule as Strategy 4) and supplies a 0.0 placeholder for any
        # leftover parameters — succeeding as long as every real variable
        # was matched to some parameter (len(set(param_to_idx.values())) ==
        # n_features), even if the reverse isn't true.
        if var_names is not None and param_names and len(var_names) == n_features:
            param_to_idx = {}
            for param_name in param_names:
                for idx, var_name in enumerate(var_names):
                    if (
                        param_name.lower() in var_name.lower()
                        or var_name.lower() in param_name.lower()
                    ):
                        param_to_idx[param_name] = idx
                        break

            if param_to_idx and len(set(param_to_idx.values())) == n_features:
                try:
                    # Vectorized: matched params get their data column,
                    # any unmatched (extra) params get a 0.0 placeholder.
                    kwargs = {
                        param: (
                            X[:, param_to_idx[param]]
                            if param in param_to_idx
                            else np.zeros(n_samples)
                        )
                        for param in param_names
                    }
                    y = func(**kwargs)
                    y = np.asarray(y)
                    if y.shape[0] == n_samples:
                        return y.flatten()
                except Exception as _e:
                    import logging as _lg, os as _os
                    _lg.getLogger(__name__).warning('swallowed: %r', _e)
                    if _os.environ.get('HYPATIAX_STRICT') == '1': raise

                try:
                    # Row-by-row fallback with the same matching/placeholder
                    # scheme.
                    y = np.empty(n_samples, dtype=float)
                    for i in range(n_samples):
                        kwargs = {
                            param: (
                                float(X[i, param_to_idx[param]])
                                if param in param_to_idx
                                else 0.0
                            )
                            for param in param_names
                        }
                        y[i] = func(**kwargs)
                    return y
                except Exception as _e:
                    import logging as _lg, os as _os
                    _lg.getLogger(__name__).warning('swallowed: %r', _e)
                    if _os.environ.get('HYPATIAX_STRICT') == '1': raise

        # ============================================================
        # All strategies failed
        # ============================================================
        raise RuntimeError(
            f"All evaluation strategies failed. "
            f"Function has {n_params} params: {param_names}, "
            f"Data has {n_features} features, "
            f"var_names: {var_names}"
        )

    def generate_formula(
        self,
        description: str,
        domain: str,
        variable_names: list[str] | None = None,
        metadata: dict | None = None,
        X: "np.ndarray | None" = None,
        y: "np.ndarray | None" = None,
    ) -> dict:
        """Generate a formula with a single, equation-agnostic prompt.

        Args:
            description: Human-readable equation description.
            domain: Domain string (e.g. "feynman_biology").
            variable_names: Input variable names.
            metadata: Protocol metadata dict (constants, ground_truth, etc.).
            X, y: accepted for call compatibility only; NOT used. No data
               statistics are placed in the prompt and nothing is fitted.
        """
        metadata = dict(metadata or {})
        disable_hc = _flag("HYPATIAX_DISABLE_HARDCODED")
        disable_hints = _flag("HYPATIAX_DISABLE_PROMPT_HINTS")
        # Defensive: never forward data-derived stats or any hint-like keys.
        for _k in ("_x_stats", "_y_stats", "ground_truth", "formula", "hint", "hints"):
            metadata.pop(_k, None)

        prompt = self._generate_standard_prompt(
            description, domain, variable_names, metadata
        )

        # Provenance is computed BEFORE the API call so error rows are as
        # auditable as success rows. The prompt is a single template with no
        # per-equation branches, so bypass_kind is "live" by construction; the
        # check below turns any future regression into a loud failure.
        _leak_markers = ("MANDATORY", "CODE TEMPLATE", "FORMULA HINT", "NEVER use")
        if any(m in prompt for m in _leak_markers):
            raise RuntimeError("equation-specific hint marker found in prompt")
        _prov = {
            "bypass_kind": "live",
            "bypass_flags": {
                "disable_hardcoded": disable_hc,
                "disable_prompt_hints": disable_hints,
                "hardcoded_bypass_present": False,  # _try_hardcoded_formula is a no-op here
            },
            # constants are sent verbatim ("task spec"); record exactly which
            "prompt_constants": dict(metadata.get("constants") or {}),
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "temperature_sent": False,
            "model_source": self.model_source,
        }
        _llm_attempted = False
        _response_received = False

        try:
            # FIX-ISSUE2B-LLM-TEMPERATURE: this call previously had no
            # `temperature` argument, so it silently used the Anthropic API
            # default (non-zero). Callers of this class (e.g.
            # EnhancedHybridSystemDeFi.generate_llm_formula, which delegates
            # here as its *preferred* path) assumed temperature=0 behaviour
            # -- see the comment at HybridDeFiMethod.run() in
            # run_comparative_suite_benchmark_v2.py claiming "At
            # temperature=0 this produces the same formula". That assumption
            # was false for this call site, which is why a fresh live call
            # per Phase-A run could return a structurally-equivalent but
            # not-bit-identical formula, producing the ~1e-9 R² spread
            # observed on Snell's Law in the Item 2b reproducibility check.
            # temperature=0.0 narrows (does not fully guarantee, since
            # provider-side serving batching can still vary) run-to-run
            # sampling variance.
            #
            # FIX-ISSUE2B-LLM-TEMPERATURE (applied): the comment above
            # described this mitigation but `temperature` was never
            # actually passed to _create_message() below,
            # so the API default (non-zero) was silently used the whole
            # time. Confirmed via a live smoke test that this model
            # (self.model, default "claude-sonnet-4-6") accepts
            # temperature=0.0 rather than rejecting it, so it's now
            # passed through for real.
            _gen_t0 = time.perf_counter()
            print(
                "GENERATE_ENTER "
                f"model={self.model!r} "
                f"domain={domain!r} "
                f"description_hash={hashlib.sha256(description.encode()).hexdigest()[:12]} "
                f"generate_formula_source={inspect.getsourcefile(self.generate_formula)!r} "
                f"api_helper_source={inspect.getsourcefile(_create_message)!r} "
                f"client_type={type(self.client).__module__}.{type(self.client).__name__}"
            )
            # [FIX-SDK1.0-TEMPERATURE] Superseding FIX-ISSUE2B-LLM-TEMPERATURE
            # above: that fix made this call start sending temperature=0.0
            # right as anthropic SDK v1.0 (2026-08-20) removed temperature/
            # top_p/top_k from Messages.create() outright -- it's a
            # client-side TypeError now (no **kwargs passthrough), and
            # current models also 400 on it server-side regardless of SDK
            # version. So this goes back to not sending temperature, but
            # for the opposite reason: it's no longer accepted at all, not
            # "not yet wired up". The temperature=0 determinism control
            # described in FIX-ISSUE2B-LLM-TEMPERATURE's comment above no
            # longer exists as an option -- run-to-run sampling variance
            # should be expected again.
            _llm_attempted = True
            response = _create_message(
                self.client,
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            _response_received = True
            print(
                "GENERATE_API_RETURN "
                f"dt={time.perf_counter() - _gen_t0:.6f}s "
                f"description_hash={hashlib.sha256(description.encode()).hexdigest()[:12]}"
            )
            # FIX (ThinkingBlock crash): response.content[0] is not guaranteed to be
            # the text block. When the model returns extended-thinking output, the
            # content list starts with a ThinkingBlock (no .text attribute), and
            # content[0].text raised 'ThinkingBlock' object has no attribute 'text'
            # on every case where thinking preceded the answer — observed on ~70%
            # of exp1 (v3/non-PCA) cases in the seed-42 re-run. Explicitly locate
            # the first text block instead of assuming position 0.
            text_blocks = [b for b in response.content if getattr(b, "type", None) == "text"]
            if not text_blocks:
                raise ValueError(
                    f"No text block in response.content "
                    f"(block types: {[getattr(b, 'type', type(b).__name__) for b in response.content]})"
                )
            content = text_blocks[0].text
            parsed = self._parse_response(content)

            _usage = getattr(response, "usage", None)

            return {
                "method": "pure_llm",
                "model": self.model,
                "description": description,
                "domain": domain,
                "formula": parsed.get("formula", "N/A"),
                "latex": parsed.get("latex", "N/A"),
                "python_code": parsed.get("python", "N/A"),
                "variables": parsed.get("variables", "N/A"),
                "assumptions": parsed.get("assumptions", "N/A"),
                "explanation": parsed.get("explanation", "N/A"),
                "raw_response": content,
                "specialized_prompt": False,
                # --- B2 provenance ---
                "llm_called": True,
                "llm_attempted": True,
                **_prov,
                "formula_present": parsed.get("python", "N/A") not in ("N/A", ""),
                "stop_reason": getattr(response, "stop_reason", None),
                "usage": {
                    "in": getattr(_usage, "input_tokens", None),
                    "out": getattr(_usage, "output_tokens", None),
                },
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(
                f"\n❌ ERROR: {type(e).__name__}: {str(e)}"
            )
            return {
                "method": "pure_llm",
                "model": self.model,
                "description": description,
                "domain": domain,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_repr": repr(e),
                # --- B2 provenance: keys always present so rows are auditable ---
                "formula": "",
                "python_code": "",
                # llm_called = a response actually came back; a rejected/failed
                # request is NOT a successful LLM call.
                "llm_called": _response_received,
                "llm_attempted": _llm_attempted,
                "error_stage": "post_response" if _response_received else "api_request",
                **_prov,
                "formula_present": False,
                "timestamp": datetime.now().isoformat(),
            }

    def _try_hardcoded_formula(
        self, description: str, desc_lower: str,
        variable_names: list[str], metadata: dict
    ) -> dict | None:
        """Intentionally a no-op: always returns None so every task goes to the LLM.

        This method used to return hardcoded ground-truth formulas (Feynman:
        I.6.20, I.41.16, II.2.42, II.6.15a, II.34.2, II.36.38, III.4.33;
        cross-benchmark: FEY_CHEM_NERNST) and OLS-fitted formulas (FEY_BIO_LOG,
        FEY_BIO_MM, FEY_BIO_ALLO, Arrhenius), bypassing the LLM entirely.
        All of those branches were deleted so the pure-LLM baseline can no
        longer be advantaged over the LLM-only comparison.  The method is kept
        only so scripts/bypass_audit.py can still call it and confirm that
        nothing is intercepted.  Do NOT add formula branches back here.
        """
        return None

    def _generate_standard_prompt(
        self, description: str, domain: str, variable_names: list[str], metadata: dict
    ) -> str:
        """Build the single equation-agnostic prompt."""
        var_info = f"\nVariables: {', '.join(variable_names)}" if variable_names else ""

        constants_info = ""
        if metadata and "constants" in metadata and metadata["constants"]:
            constants_info = "\n\n⚠️ CRITICAL - Use these EXACT constant values:"
            for const_name, const_value in metadata["constants"].items():
                constants_info += f"\n  • {const_name} = {const_value}"

        # No equation-specific hints exist in this prompt (deleted, not gated).
        # constants_info above is the protocol's task-spec constants; it must
        # be identical for every system compared (see input-parity paragraph).

        return f"""You are a mathematical formula expert in DeFi and quantitative finance.

Task: {description}
Domain: {domain}{var_info}{constants_info}

Provide your response in this EXACT format:

FORMULA:
[Write the formula in standard mathematical notation]

LATEX:
[Write the formula in LaTeX notation]

PYTHON:
def formula(param1, param2, ...):
    # Use individual parameters, NOT a dict
    # Use EXACT constants if specified above
    # Use numpy functions: np.sqrt, np.minimum, np.maximum, etc.
    return result

VARIABLES:
[List each variable with meaning]

ASSUMPTIONS:
[List assumptions]

EXPLANATION:
[Brief explanation]

CRITICAL REQUIREMENTS:
- Function signature must be: def formula(param1, param2, ...) with individual parameters
- DO NOT use dict parameters like def formula(params)
- Use numpy for all math operations (np.sqrt, np.log, etc.)
- Use EXACT constant values if specified
- NO scipy imports (use only numpy)
- NO markdown code blocks
- Ensure operations work element-wise on numpy arrays"""

    # Canonical section headers this parser understands, in the order the
    # prompt asks the model to emit them. A single regex finds every header
    # regardless of how much whitespace/blank-lines surround it, then each
    # section's body is just "everything between this header and the next
    # one" -- no reliance on the model emitting exactly one blank line
    # before the next ALL-CAPS: header, which --no-llm-cache live sampling
    # does not reliably produce (fixed 2026-08: previously used a
    # `(?=\n\n[A-Z]+:|$)` lookahead per-section, which silently swallowed
    # VARIABLES:/ASSUMPTIONS:/EXPLANATION: into python_code -- the only
    # field test_formula_accuracy() actually executes -- whenever the model
    # used a single newline instead of a blank line before the next
    # header. That produced intermittent PureLLM eval failures that varied
    # run-to-run with no code change, since nothing here is deterministic
    # LLM output.)
    _SECTION_HEADERS = ("FORMULA", "LATEX", "PYTHON", "VARIABLES", "ASSUMPTIONS", "EXPLANATION")

    def _parse_response(self, content: str) -> dict[str, str]:
        """Parse LLM response by splitting on known section headers.

        Robust to whatever whitespace/blank-line pattern the model used
        around each header -- does not require the next header to be
        preceded by exactly one blank line.
        """
        header_pat = re.compile(
            r"^\s*(" + "|".join(self._SECTION_HEADERS) + r")\s*:\s*$",
            re.IGNORECASE | re.MULTILINE,
        )

        matches = list(header_pat.finditer(content))
        parsed = {s.lower(): "N/A" for s in self._SECTION_HEADERS}

        if not matches:
            # Fall back to the original single-line FORMULA: <text> style,
            # in case the model put content on the same line as the header
            # instead of the line below it.
            m = re.search(r"FORMULA:\s*(.+)", content, re.IGNORECASE)
            if m:
                parsed["formula"] = m.group(1).strip()
            return parsed

        for i, m in enumerate(matches):
            name = m.group(1).lower()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body = content[start:end].strip()
            if name == "python":
                body = self._clean_python_code(body)
            parsed[name] = body if body else "N/A"

        return parsed

    def _clean_python_code(self, code: str) -> str:
        """Clean Python code: strip optional ```python / ``` fences."""
        code = code.strip()
        code = re.sub(r"^```(?:python)?\s*\n?", "", code, flags=re.IGNORECASE)
        code = re.sub(r"\n?```\s*$", "", code)
        return code.strip()

    def test_formula_accuracy(
        self,
        formula_dict: dict,
        X: np.ndarray,
        y_true: np.ndarray,
        var_names,
        verbose: bool = False,
    ) -> dict:
        """Test formula accuracy with FIXED evaluation logic."""
        try:
            python_code = formula_dict.get("python_code", "")
            if not python_code or python_code == "N/A":
                return {"error": "No code", "success": False}

            if verbose:
                print(f"\n  DEBUG - Code:\n{python_code}\n")

            # Execute the code.
            # Provide a rich namespace so formulas using bare names (sqrt, pi,
            # exp, ...) or math.* work even when the LLM ignores the "use numpy"
            # instruction.  Also intercept any `import` statements the LLM may
            # have included — they would raise NameError inside a restricted
            # exec dict, so we pre-populate the known-safe modules instead.
            import math as _math
            try:
                import scipy.special as _scipy_special
                _erf  = _scipy_special.erf
                _erfc = _scipy_special.erfc
            except ImportError:
                _erf  = np.vectorize(_math.erf)
                _erfc = np.vectorize(_math.erfc)

            _exec_globals = {
                "__builtins__": {
                    "__import__": __import__, "float": float, "int": int,
                    "len": len, "range": range, "max": max, "min": min,
                    "pow": pow, "round": round, "zip": zip,
                    "enumerate": enumerate, "isinstance": isinstance,
                    "tuple": tuple, "list": list, "bool": bool,
                    "ValueError": ValueError, "ZeroDivisionError": ZeroDivisionError,
                },
                "np":      np,
                "numpy":   np,
                "math":    _math,
                "pi":      np.pi,
                "e":       np.e,
                "inf":     np.inf,
                "nan":     np.nan,
                "exp":     lambda x: np.exp(np.clip(x, -500.0, 500.0)),
                "log":     np.log,
                "log2":    np.log2,
                "log10":   np.log10,
                "sqrt":    np.sqrt,
                "abs":     np.abs,
                "fabs":    np.abs,
                "sin":     np.sin,
                "cos":     np.cos,
                "tan":     np.tan,
                "arcsin":  lambda x: np.arcsin(np.clip(x, -1.0, 1.0)),
                "arccos":  lambda x: np.arccos(np.clip(x, -1.0, 1.0)),
                "arctan":  np.arctan,
                "arctan2": np.arctan2,
                "sinh":    np.sinh,
                "cosh":    np.cosh,
                "tanh":    np.tanh,
                "power":   np.power,
                "sign":    np.sign,
                "floor":   np.floor,
                "ceil":    np.ceil,
                "minimum": np.minimum,
                "maximum": np.maximum,
                "clip":    np.clip,
                "sum":     np.sum,
                "mean":    np.mean,
                "std":     np.std,
                "erf":     _erf,
                "erfc":    _erfc,
            }
            # B2: ONE namespace. With separate globals/locals dicts, any
            # module-level constant or helper the LLM wrote landed in locals,
            # but formula() resolves names in globals -> spurious NameError.
            _before = set(_exec_globals)
            exec(python_code, _exec_globals)

            # Find the function
            func = _exec_globals.get("formula")
            if not callable(func):
                func = next(
                    (
                        v
                        for k, v in _exec_globals.items()
                        if k not in _before and callable(v) and not k.startswith("_")
                    ),
                    None,
                )
            if not func:
                return {"error": "No function found", "success": False}

            if verbose:
                print(f"  DEBUG - Found function: {func.__name__}")
                print(f"  DEBUG - Signature: {inspect.signature(func)}")

            # Evaluate with comprehensive fallback
            try:
                y_pred = self.evaluate_function(func, X, var_names)

                # Check dimensions match
                if len(y_pred) != len(y_true):
                    return {
                        "error": f"Dimension mismatch: pred={len(y_pred)}, true={len(y_true)}",
                        "success": False,
                    }

            except Exception as eval_error:
                if verbose:
                    import traceback
                    traceback.print_exc()
                return {
                    "error": f"Evaluation failed: {str(eval_error)}",
                    "success": False,
                    "code_snippet": python_code[:200],
                }

            # B2/C4: NaN/inf predictions are failures, not "success with NaN R²".
            y_pred = np.asarray(y_pred, dtype=float)
            if not np.all(np.isfinite(y_pred)):
                n_bad = int((~np.isfinite(y_pred)).sum())
                return {
                    "success": False,
                    "error": f"non-finite predictions ({n_bad}/{len(y_pred)})",
                    "r2": float("nan"),
                    "r2_status": "nonfinite_prediction",
                }

            # Calculate metrics
            mse = np.mean((y_pred - y_true) ** 2)
            mae = np.mean(np.abs(y_pred - y_true))
            rmse = np.sqrt(mse)

            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

            # Relative threshold — scales with the data so tiny-y equations
            # (Photon y~1e-19, Zeeman y~1e-23, Newton y~1e-11, Lorentz y~1e-11)
            # are not misclassified as constant targets by an absolute 1e-10 floor.
            # FIX-EVAL-NEARCONST: the previous tolerance (1e-10 * max|y|^2 * n)
            # is relative to the OFFSET, not the spread, so y = 1e6 + N(0,1)
            # was classed "constant" and any prediction within ~10 of it scored
            # R^2 = 1.0 (true R^2 was -27). A target is constant only if its
            # peak-to-peak spread is at float-roundoff level of its magnitude.
            _mag = float(np.max(np.abs(y_true)))
            _is_const = float(np.ptp(y_true)) <= 1e-12 * _mag if _mag > 0 else True
            if not _is_const and ss_tot > 0:
                r2 = float(1.0 - ss_res / ss_tot)
                _r2_status = "ok"
            else:
                # Genuinely constant target: perfect only if predictions match it
                _match = np.allclose(y_pred, y_true, rtol=1e-9, atol=1e-30)
                r2 = 1.0 if _match else float("-inf")
                _r2_status = "constant_target_match" if _match else "constant_target_mismatch"

            return {
                "mse": float(mse),
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2),
                "r2_status": _r2_status,
                "success": True,
            }

        except SyntaxError as e:
            return {
                "error": f"Syntax error: {str(e)}",
                "success": False,
                "code": python_code,
            }
        except Exception as e:
            return {"error": f"Execution error: {str(e)}", "success": False}

    def save_results(self, filepath: str):
        """Save results to JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(_json_safe(self.results), f, indent=2, allow_nan=False)
        print(f"\n✅ Results saved: {filepath}")


def run_comprehensive_test(
    domains: list[str] = None, num_samples: int = 100, verbose: bool = False
):
    """Run comprehensive test."""
    protocol = DeFiExperimentProtocol()
    baseline = PureLLMBaseline()

    if domains is None:
        domains = protocol.get_all_domains()

    print("=" * 80)
    print("✨ FIXED PURE LLM BASELINE - WITH LIQUIDATION FIXES ✨".center(80))
    print("=" * 80)
    print(f"Model: {baseline.model}")
    print(f"Domains: {', '.join(domains)}")
    print(f"Samples: {num_samples}")
    print("=" * 80)

    all_results = []

    for domain in domains:
        print(f"\n{'=' * 80}")
        print(f"DOMAIN: {domain.upper()}".center(80))
        print("=" * 80)

        test_cases = protocol.load_test_data(domain, num_samples=num_samples)

        for i, (desc, X, y_true, var_names, meta) in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {desc}")
            print(f"  Variables: {', '.join(var_names)}")
            print(f"  Reference formula (console only, never sent to LLM): {meta.get('ground_truth', 'N/A')}")

            if meta.get("extrapolation_test"):
                print("  ⚠️  EXTRAPOLATION TEST")

            start = time.time()
            result = baseline.generate_formula(
                desc, domain, var_names, meta, X=X, y=y_true
            )
            result["generation_time"] = time.time() - start
            result["metadata"] = meta

            print(f"  Generated in {result['generation_time']:.2f}s")

            metrics = baseline.test_formula_accuracy(
                result, X, y_true, var_names, verbose=verbose
            )
            result["evaluation"] = metrics

            if metrics.get("success"):
                r2 = metrics["r2"]
                print(f"  ✅ R²: {r2:.6f}, RMSE: {metrics['rmse']:.6f}")

                if r2 > 0.99:
                    print("  🎯 EXCELLENT FIT")
                elif r2 > 0.95:
                    print("  ✓ Good fit")
                elif r2 > 0.80:
                    print("  ⚠️ Moderate fit")
                else:
                    print("  ❌ Poor fit")
            else:
                print(f"  ❌ Failed: {metrics.get('error', 'Unknown error')[:100]}")
                if verbose and "code_snippet" in metrics:
                    print(f"  Code: {metrics['code_snippet']}")

            all_results.append(result)
            baseline.results.append(result)
            time.sleep(1)

    print("\n" + "=" * 80)
    print("GENERATING REPORT".center(80))
    print("=" * 80)

    report = protocol.generate_experiment_report(all_results)

    os.makedirs("results", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    baseline.save_results(f"results/baseline_llm_FIXED_{ts}.json")

    with open(f"results/report_llm_FIXED_{ts}.json", "w") as f:
        json.dump(_json_safe(report), f, indent=2, allow_nan=False)

    print("\n" + "=" * 80)
    print("SUMMARY".center(80))
    print("=" * 80)

    overall = report["overall"]
    print(f"\n📊 Total: {overall['total_cases']}")
    print(
        f"Success: {overall['successful']}/{overall['total_cases']} ({100 * overall['success_rate']:.1f}%)"
    )

    if "mean_r2" in overall and overall["mean_r2"] is not None:
        print(f"Mean R²: {overall['mean_r2']:.6f}")
        print(f"Median R²: {overall['median_r2']:.6f}")

    print("\n📈 By Domain:")
    for domain, stats in report["by_domain"].items():
        mean_r2 = stats.get("mean_r2")
        r2_str = f"{mean_r2:.4f}" if mean_r2 is not None else "N/A"
        print(f"  {domain}: {stats['successful']}/{stats['total']} - R²: {r2_str}")

    if report.get("extrapolation_tests"):
        print("\n🎯 Extrapolation Tests:")
        for test in report["extrapolation_tests"]:
            status = "✅" if test["success"] else "❌"
            r2 = test.get("r2")
            r2_str = f"R²: {r2:.4f}" if r2 is not None else "Failed"
            print(f"  {status} {test['description'][:50]}: {r2_str}")

    print("\n" + "=" * 80)
    print("✨ COMPLETE - LIQUIDATION FIXED! ✨".center(80))
    print("=" * 80)


if __name__ == "__main__":
    from hypatiax.core.enforce_flags import enforce; enforce()  # fail-closed flag guard
    import sys

    verbose = "--verbose" in sys.argv
    run_comprehensive_test(domains=None, num_samples=100, verbose=verbose)
