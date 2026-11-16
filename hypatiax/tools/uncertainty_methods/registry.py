"""Explicit factory registries for uncertainty estimators and calibrators."""
class MethodRegistry:
    def __init__(self, kind: str):
        self.kind = str(kind)
        self._factories = {}

    def register(self, name: str, factory=None):
        key = str(name).strip().lower()
        if not key:
            raise ValueError("Registry names must be non-empty.")
        def add(candidate):
            if not callable(candidate):
                raise TypeError("Registered factory must be callable.")
            if key in self._factories:
                raise KeyError(f"{self.kind} method already registered: {key}")
            self._factories[key] = candidate
            return candidate
        return add if factory is None else add(factory)

    def create(self, name: str, **kwargs):
        key = str(name).strip().lower()
        if key not in self._factories:
            raise KeyError(f"Unknown {self.kind} method {key!r}; available: {', '.join(self.names()) or '(none)'}")
        return self._factories[key](**kwargs)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


UNCERTAINTY_METHODS = MethodRegistry("uncertainty")
CALIBRATION_METHODS = MethodRegistry("calibration")
