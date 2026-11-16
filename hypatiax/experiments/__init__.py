"""
HypatiaX Core Module
====================

Core functionality for the HypatiaX NER system.
"""

__version__ = "1.0.0"
__author__ = "HypatiaX Team"

from .evaluation import add_noise_matched_extrapolation

__all__ = ["add_noise_matched_extrapolation"]

# Optional module
try:
    from . import preprocessing
    __all__.append("preprocessing")
except ImportError:
    preprocessing = None

