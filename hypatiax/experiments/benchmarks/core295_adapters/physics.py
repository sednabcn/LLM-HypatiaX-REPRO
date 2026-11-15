"""Physics adapter for the Core-295 scalar-expression benchmark contract."""
from .common import run_equation as _run

def run_equation(*, entry, context):
    return _run(entry=entry, context=context, domain="Physics")
