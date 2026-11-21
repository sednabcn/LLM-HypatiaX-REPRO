"""
Pure LLM baseline for the DeFi / Feynman formula-discovery benchmark.

INPUT-PARITY POLICY
  The general-purpose baseline contains task wording, domain, variable names,
  and task-specific constants when supplied. Phase 2's explicit
  hds_prompt_context adds only the HDS-matched rounded constants and the
  DataPatternAnalyzer summary computed from the training split. No target
  formula, equation name/description, evaluation-set statistics, or equation-
  specific hints are included. All former equation-specific hint blocks
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
from hypatiax.safe_formula import parse_formula
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


def _opt_in(name: str) -> bool:
    """True ONLY when env var `name` is explicitly set to 1/true/yes.

    Unlike _flag() this is fail-OPEN-to-OFF: unset/empty means False. Use it
    for scoring conveniences (e.g. sign-flip) that must never be active by
    default, because they would break input/scoring parity between arms.
    """
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


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
    """Make exactly one shared-wrapper API attempt using Core-15 temperature=0.25.

    The wrapper inserts the protocol-fixed temperature and fails closed if the
    client rejects it. No retry may silently fall back to a provider default.
    """
    t0 = time.perf_counter()
    print(
        "API_ENTER "
        f"model={kwargs.get('model')!r} "
        f"max_tokens={kwargs.get('max_tokens')!r} "
        f"messages={len(kwargs.get('messages', []))}"
    )
    try:
        from hypatiax.core.llm_call import create_message
        response = create_message(client, **kwargs)
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
        Evaluate a parsed formula using ordered, fail-closed binding strategies.

        A failed vectorized attempt must not prevent scalar or named binding
        fallbacks. HYPATIAX_STRICT controls formula provenance, not whether a
        safe evaluator may try its remaining deterministic binding strategies.
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

            try:
                # Try row-by-row
                y = np.empty(n_samples, dtype=float)
                for i in range(n_samples):
                    y[i] = func(*[X[i, j] for j in range(n_features)])
                return y
            except Exception as _e:
                import logging as _lg, os as _os
                _lg.getLogger(__name__).warning('swallowed: %r', _e)

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

        # Do not invent values for required parameters that have no matching
        # input column. Such a zero-placeholder can turn an under-specified
        # generated function into a plausible but scientifically different
        # equation. If no complete variable binding is possible, fail closed.

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
            # These are intended defaults until this call updates them;
            # never inherit provenance from a previous thread-local API call.
            "temperature_sent": False,
            "temperature_requested": __import__("hypatiax.core.llm_call", fromlist=["x"]).configured_temperature(),
            "model_source": self.model_source,
        }
        _llm_attempted = False
        _response_received = False

        try:
            # The shared wrapper always requests Core-15 temperature=0.25
            # and fails closed rather than retrying with a provider default.
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
            _llm_attempted = True
            response = _create_message(
                self.client,
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            _temperature_info = __import__("hypatiax.core.llm_call", fromlist=["x"]).last_call_info()
            _prov["temperature_sent"] = _temperature_info.get("temperature_sent")
            _prov["temperature_requested"] = _temperature_info.get("temperature_requested")
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
                "generation_path": "pure_llm_api",  # PHASE1-FIX
                "formula_present": parsed.get("python", "N/A") not in ("N/A", ""),
                "stop_reason": getattr(response, "stop_reason", None),
                "usage": {
                    "in": getattr(_usage, "input_tokens", None),
                    "out": getattr(_usage, "output_tokens", None),
                },
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            # Only read thread-local wrapper metadata after this invocation
            # actually entered the API wrapper. Otherwise it may describe a
            # previous call on the same thread.
            if _llm_attempted:
                _temperature_info = __import__("hypatiax.core.llm_call", fromlist=["x"]).last_call_info()
                _prov["temperature_sent"] = bool(_temperature_info.get("temperature_sent", False))
                _prov["temperature_requested"] = _temperature_info.get("temperature_requested", 0.25)
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
                "generation_path": "pure_llm_api" if _response_received else "pure_llm_api_failed",
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
        if metadata and metadata.get("hds_prompt_context"):
            # HDS's fixed rounded constants are Phase 2 matched-input context only.
            constants_info = """\n\nAVAILABLE PHYSICAL CONSTANTS (use these exact Python names):
  h=6.626e-34 (Planck), hbar=1.055e-34 (reduced Planck), c=2.998e8 (speed of light),
  k_B=1.381e-23 (Boltzmann), k=1.381e-23, N_A=6.022e23 (Avogadro), g_n=9.807,
  m_e=9.109e-31 (electron mass), q_e=1.602e-19 (elementary charge),
  epsilon0=8.854e-12 (vacuum permittivity), mu0=1.257e-6 (vacuum permeability)
