"""Versioned JSON-safe result records for uncertainty experiments."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Mapping
import numpy as np

RESULT_SCHEMA_VERSION = "1.0"


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [json_safe(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


@dataclass
class UncertaintyResult:
    """One method × evaluation-slice × optional coverage record."""
    method: str
    evaluation_domain: str
    n_evaluated: int
    nominal_coverage: float | None = None
    equation: str | None = None
    dataset: str | None = None
    strategy: str | None = None
    direction: str | None = None
    distance: float | None = None
    point_metrics: Mapping[str, Any] = field(default_factory=dict)
    interval_metrics: Mapping[str, Any] = field(default_factory=dict)
    uncertainty_summary: Mapping[str, Any] = field(default_factory=dict)
    calibration: Mapping[str, Any] = field(default_factory=dict)
    shift_diagnostics: Mapping[str, Any] = field(default_factory=dict)
    status: str = "ok"
    reason: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["schema_version"] = RESULT_SCHEMA_VERSION
        payload["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
        return json_safe(payload)


def write_uncertainty_results_json(records, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": RESULT_SCHEMA_VERSION, "records": [
        item.to_dict() if isinstance(item, UncertaintyResult) else json_safe(item) for item in records
    ]}
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
