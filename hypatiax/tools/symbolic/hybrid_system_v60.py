"""Opt-in HybridDiscovery V60 migration boundary.

V60 is intentionally introduced as a separate class.  This first increment
is a compatibility adapter over the proven V50.2 implementation; it does not
claim that the native V60 staged discovery pipeline is complete.  Keeping the
adapter explicit lets callers select V60 without changing historical V50.2
behavior while subsequent PRs replace individual stages behind this API.
"""

from __future__ import annotations

from typing import Any

from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem


class HybridDiscoverySystemV60(HybridDiscoverySystem):
    """Versioned V60 entry point with an explicit V50.2 compatibility bridge.

    All constructor arguments and discovery semantics remain backward
    compatible with :class:`HybridDiscoverySystem`.  Result provenance makes
    the current implementation boundary machine-readable; consumers must not
    interpret this adapter as evidence that native V60 stages are active.
    """

    VERSION = "6.0.0"
    IMPLEMENTATION_MODE = "v50_2_compatibility_adapter"

    def _annotate_v60_result(self, result: Any) -> Any:
        if not isinstance(result, dict):
            return result
        annotated = dict(result)
        provenance = annotated.get("implementation_provenance")
        provenance = dict(provenance) if isinstance(provenance, dict) else {}
        provenance.update(
            {
                "engine_family": "hybrid_discovery",
                "engine_version": self.VERSION,
                "implementation_mode": self.IMPLEMENTATION_MODE,
                "native_v60_pipeline": False,
                "compatibility_baseline": "hybrid_system_v50_2",
            }
        )
        annotated["implementation_provenance"] = provenance
        return annotated

    def discover(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Run the compatibility implementation and label its provenance."""
        return self._annotate_v60_result(super().discover(*args, **kwargs))

    def discover_validate_interpret(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Preserve the legacy entry point while exposing V60 adapter provenance."""
        return self._annotate_v60_result(
            super().discover_validate_interpret(*args, **kwargs)
        )
