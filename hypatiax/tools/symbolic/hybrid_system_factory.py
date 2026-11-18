"""Explicit version selection for HybridDiscovery implementations.

The default remains V50.2.  V60 must be selected explicitly through the
`engine.implementation` configuration key or the factory argument.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def create_hybrid_discovery_system(
    implementation: str = "v50_2", **kwargs: Any
):
    """Construct the requested HybridDiscovery implementation lazily."""
    selected = str(implementation).strip().lower()
    if selected in {"v50_2", "hybrid_system_v50_2"}:
        from hypatiax.tools.symbolic.hybrid_system_v50_2 import HybridDiscoverySystem

        return HybridDiscoverySystem(**kwargs)
    if selected in {"v60", "hybrid_system_v60"}:
        from hypatiax.tools.symbolic.hybrid_system_v60 import HybridDiscoverySystemV60

        return HybridDiscoverySystemV60(**kwargs)
    raise ValueError(
        "Unsupported HybridDiscovery implementation "
        f"{implementation!r}; expected 'v50_2' or 'v60'."
    )


def create_hybrid_discovery_system_from_config(
    config: Mapping[str, Any], **kwargs: Any
):
    """Build from a repro-style mapping; absent selector preserves V50.2."""
    engine_config = config.get("engine", {})
    if not isinstance(engine_config, Mapping):
        raise TypeError("config['engine'] must be a mapping")
    implementation = engine_config.get("implementation", "v50_2")
    return create_hybrid_discovery_system(str(implementation), **kwargs)
