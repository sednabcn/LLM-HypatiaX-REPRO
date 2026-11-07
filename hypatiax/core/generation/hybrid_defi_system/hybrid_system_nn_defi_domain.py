# hybrid_system_nn_defi_domain.py
"""
Enhanced Hybrid System - LLM symbolic formula + Neural Network ensemble.
Fully implements:
  - generate_llm_formula()    (LLM symbolic discovery)
  - train_nn()                (NN baseline)
  - hybrid_predict()          (LLM-guided + NN ensemble)
  - evaluate_llm_formula()    (evaluate formula on held-out data)
  - --batch CLI mode          (runs full DeFi benchmark suite, writes hybrid_defi_*.json)
"""

from hypatiax.safe_formula import parse_formula
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root bootstrap — must run before any `hypatiax` import.
# This file lives at:
#   hypatiax/core/generation/hybrid_defi_system/hybrid_system_nn_defi_domain.py
# Walking up 4 levels (parents[4]) reaches the repo root where the top-level
# `hypatiax/` package directory lives.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import numpy as np
import torch
import torch.nn as nn
from anthropic import Anthropic
from dotenv import load_dotenv

from hypatiax.core.r2_canonical import r2_checked
from hypatiax.protocols.experiment_protocol_defi import DeFiExperimentProtocol

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


# ---------------------------------------------------------------------------
# Neural Network
# ---------------------------------------------------------------------------

class ImprovedNN(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list[int] = None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [128, 64, 32]
        layers = []
        prev = input_dim
        for h in hidden_dims:
            # LayerNorm instead of BatchNorm1d — no batch-size sensitivity.
            # No Dropout — 160 training samples cannot afford activation dropout;
            # it degrades convergence without adding regularisation benefit.
            layers += [nn.Linear(prev, h), nn.LayerNorm(h), nn.SiLU()]
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def train_nn_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    hidden_dims: list[int] = None,
    epochs: int = 1000,
    lr: float = 0.003,
    seed: int | None = None,
) -> tuple[ImprovedNN, object, object]:
    """Train NN; returns (model, scaler_X, scaler_y).

    KEY IMPROVEMENTS vs original:
    - LayerNorm + SiLU instead of BatchNorm + ReLU + Dropout
    - CosineAnnealingWarmRestarts LR schedule (better than StepLR)
    - Best-model tracking via deep .clone() of state dict
    - Early stopping with patience=100
    - 1000 epochs (up from 500)
    - Adaptive architecture by input dimensionality

    FIX-ISSUE2B-UNSEEDED-NN: `seed`, when given, is passed to
    torch.manual_seed() right before the model is constructed. Previously
    this function had no seeding at all, so ImprovedNN's weight
    initialization used whatever torch's global RNG state happened to be
    -- fine within a single process, but not reproducible across the
    separate process invocations used by the Item 2b reproducibility
    check (phaseA_run1/run2/run3). The harness's own residual-correction
    step and the HSL/M4 method already follow this same
    sha256(description)-derived-seed pattern; this brings EHD/M3's
    *primary* NN training step in line with it too, rather than leaving
    it as the one unseeded stage in the pipeline.
    """
    from sklearn.preprocessing import StandardScaler

    if seed is not None:
        torch.manual_seed(seed)

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    Xs = scaler_X.fit_transform(X_train)
    ys = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()

    # Adaptive hidden dims based on input size
    n_vars = X_train.shape[1]
    if hidden_dims is None:
        if n_vars <= 2:
            hidden_dims = [128, 64, 32]
        elif n_vars <= 4:
            hidden_dims = [256, 128, 64, 32]
        else:
            hidden_dims = [512, 256, 128, 64]

    model = ImprovedNN(X_train.shape[1], hidden_dims)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=200, T_mult=2, eta_min=3e-6
    )
    criterion = nn.MSELoss()

    Xt = torch.FloatTensor(Xs)
    yt = torch.FloatTensor(ys).reshape(-1, 1)

    best_loss  = float("inf")
    best_state = None
    patience   = 100
    no_improve = 0

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(Xt), yt)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step(epoch)

        val_loss = loss.item()
        if val_loss < best_loss - 1e-8:
            best_loss  = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    return model, scaler_X, scaler_y


