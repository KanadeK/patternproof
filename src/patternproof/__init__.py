"""PatternProof public package."""

from patternproof.analysis import AnalysisOptions, analyze
from patternproof.loader import PatternInputError, load_pattern

__all__ = ["AnalysisOptions", "PatternInputError", "analyze", "load_pattern"]
__version__ = "0.1.0"