Do NOT use bare 'e' for elementary charge — use q_e instead."""
        elif metadata and metadata.get("constants"):
            # Preserve the general-purpose baseline's task-specific constants.
            task_constants = ", ".join(
                f"{name}={value}" for name, value in metadata["constants"].items()
            )
            constants_info = f"\n\nTASK-SPEC CONSTANTS (use these exact values): {task_constants}"
        patterns_info = ""
        if metadata and metadata.get("hds_prompt_context") and metadata.get("data_patterns") is not None:
            patterns_info = "\n\nDATA PATTERNS (computed from training split only):\n"
            patterns_info += json.dumps(metadata["data_patterns"], indent=2)

        # No equation-specific hints exist in this prompt (deleted, not gated).
        # constants_info above is the protocol's task-spec constants; it must
        # be identical for every system compared (see input-parity paragraph).

        signature = ", ".join(variable_names or [])
        return f"""You are a mathematical formula expert in DeFi and quantitative finance.

Task: {description}
Domain: {domain}{var_info}{constants_info}{patterns_info}

The only input variables available to the formula are exactly: {", ".join(variable_names or [])}.
Provide your response in this EXACT format:

FORMULA:
[Write the formula in standard mathematical notation]

LATEX:
[Write the formula in LaTeX notation]

PYTHON:
def formula({signature}):
    # Use only the declared input variables, numeric literals, and numpy/math functions.
    # Every coefficient or constant not supplied in the task specification must be a numeric literal.
    # Do not add parameters for unknown coefficients or other undeclared symbols.
    # Do not estimate or fit coefficients from X or y.
    return result

VARIABLES:
[List each declared input variable with meaning]

ASSUMPTIONS:
[List assumptions]

EXPLANATION:
[Brief explanation]