def nn_predict(model, scaler_X, scaler_y, X: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        Xs = scaler_X.transform(X)
        ys = model(torch.FloatTensor(Xs)).numpy().flatten()
        return scaler_y.inverse_transform(ys.reshape(-1, 1)).flatten()


def r2_score_checked(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, str]:
    """Canonical R2 and its status (hypatiax/core/r2_canonical.py).

    R2-CANONICAL: the old guard here was ABSOLUTE (ss_tot < 1e-30 -> 0.0), which scored
    legitimately tiny-scale targets (Photon ~1e-19, Zeeman ~1e-23) as 0.0 whatever the
    prediction.  The canonical guard is RELATIVE.  Status is one of: ok,
    degenerate_target, nonfinite_target, nonfinite_pred, bad_shape.
    """
    # HYPATIAX_R2_CANONICAL_MIGRATION_V1
    with np.errstate(over="ignore", invalid="ignore"):
        return r2_checked(y_true, y_pred)


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """R2 for INTERNAL model selection (Stage-2 fitting, NN-vs-formula decision).

    Keeps this module's historical contract: an undefined or failed score (degenerate
    target, non-finite prediction, overflow) is returned as 0.0 so the decision logic
    below never has to compare NaN/-inf.  It is never 1.0.  Use r2_score_checked() when
    the status matters; reported rows carry it as evaluation["r2_status"].
    """
    val, status = r2_score_checked(y_true, y_pred)
    return float(val) if status == "ok" and np.isfinite(val) else 0.0


# ---------------------------------------------------------------------------
# Formula evaluation helpers
# -----------------------------def _safe_exec_formula(python_code: str, X: np.ndarray, var_names: list[str]) -> np.ndarray | None:
    """Safely evaluate a restricted LLM formula against a feature matrix."""
    try:
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0:
            return None
        if len(var_names) != X.shape[1] or not np.all(np.isfinite(X)):
            return None

        func = parse_formula(python_code)
        args = [X[:, i] for i in range(X.shape[1])]

        try:
            result = func(*args)
        except Exception:
            result = np.array([func(*row) for row in X], dtype=float)

        result = np.asarray(result, dtype=float)
        if result.ndim == 0:
            result = np.full(X.shape[0], float(result))
        elif result.ndim != 1:
            return None

        if result.shape != (X.shape[0],) or not np.all(np.isfinite(result)):
            return None
        return result
    except Exception:
        return None

# -----------------------------------------------

def _parametrize_formula(python_code: str, var_names: list[str]) -> tuple:
    """
    Make formula parameters free by replacing their assigned numeric values
    with _P[i] index references so scipy can optimize them.

    Works for ANY case convention the LLM uses (Vmax, km, VMAX, r, K, etc.).
    Does NOT require the LLM to follow any naming convention.

    Two strategies, tried in order:
      A) Named assignments — finds `name = <number>` lines and replaces
         the literal with _P[i].  Handles: Vmax=80.0, Km=5.0, r=0.5, etc.
      B) Inline literals — fallback for fully numeric formulas like
         `return 80.0 * S / (5.0 + S)`. Replaces all non-structural
         numeric literals (skips 0, 1, 2) with _P[i].

    Returns (parametrized_code, init_vals, param_names).
    param_names is empty for the inline-literal fallback.
    """
    _SKIP = set(var_names or []) | {
        'np', 'numpy', 'math', 'import', 'True', 'False', 'None'
    }
    body_start = python_code.find('\n')
    sig  = python_code[:body_start]
    body = python_code[body_start:]

    # ── Strategy A: named assignments ─────────────────────────────────
    pattern = re.compile(
        r'^([ \t]+)([a-zA-Z_]\w*)\s*='
        r'\s*([+-]?\s*\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)\s*$',
        re.MULTILINE,
    )
    seen_names: dict[str, int] = {}
    init_vals: list[float] = []
    new_body = body

    for m in pattern.finditer(body):
        indent, name, val_str = m.group(1), m.group(2), m.group(3)
        if name in _SKIP or name in seen_names:
            continue
        idx = len(init_vals)
        seen_names[name] = idx
        init_vals.append(float(val_str.replace(' ', '')))
        # Use re.sub with count=1 so only the first occurrence of this exact
        # assignment line is replaced (str.replace would silently rewrite all
        # duplicate lines if the same name=value pair appeared more than once).
        new_body = re.sub(
            re.escape(m.group(0)),
            f"{indent}{name} = _P[{idx}]  # was {val_str.strip()}\n",
            new_body,
            count=1,
        )

    if init_vals:
        return sig + "\n" + new_body, init_vals, list(seen_names.keys())

    # ── Strategy B: inline numeric literals ────────────────────────────
    # 0, 1, 2 are treated as structural: skipping them avoids over-
    # parametrizing formulas that contain these as ordinary mathematical
    # constants (identity, sign, squaring).  Removing 2.0 from this set
    # caused curve_fit to gain an unnecessary free dimension on formulas
    # like Michaelis-Menten, confusing its local search, triggering the
    # expensive differential_evolution fallback (+10 s), and degrading
    # both speed and R².  Formulas where 2.0 genuinely IS a scale factor
    # (e.g. impermanent loss 2*sqrt(r)/(1+r)) are handled by Strategy A's
    # named-assignment pass instead, so they are unaffected by this choice.
    _STRUCTURAL = {0.0, 1.0, 2.0}
    counter = [0]
    b_init: list[float] = []

    def _replace_literal(m: re.Match) -> str:
        val = float(m.group(0))
        if val in _STRUCTURAL:
            return m.group(0)
        idx = counter[0]
        counter[0] += 1
        b_init.append(val)
        return f"_P[{idx}]"

    new_body_b = re.sub(
        r'\b\d+\.?\d*(?:[eE][+-]?\d+)?\b',
        _replace_literal,
        body,
    )
    return sig + "\n" + new_body_b, b_init, []


def fit_formula_params(
    python_code: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    variable_names: list[str],
    verbose: bool = False,
) -> tuple[str | None, float]:
    """Evaluate a formula through the restricted AST gate.

    Parameter fitting is intentionally disabled: the previous implementation
    executed parametrized generated Python with exec/compile, bypassing the
    formula safety gate.
    """
    try:
        X = np.asarray(X_train, dtype=float)
        y = np.asarray(y_train, dtype=float)

        if (
            X.ndim != 2
            or X.shape[0] == 0
            or X.shape[1] == 0
            or y.ndim != 1
            or y.shape[0] != X.shape[0]
            or len(variable_names) != X.shape[1]
            or not np.isfinite(X).all()
            or not np.isfinite(y).all()
        ):
            return None, -np.inf

        preds = _safe_exec_formula(python_code, X, variable_names)
        if preds is None:
            return None, -np.inf

        preds = np.asarray(preds, dtype=float)
        if preds.shape != y.shape or not np.isfinite(preds).all():
            return None, -np.inf

        score = float(r2_score(y, preds))
        if not np.isfinite(score):
            return None, -np.inf

        if verbose:
            print(
                "  [Stage2] parameter fitting disabled; "
                f"restricted raw-formula R²={score:.4f}"
            )
        return python_code, score

    except Exception:
        return None, -np.inf


# ---------------------------------------------------------------------------
# Main Hybrid System
# ---------------------------------------------------------------------------

def _create_message_deterministic(client, **kwargs):
    """Call client.messages.create(), preferring temperature=0.0 for
    reproducibility (see FIX-ISSUE2B-LLM-TEMPERATURE), but tolerate newer
    models that no longer accept the parameter at all.

    FIX-ISSUE2B-LLM-TEMPERATURE-DEPRECATED: duplicated from the identical
    helper in hybrid_system_llm_nn_all_domains.py (HSL) / baseline_pure_llm_
    defi_discovery.py, per this codebase's existing convention of
    per-file copies rather than cross-module imports for this helper.
    Without this, EnhancedHybridSystemDeFi's local fallback (both the
    initial call and its max_tokens/malformed-response retry) called
    client.messages.create(temperature=0.0, ...) directly -- which raises
    on any model that has deprecated the temperature/top_p/top_k sampling
    parameters (Claude Sonnet 4.6+, Opus 4.7+), and that exception was
    swallowed by generate_llm_formula's bare except into an N/A/error
    result rather than retried, unlike HSL's equivalent fallback. Tries
    temperature=0.0 first and retries once without it only on that
    specific deprecation error, so determinism is preserved wherever the
    model still supports it, and the fallback degrades the same way HSL's
    does instead of going silently dark.
    """
    try:
        return client.messages.create(temperature=0.0, **kwargs)
    except Exception as e:
        msg = str(e)
        if "temperature" in msg.lower() and "deprecated" in msg.lower():
            return client.messages.create(**kwargs)
        raise


class EnhancedHybridSystemDeFi:
    """
    Hybrid system: LLM symbolic formula + NN, with ensemble fallback.

    Public API used by test_enhanced_defi_extrapolation.py:
      generate_llm_formula(description, domain, var_names, metadata, verbose) -> Dict
      hybrid_predict(description, domain, X, y, var_names, metadata, verbose) -> Dict
      evaluate_llm_formula(result_dict, X, y, var_names, verbose) -> Dict
    """

    def __init__(self, model: str = "claude-sonnet-4-6", no_cache: bool = False):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.results = []
        self.formula_cache: dict[str, dict] = {}
        self._no_cache = no_cache   # honoured in generate_llm_formula

        # Clean-rerun guard: the delegate baseline reads these two env flags.
        # If either is unset, hardcoded answers / prompt hints may leak into
        # the LLM arm, so say so up front rather than let it pass silently.
        from hypatiax.core.flags import flag_on   # single source of truth (fail closed, strict '1')
        _unset = [
            n for n in ("HYPATIAX_DISABLE_HARDCODED", "HYPATIAX_DISABLE_PROMPT_HINTS")
            if not flag_on(n)
        ]
        self.strict_live = not _unset
        if _unset:
            print(
                f"⚠  not a clean live run: {', '.join(_unset)} not set to 1 "
                f"(hardcoded answers / prompt hints may be active)"
            )

        # FIX-ISSUE2B-LLM-API-NONDETERMINISM: the Anthropic API (like most
        # LLM inference stacks) is not guaranteed to return byte-identical
        # completions for an identical prompt at temperature=0 -- this is a
        # server-side batching/kernel effect, not something fixable with
        # local seeding. Item 2b's reproducibility check runs this class
        # fresh in 3 *separate processes* (phaseA_run1/run2/run3), so
        # in-memory formula_cache (above) never helps across runs even
        # though it prevents redundant calls within one run.
        #
        # HYPATIAX_LLM_FREEZE_CACHE, when set to a file path, makes this
        # class read-through/write-through a JSON file shared across
        # process invocations: run1 populates it on cache misses, and
        # run2/run3 then get bit-identical formula text for the same
        # (description, domain, variable_names) key instead of re-querying
        # the API -- removing the API as a source of cross-run variance.
        # This is opt-in and does not change default behaviour for normal
        # (non-reproducibility-check) use of this class.
        self._freeze_cache_path = os.getenv("HYPATIAX_LLM_FREEZE_CACHE")
        if self._freeze_cache_path:
            self._load_frozen_cache()

        # Delegate LLM formula generation to PureLLMBaseline so Feynman
        # equations (biology/chemistry/physics) benefit from hardcoded OLS
        # paths, variant guards, and all prompt fixes — without reimplementing
        # that logic here.  The DeFi-specific specialised prompts in this class
        # remain as a fallback for pure DeFi equations.
        try:
            from hypatiax.core.base_pure_llm.baseline_pure_llm_defi_discovery import (
                PureLLMBaseline as _PureLLMBaseline,
            )
            self._llm_baseline = _PureLLMBaseline(model=model)
        except Exception as e:
            print(
                f"⚠  PureLLMBaseline delegate unavailable; ALL tasks will use the "
                f"local fallback prompt: {type(e).__name__}: {str(e)[:120]}"
            )
            self._llm_baseline = None

    # ------------------------------------------------------------------
    # Frozen (cross-process) LLM cache — see FIX-ISSUE2B-LLM-API-NONDETERMINISM
    # in __init__ for why this exists.
    # ------------------------------------------------------------------

    def _load_frozen_cache(self) -> None:
        """Load any previously-persisted formula results into memory.

        Tolerant of a missing/empty/corrupt file — a frozen cache miss
        should never be worse than not having the feature at all, so any
        failure here just falls back to normal (live-API) behaviour.
        """
        try:
            p = Path(self._freeze_cache_path)
            if p.exists() and p.stat().st_size > 0:
                with open(p, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.formula_cache.update(data)
        except Exception as _e:
            import logging as _lg, os as _os
            _lg.getLogger(__name__).warning('swallowed: %r', _e)
            if _os.environ.get('HYPATIAX_STRICT') == '1': raise

    def _save_to_frozen_cache(self, cache_key: str, result: dict) -> None:
        """Persist one entry to the shared frozen-cache file (atomic write).

        Re-reads the file first so concurrent/sequential process
        invocations don't clobber each other's entries — each of
        phaseA_run1/run2/run3 only ever *adds* keys it generated fresh; a
        key already present (written by an earlier run) is never
        overwritten, which is what guarantees run2/run3 see exactly what
        run1 saw.
        """
        try:
            p = Path(self._freeze_cache_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            existing: dict = {}
            if p.exists() and p.stat().st_size > 0:
                try:
                    with open(p, "r") as f:
                        existing = json.load(f)
                except Exception:
                    existing = {}
            if cache_key not in existing:
                existing[cache_key] = result
                tmp = p.with_suffix(p.suffix + f".tmp{os.getpid()}")
                with open(tmp, "w") as f:
                    json.dump(existing, f)
                os.replace(tmp, p)   # atomic on POSIX
        except Exception as _e:
            import logging as _lg, os as _os
            _lg.getLogger(__name__).warning('swallowed: %r', _e)
            if _os.environ.get('HYPATIAX_STRICT') == '1': raise

    # ------------------------------------------------------------------
    # LLM formula generation
    # ------------------------------------------------------------------

    def generate_llm_formula(
        self,
        description: str,
        domain: str,
        variable_names: list[str],
        metadata: dict,
        verbose: bool = False,
        X: "np.ndarray | None" = None,
        y: "np.ndarray | None" = None,
    ) -> dict:
        cache_key = f"{description}|{domain}|{','.join(variable_names)}"

        # Frozen cross-process cache takes priority over everything else,
        # including --no-llm-cache: freezing exists specifically to pin the
        # LLM's output identical across the separate phaseA_run* processes
        # used by the Item 2b reproducibility check, which is a different
        # goal from the intra-run "always call the live API" semantics
        # that --no-llm-cache/_no_cache provides.
        if self._freeze_cache_path and cache_key in self.formula_cache:
            print(
                f"⚠  frozen-cache hit (HYPATIAX_LLM_FREEZE_CACHE): not a fresh LLM "
                f"call for: {description[:50]}"
            )
            _hit = self.formula_cache[cache_key].copy()
            _hit.setdefault("llm_source", "frozen_cache_unknown_origin")
            return _hit

        if not self._no_cache and cache_key in self.formula_cache:
            return self.formula_cache[cache_key].copy()

        # ── Delegate to PureLLMBaseline (preferred path) ─────────────────────
        # Feynman biology/chemistry/physics equations benefit from hardcoded OLS
        # paths, variant guards, and all prompt fixes in PureLLMBaseline.
        # Pure DeFi equations fall through to the local specialised prompts.
        if self._llm_baseline is not None:
            try:
                result = self._llm_baseline.generate_formula(
                    description=description,
                    domain=domain,
                    variable_names=variable_names,
                    metadata=metadata,
                    X=X,
                    y=y,
                )
                code = result.get("python_code", "N/A")
                if code and code != "N/A" and "return" in code:
                    result["llm_source"] = "delegate"
                    if not self._no_cache:
                        self.formula_cache[cache_key] = result.copy()
                    if self._freeze_cache_path:
                        self.formula_cache[cache_key] = result.copy()
                        self._save_to_frozen_cache(cache_key, result)
                    if verbose:
                        print(f"  [LLM→PureLLM] formula: {result.get('formula','')[:80]}")
                    return result
                _why = result.get("error") or "empty/N/A python_code"
                print(
                    f"⚠  local fallback for: {description[:50]} "
                    f"(delegate returned no usable code: {str(_why)[:100]})"
                )
            except Exception as e:
                print(
                    f"⚠  local fallback for: {description[:50]} "
                    f"(delegate raised {type(e).__name__}: {str(e)[:100]})"
                )
        else:
            print(f"⚠  local fallback for: {description[:50]} (no delegate)")

        # ── Local DeFi implementation (fallback) ─────────────────────────────
        # FIX GT-LEAK-2 (2026-08-10): _specialized_prompt() used to be called
        # here for ["kelly", "impermanent loss", "liquidation", "expected
        # shortfall", "black-scholes", "sharpe", "value at risk"] cases.
        # Unlike the ground-truth-hint leaks fixed elsewhere in this codebase
        # (hypatiax_defi_benchmark_v3c.py Fix 14, hybrid_system_llm_nn_all_
        # domains.py FIX GT-LEAK), _specialized_prompt() didn't add a hint to
        # a genuine derivation request — for kelly/impermanent-loss/VaR/
        # expected-shortfall it returned the COMPLETE pre-solved answer,
        # already formatted in the FORMULA:/PYTHON:/EXPLANATION: schema the
        # parser expects, with no task or question posed to the model at
        # all. That's not a leak into a derivation — it's skipping the
        # derivation entirely while still logging the result as "LLM
        # formula: <description>". This only fired on the fallback path
        # (when the audited PureLLMBaseline delegate above failed or
        # returned N/A). Always using the genuine _standard_prompt() here
        # means the LLM is actually asked to derive the formula in every
        # case; _specialized_prompt() is left in place below for reference
        # but is no longer called.
        prompt = self._standard_prompt(description, domain, variable_names, metadata)

        try:
            resp = _create_message_deterministic(
                self.client,
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text if resp.content else ""

            # Guard against stop_reason=max_tokens: retry with tighter prompt.
            stop_reason = getattr(resp, "stop_reason", None)
            if stop_reason == "max_tokens" or (
                content and "def formula" in content and "return" not in content
            ):
                tight_prompt = (
                    f"Give ONLY the Python function for: {description}\n"
                    f"Variables: {', '.join(variable_names)}\n\n"
                    f"PYTHON:\n"
                    f"def formula({', '.join(variable_names)}):\n"
                    f"    import numpy as np\n"
                    f"    return ...\n\n"
                    f"Reply with ONLY the def block, no explanation."
                )
                resp2 = _create_message_deterministic(
                    self.client,
                    model=self.model,
                    max_tokens=512,
                    messages=[{"role": "user", "content": tight_prompt}],
                )
                content = resp2.content[0].text if resp2.content else content

            parsed = self._parse_response(content)

            python_code = parsed.get("python", "N/A")
            if python_code and python_code != "N/A" and "return" not in python_code:
                python_code = "N/A"

            result = {
                "formula": parsed.get("formula", "N/A"),
                "latex": parsed.get("latex", "N/A"),
                "python_code": python_code,
                "explanation": parsed.get("explanation", "N/A"),
                # BUGFIX: was `use_specialized`, which is undefined since
                # FIX GT-LEAK-2 stopped calling _specialized_prompt(); it
                # raised NameError, which the except below swallowed, so
                # every successful local fallback came back as N/A.
                "specialized": False,
                "llm_source": "local_fallback",
                "raw_response": content,
            }

            if result["python_code"] and result["python_code"] != "N/A":
                self.formula_cache[cache_key] = result.copy()
                if self._freeze_cache_path:
                    self._save_to_frozen_cache(cache_key, result)

            if verbose:
                print(f"  [LLM] formula extracted: {result['formula'][:80]}")
            return result

        except Exception as e:
            return {
                "formula": "N/A", "latex": "N/A",
                "python_code": "N/A", "explanation": "N/A",
                "specialized": False, "raw_response": "",
                "llm_source": "local_fallback",
                "error": str(e),
            }


    def _standard_prompt(self, description, domain, variable_names, metadata):
        var_info = f"Variables (in order): {', '.join(variable_names)}" if variable_names else ""
        constants = ""
        if metadata and metadata.get("constants"):
            constants = "\nConstants:\n"
            for k, v in metadata["constants"].items():
                constants += f"  {k} = {v}\n"
        return f"""You are a mathematical formula expert in DeFi / {domain}.
Task: Derive the closed-form formula for: {description}
{var_info}
{constants}

Respond with EXACTLY these sections and no other text:

FORMULA:
[concise mathematical expression]

PYTHON:
def formula({", ".join(variable_names)}):
    import numpy as np
    # implement using np.* for array support
    return ...

EXPLANATION:
[1-2 sentences describing the formula]
"""


    def _parse_response(self, content: str) -> dict[str, str]:
        parsed = {"formula": "N/A", "latex": "N/A", "python": "N/A", "explanation": "N/A"}

        for key, tag in [("formula", "FORMULA"), ("latex", "LATEX"), ("explanation", "EXPLANATION")]:
            m = re.search(rf"{tag}:\s*\n(.*?)(?=\n[A-Z]+:|\Z)", content, re.DOTALL | re.IGNORECASE)
            if m:
                parsed[key] = m.group(1).strip()

        # Python extraction
        code = None
        m = re.search(r"PYTHON:\s*\n(.*?)(?=\n[A-Z]+:|\Z)", content, re.DOTALL | re.IGNORECASE)
        if m:
            code = m.group(1).strip()
        if not code:
            m = re.search(r"```python\s*\n(.*?)\n```", content, re.DOTALL)
            if m:
                code = m.group(1).strip()
        if not code:
            m = re.search(r"(def\s+\w+\s*\([^)]*\)\s*:(?:\n(?:[ \t]+.*))*)", content)
            if m:
                code = m.group(1).strip()
        if code:
            code = re.sub(r"^```python\s*", "", code.strip())
            code = re.sub(r"\s*```$", "", code)
            parsed["python"] = code.strip()

        return parsed

    # ------------------------------------------------------------------
    # Hybrid predict (train + evaluate on same split)
    # ------------------------------------------------------------------
    def hybrid_predict(
            self,
            description: str,
            domain: str,
            X_train: np.ndarray,
            y_train: np.ndarray,
            variable_names: list[str],
            metadata: dict,
            verbose: bool = False,
    ) -> dict:
        """
        Hybrid symbolic + neural system.

        Returns:
            llm_result
            llm_train_r2
            nn_train_r2
            decision_margin
            decision
            nn_model
            scaler_X
            scaler_y
            evaluation {r2, mse, mae}
        """

        # =====================================================
        # 1️⃣  STAGE 1 — LLM symbolic structure discovery
        # =====================================================
        llm_result = self.generate_llm_formula(
            description, domain, variable_names, metadata,
            verbose=verbose, X=X_train, y=y_train,
        )

        llm_train_r2    = 0.0
        llm_preds_train = None

        if llm_result.get("python_code") and llm_result["python_code"] != "N/A":
            llm_preds_train = _safe_exec_formula(
                llm_result["python_code"], X_train, variable_names
            )
            if llm_preds_train is not None and np.isfinite(llm_preds_train).all():
                llm_train_r2 = r2_score(y_train, llm_preds_train)
            else:
                llm_preds_train = None

        # =====================================================
        # 2️⃣  STAGE 2 — scipy nonlinear parameter fitting
        #       Parametrizes the LLM formula and fits its numeric
        #       constants to training data — works regardless of
        #       what naming convention the LLM used.
        # =====================================================
        fitted_code       = llm_result.get("python_code", "N/A")
        fitted_train_r2   = llm_train_r2
        fitted_preds_train = llm_preds_train

        if fitted_code and fitted_code != "N/A":
            fc, fr2 = fit_formula_params(
                fitted_code, X_train, y_train, variable_names, verbose=verbose
            )
            if fr2 > llm_train_r2 + 0.001:
                fitted_code        = fc
                fitted_train_r2    = fr2
                fitted_preds_train = _safe_exec_formula(fc, X_train, variable_names)
                if fitted_preds_train is None or not np.isfinite(fitted_preds_train).all():
                    fitted_preds_train = llm_preds_train
                    fitted_train_r2    = llm_train_r2
                elif verbose:
                    print(f"  [Stage2] R²: {llm_train_r2:.4f} → {fitted_train_r2:.4f}")


        # =====================================================
        # 3️⃣  NEURAL NETWORK TRAINING
        # =====================================================
        nn_model = None
        scaler_X = None
        scaler_y = None
        nn_preds_train = None
        nn_train_r2 = 0.0

        try:
            # FIX-ISSUE2B-UNSEEDED-NN: same sha256(description)-derived-seed
            # pattern used by the harness's own NN steps (see
            # HybridDeFiMethod._nn_residual_fit / HybridAllDomainsMethod in
            # run_comparative_suite_benchmark_v2.py) so this NN's weight
            # init is reproducible across separate process runs of the
            # same equation, not just within a single process.
            _nn_seed = int(hashlib.sha256(description.encode()).hexdigest(), 16) % (2**31)
            nn_model, scaler_X, scaler_y = train_nn_model(X_train, y_train, seed=_nn_seed)
            nn_preds_train = nn_predict(nn_model, scaler_X, scaler_y, X_train)

            if nn_preds_train is not None:
                nn_train_r2 = r2_score(y_train, nn_preds_train)

        except Exception as e:
            if verbose:
                print(f"[NN] Training failed: {e}")


        # =====================================================
        # 4️⃣  DECISION LOGIC
        # =====================================================
        decision_margin = fitted_train_r2 - nn_train_r2

        # Fitted symbolic formula clearly dominates
        if fitted_train_r2 >= 0.85 and decision_margin > 0.05:
            decision   = "fitted_llm"
            best_preds = fitted_preds_train

        # Both competitive — adaptive ensemble weighted by R²
        elif (
            fitted_train_r2 >= 0.5
            and nn_train_r2 >= 0.5
            and abs(decision_margin) <= 0.15
            and fitted_preds_train is not None
            and nn_preds_train is not None
        ):
            decision = "ensemble"
            total = fitted_train_r2 + nn_train_r2
            w = fitted_train_r2 / total if total > 0 else 0.6
            best_preds = w * fitted_preds_train + (1.0 - w) * nn_preds_train

        # NN fallback
        else:
            decision   = "nn"
            best_preds = nn_preds_train


        # =====================================================
        # 4️⃣  FINAL TRAIN METRICS
        # =====================================================
        # Guard: if best_preds contains non-finite values (overflow from a
        # badly-fitted formula that slipped through), fall back to NN so the
        # benchmark never receives astronomically wrong predictions.
        if best_preds is not None and not np.isfinite(best_preds).all():
            if nn_preds_train is not None and np.isfinite(nn_preds_train).all():
                best_preds = nn_preds_train
                decision   = "nn"
            else:
                best_preds = None

        if best_preds is not None:
            final_r2  = r2_score(y_train, best_preds)
            _, final_r2_status = r2_score_checked(y_train, best_preds)
            residuals = y_train - best_preds
            with np.errstate(over="ignore", invalid="ignore"):
                mse = float(np.mean(residuals ** 2))
            # L54: a non-finite MSE is a failure, never a perfect (0.0) RMSE
            rmse = float(np.sqrt(mse)) if np.isfinite(mse) else None
            mae  = float(np.mean(np.abs(residuals)))
        else:
            # L54: no predictions is a failure, not a score. None + status, never 0.0
            # (0.0 R2 / 0.0 RMSE is indistinguishable from a genuine mean-predictor fit).
            final_r2 = None
            final_r2_status = "no_predictions"
            mse  = None
            rmse = None
            mae  = None


        # =====================================================
        # 5️⃣  RETURN STRUCTURE (CRITICAL FOR EXTRAPOLATION TEST)
        # =====================================================
        return {
            "llm_result":      llm_result,
            "llm_source":      llm_result.get("llm_source", "unknown"),
            "llm_train_r2":    float(llm_train_r2),
            "fitted_train_r2": float(fitted_train_r2),
            "fitted_code":     fitted_code,
            "nn_train_r2":     float(nn_train_r2),
            "decision_margin": float(decision_margin),
            "decision":        decision,

            # Always keep NN artefacts regardless of decision.  The extrapolation
            # test (test_enhanced_defi_extrapolation.py) checks for a non-None
            # nn_model as a fallback when the symbolic formula fails on held-out
            # data.  Returning None when decision=="fitted_llm" broke that path.
            "nn_model": nn_model,
            "scaler_X": scaler_X,
            "scaler_y": scaler_y,

            "evaluation": {
                "llm_source": llm_result.get("llm_source", "unknown"),
                "r2":   (float(final_r2) if final_r2 is not None else None),
                "r2_status": final_r2_status,   # ok | degenerate_target | nonfinite_pred | ...
                "rmse": rmse,
                "mse":  mse,
                "mae":  mae,
            },
        }

    # ------------------------------------------------------------------
    # Evaluate LLM formula on arbitrary data
    # ------------------------------------------------------------------

    def evaluate_llm_formula(
        self,
        result_dict: dict,
        X: np.ndarray,
        y: np.ndarray,
        variable_names: list[str],
        verbose: bool = False,
    ) -> dict:
        """Evaluate a formula dict (with 'python_code') against data."""
        code = result_dict.get("python_code", "N/A")
        if not code or code == "N/A":
            return {"success": False, "r2": None, "error": "no python_code", "reason": "nonfinite_metric"}  # PHASE1-FIX: failure, not a score

        preds = _safe_exec_formula(code, X, variable_names)
        if preds is None or not np.isfinite(preds).all():
            return {"success": False, "r2": None, "error": "formula evaluation failed", "reason": "nonfinite_metric"}  # PHASE1-FIX: failure, not a score

        r2 = r2_score(y, preds)
        _, r2_status = r2_score_checked(y, preds)
        mse = float(np.mean((y - preds) ** 2))
        mae = float(np.mean(np.abs(y - preds)))

        if verbose:
            print(f"  [eval] R²={r2:.4f}, MSE={mse:.4e}, MAE={mae:.4e}")

        return {"success": True, "r2": r2, "r2_status": r2_status, "mse": mse, "mae": mae}


# ---------------------------------------------------------------------------
# --batch mode: run full DeFi benchmark suite and save results
# ---------------------------------------------------------------------------

def run_batch(verbose: bool = False, no_cache: bool = False):
    """Run the full DeFi benchmark suite and write hybrid_defi_<timestamp>.json."""
    protocol = DeFiExperimentProtocol()
    hybrid = EnhancedHybridSystemDeFi(no_cache=no_cache)

    domains = ["amm", "lending", "risk", "staking", "trading", "derivatives", "liquidity"]
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 72)
    print("HYBRID DEFI BENCHMARK SUITE — BATCH MODE")
    print(f"Timestamp: {timestamp}")
    print("=" * 72)

    for domain in domains:
        try:
            test_cases = protocol.load_test_data(domain, num_samples=200)
        except Exception as e:
            print(f"  [SKIP] {domain}: {e}")
            continue

        for description, X, y, var_names, metadata in test_cases:
            print(f"\n  {domain.upper()} | {description[:60]}")
            try:
                result = hybrid.hybrid_predict(
                    description, domain, X, y, var_names, metadata, verbose=verbose
                )

                entry = {
                    "domain": domain,
                    "description": description,
                    "variable_names": var_names,
                    "decision": result["decision"],
                    "llm_train_r2": result["llm_train_r2"],
                    "nn_train_r2": result["nn_train_r2"],
                    "hybrid_train_r2": result["evaluation"]["r2"],
                    "llm_formula": result["llm_result"].get("formula", "N/A"),
                    "llm_python": result["llm_result"].get("python_code", "N/A"),
                    "llm_source": result.get("llm_source", "unknown"),
                    "success": True,
                }
                print(
                    f"    decision={result['decision']}, "
                    f"LLM R²={result['llm_train_r2']:.4f}, "
                    f"NN R²={result['nn_train_r2']:.4f}, "
                    f"Hybrid R²={result['evaluation']['r2']:.4f}"
                )
            except Exception as e:
                entry = {
                    "domain": domain,
                    "description": description,
                    "success": False,
                    "error": str(e),
                }
                print(f"    ERROR: {e}")

            all_results.append(entry)

    # Save results — must land under hybrid_pysr/defi/ so the CI
    # commit-verification step (RESULT_SUBDIR=hypatiax/data/results/hybrid_pysr/defi)
    # finds the files and the downstream SEP build can locate them.
    out_dir = Path("hypatiax/data/results/hybrid_pysr/defi")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"hybrid_defi_{timestamp}.json"

    with open(out_path, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "strict_live": hybrid.strict_live,
                "no_llm_cache": no_cache,
                "total": len(all_results),
                "successful": sum(1 for r in all_results if r.get("success")),
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"\n✅ Saved {len(all_results)} results → {out_path}")

    # Summary
    successful = [r for r in all_results if r.get("success")]
    if successful:
        avg_hybrid = np.mean([r["hybrid_train_r2"] for r in successful])
        avg_llm = np.mean([r["llm_train_r2"] for r in successful])
        avg_nn = np.mean([r["nn_train_r2"] for r in successful])
        # "fitted_llm" is the primary symbolic-formula decision in hybrid_predict;
        # it must be counted alongside the original "llm" key so the summary is
        # not silently wrong and downstream analysis scripts see all decision types.
        decisions = {
            d: sum(1 for r in successful if r.get("decision") == d)
            for d in ["llm", "fitted_llm", "nn", "ensemble"]
        }
        print(f"\n📊 Summary ({len(successful)}/{len(all_results)} succeeded):")
        print(f"   Avg LLM R²:    {avg_llm:.4f}")
        print(f"   Avg NN R²:     {avg_nn:.4f}")
        print(f"   Avg Hybrid R²: {avg_hybrid:.4f}")
        print(
            f"   Decisions: LLM={decisions['llm']}, FittedLLM={decisions['fitted_llm']}, "
            f"NN={decisions['nn']}, Ensemble={decisions['ensemble']}"
        )
        print("   LLM source breakdown:")
        for src in sorted({r.get("llm_source", "unknown") for r in successful}):
            n = sum(1 for r in successful if r.get("llm_source", "unknown") == src)
            print(f"     {src}: {n}")

    return all_results


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid DeFi System")
    parser.add_argument("--batch", action="store_true", help="Run full benchmark suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-llm-cache", action="store_true",
        help="Bypass the in-memory formula cache and always call the LLM",
    )
    args = parser.parse_args()

    if args.batch:
        run_batch(verbose=args.verbose, no_cache=args.no_llm_cache)
    else:
        # Quick smoke test
        hybrid = EnhancedHybridSystemDeFi(no_cache=args.no_llm_cache)
        out = hybrid.generate_llm_formula(
            "Optimal LP position size using risk-adjusted Kelly criterion",
            "liquidity",
            ["expected_fee_apy", "il_risk"],
            metadata={"ground_truth": "min(expected_fee_apy/(2*il_risk**2),1.0)"},
            verbose=True,
        )
        print(json.dumps({k: v for k, v in out.items() if k != "raw_response"}, indent=2))
