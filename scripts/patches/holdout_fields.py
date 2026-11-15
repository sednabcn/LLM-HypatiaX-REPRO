#!/usr/bin/env python3
"""L06: add held-out R2 fields to hybrid_predict (option 2). Dry run by default;
--apply writes. Every edit must match exactly once or nothing is written."""
import argparse, difflib, sys
from pathlib import Path

T = Path("hypatiax/core/generation/hybrid_all_domains_llm_nn/"
         "hybrid_system_llm_nn_all_domains.py")
EDITS = []

METHOD = '''    def _holdout_scores(self, description, X, y_true, var_names, llm_result, llm_ok):
        # L06: held-out R2 on a third split. Trains a SECOND NN on the train
        # rows only; held-out rows never reach training or early stopping.
        from sklearn.model_selection import train_test_split as _tts

        _seed = int(hashlib.sha256(("holdout:" + description).encode()).hexdigest(), 16) % (2**31)
        _tr, _te = _tts(np.arange(len(X)), test_size=0.2, random_state=_seed)
        out = {"holdout_n_test": int(len(_te)), "holdout_seed": _seed}
        if len(_tr) < 10 or len(_te) < 2:
            out["holdout_status"] = "too_small"
            return out
        _attrs = ("_last_nn_scaler_X", "_last_nn_scaler_y", "_last_nn_use_logy")
        _saved = {a: getattr(self, a, None) for a in _attrs}

        def _r2(yt, yp):
            v = _r2_rule_a(yt, yp)[0]
            return float(v) if v is not None and np.isfinite(v) else None

        try:
            llm_te = self._get_llm_predictions(llm_result, X[_te], var_names) if llm_ok else None
            llm_tr = self._get_llm_predictions(llm_result, X[_tr], var_names) if llm_ok else None
            model, _m = self.train_nn(X[_tr], y_true[_tr], epochs=1000, seed=_seed)
            nn_te = self._get_nn_predictions(model, X[_te])
            nn_tr = self._get_nn_predictions(model, X[_tr])
            out["r2_holdout_llm"] = _r2(y_true[_te], llm_te) if llm_te is not None else None
            out["r2_holdout_nn"] = _r2(y_true[_te], nn_te) if nn_te is not None else None
            out["r2_holdout_blend"] = None
            if all(p is not None for p in (llm_te, llm_tr, nn_te, nn_tr)):
                w_llm = max(_r2(y_true[_tr], llm_tr) or 0.0, 0.0)
                w_nn = max(_r2(y_true[_tr], nn_tr) or 0.0, 0.0)
                tot = w_llm + w_nn if (w_llm + w_nn) > 0 else 1.0
                out["r2_holdout_blend"] = _r2(y_true[_te], (w_llm * llm_te + w_nn * nn_te) / tot)
            out["holdout_status"] = "ok"
        except Exception as e:
            out["holdout_status"] = "error: %s: %s" % (type(e).__name__, str(e)[:80])
        finally:
            for a, v in _saved.items():
                setattr(self, a, v)
        return out

'''

EDITS.append(("insert _holdout_scores before hybrid_predict",
    "    def hybrid_predict(\n",
    METHOD + "    def hybrid_predict(\n"))

EDITS.append(("call it before the result is built",
    "        # Build result with observations\n",
    '''        _holdout = {}
        if os.environ.get("HYPATIAX_HOLDOUT") == "1":
            _holdout = self._holdout_scores(
                description, X, y_true, var_names, llm_result, llm_ok
            )

        # Build result with observations
'''))

EDITS.append(("add fields to the normal evaluation dict",
    '''                "rmse": float(final_rmse),
                "success": decision != "fail",
            },
''',
    '''                "rmse": float(final_rmse),
                "success": decision != "fail",
                "r2_in_sample": float(final_r2),
                **_holdout,
            },
'''))

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
args = ap.parse_args()
src = T.read_text(encoding="utf-8")
new, bad = src, False
for name, old, repl in EDITS:
    n = new.count(old)
    print("[%s] %s: %d match(es)" % ("ok" if n == 1 else "FAIL", name, n))
    if n != 1:
        bad = True
        continue
    new = new.replace(old, repl)
if bad:
    print("Refusing to write: every edit must match exactly once.")
    sys.exit(2)
sys.stdout.writelines(difflib.unified_diff(
    src.splitlines(True), new.splitlines(True), "a/" + str(T), "b/" + str(T)))
if args.apply:
    T.write_text(new, encoding="utf-8")
    print("applied")
else:
    print("dry run; pass --apply to write")