CRITICAL REQUIREMENTS:
- The function signature must match the declared input variables EXACTLY, in the same order: def formula({signature})
- Do not add parameters such as a, b, c, or other symbols unless they are declared input variables.
- Every symbol in the expression must be a declared input, a numeric literal, or an approved numpy/math function.
- Do not use dict parameters, *args, **kwargs, or optional/default parameters.
- Use numpy for element-wise math operations (np.sqrt, np.minimum, np.maximum, etc.).
- Use EXACT task-specification constant values if supplied; otherwise express coefficients as numeric literals.
- Do not infer coefficients from training data or fit any parameters.
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

    @staticmethod
    def validate_formula_signature(python_code: str, var_names: list[str] | None):
        """Require an LLM formula to accept exactly the declared input variables.

        This is a structural contract only: it never supplies or estimates
        missing coefficients. Unknown symbols must be represented as numeric
        literals in the generated expression or the formula fails closed.
        """
        func = parse_formula(python_code)
        expected = list(var_names or [])
        params = list(inspect.signature(func).parameters.values())
        actual = [param.name for param in params]
        if actual != expected:
            raise ValueError(
                "formula signature mismatch: "
                f"expected parameters {expected}, got {actual}"
            )
        invalid_kinds = [
            param.name for param in params
            if param.kind not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ) or param.default is not inspect.Parameter.empty
        ]
        if invalid_kinds:
            raise ValueError(
                "formula signature contains unsupported variadic, keyword-only, "
                f"or default parameters: {invalid_kinds}"
            )
        return func

    def test_formula_accuracy(
        self,
        formula_dict: dict,
        X: np.ndarray,
        y_true: np.ndarray,
        var_names,
        verbose: bool = False,
    ) -> dict:
        """Test formula accuracy with FIXED evaluation logic.

        Result-row contract for scored rows (every row that reaches the R²
        stage carries `r2`, `r2_status`, `r2_sign_flip`, `success`):
          * non-finite predictions -> success=False, r2=None,
                                      r2_status="nonfinite_pred"
          * zero-variance target   -> success=False, r2=None,
                                      r2_status="degenerate_target"
          * otherwise              -> success=True, canonical R^2.
        Sign-flip rescoring (score -y_pred when it beats y_pred) is OFF by
        default and only enabled by HYPATIAX_R2_SIGN_FLIP=1; the row always
        records whether a flip was applied in `r2_sign_flip`.
        """
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
            func = self.validate_formula_signature(python_code, var_names)

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
            # Contract: r2 = None (null) with r2_status carrying the reason; consumers score None as unavailable.
            # (_json_safe keeps None as null on disk.)
            y_pred = np.asarray(y_pred, dtype=float)
            y_true = np.asarray(y_true, dtype=float)
            if not np.all(np.isfinite(y_pred)):
                n_bad = int((~np.isfinite(y_pred)).sum())
                return {
                    "success": False,
                    "error": f"non-finite predictions ({n_bad}/{len(y_pred)})",
                    "r2": None,
                    "r2_status": "nonfinite_pred",
                    "r2_sign_flip": False, "reason": "nonfinite_metric",
                }

            # Calculate metrics
            mse = np.mean((y_pred - y_true) ** 2)
            mae = np.mean(np.abs(y_pred - y_true))
            rmse = np.sqrt(mse)

            # PHASE1-FIX-P3b: canonical R^2 (hypatiax.core.r2_canonical.r2_checked).
            r2, _r2_status = _r2_checked_call(y_true, y_pred)

            # A zero-variance target has no defined R^2. It is reported as a
            # degenerate, FAILED row (r2 = None) instead of being scored 1.0 for a
            # trivial exact match or -inf for a mismatch: a constant target must
            # never contribute a "perfect" score to the arm.
            # NOTE: this replaces the old constant_target_match /
            # constant_target_mismatch contract; update test_baseline_regressions.
            if _r2_status == "degenerate_target":
                return {
                    "mse": float(mse),
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "r2": None,
                    "r2_status": "degenerate_target",
                    "r2_sign_flip": False,
                    "success": False,
                    "error": "degenerate target (zero variance): R^2 undefined", "reason": "nonfinite_metric",
                }

            # Optional sign-flip rescoring. OFF by default (explicit opt-in only);
            # whether it fired is always recorded in `r2_sign_flip`.
            r2_sign_flip = False
            if _opt_in("HYPATIAX_R2_SIGN_FLIP") and np.isfinite(r2) and r2 < 0:
                _r2_alt, _alt_status = _r2_checked_call(y_true, -y_pred)
                if np.isfinite(_r2_alt) and _r2_alt > r2:
                    r2, _r2_status, r2_sign_flip = _r2_alt, _alt_status, True
                    y_pred = -y_pred
                    mse = np.mean((y_pred - y_true) ** 2)
                    mae = np.mean(np.abs(y_pred - y_true))
                    rmse = np.sqrt(mse)

            return {
                "mse": float(mse),
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2),
                "r2_status": _r2_status,
                "r2_sign_flip": r2_sign_flip,
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


def _r2_checked_call(y_true, y_pred):
    """Thin wrapper around the canonical R^2 so it is imported lazily (and in
    one place). Returns (r2, status)."""
    # HYPATIAX_R2_CANONICAL_MIGRATION_V1
    from hypatiax.core.r2_canonical import r2_checked as _r2_checked
    return _r2_checked(y_true, y_pred)


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
