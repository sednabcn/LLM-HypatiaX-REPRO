import numpy as np
from hypatiax.core.r2_canonical import r2_checked

def recovery_r2(y_true, y_pred):
    """Canonical R2 as a plain float; NaN when undefined (rule A)."""
    v, status = r2_checked(np.asarray(y_true, float), np.asarray(y_pred, float))
    return float(v) if status == "ok" and v is not None and np.isfinite(v) else float("nan")
