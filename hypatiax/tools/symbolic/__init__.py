"""Public, lazy exports for HypatiaX symbolic-regression tools."""

from importlib import import_module

__all__ = [
    "PhysicsAwareRegressor",
    "SymbolicEngine",
    "SymbolicEngineWithLLM",
    "DiscoveryConfig",
    "LLMConfig",
]


def __getattr__(name: str):
    """Load symbolic implementations only when their public names are requested."""
    if name == "PhysicsAwareRegressor":
        module = import_module(".physics_aware_regressor", __name__)
    elif name in {
        "SymbolicEngine",
        "SymbolicEngineWithLLM",
        "DiscoveryConfig",
        "LLMConfig",
    }:
        module = import_module(".symbolic_engine", __name__)
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
