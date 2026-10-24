# usage: source env_repro.sh   (from the repo root)
unset HYPATIAX_ROOT HYPATIAX_DATA_DIR HYPATIAX_OUTPUT_DIR
export PYTHONPATH="$PWD"
export HYPATIAX_DISABLE_HARDCODED=1 HYPATIAX_DISABLE_PROMPT_HINTS=1 HYPATIAX_R2_SIGN_FLIP=0 HYPATIAX_STRICT=1
_repo="$PWD"
( cd /tmp && REPO="$_repo" python - <<'PY'
import os, pathlib, sys, hypatiax
f, root = pathlib.Path(hypatiax.__file__).resolve(), pathlib.Path(os.environ["REPO"]).resolve()
if root not in f.parents:
    sys.exit(f"PREFLIGHT FAILED: hypatiax resolves to {f}, not under {root}")
print("preflight ok:", f)
PY
) || return 1
