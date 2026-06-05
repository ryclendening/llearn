"""Compatibility facade for worked-example operations."""

from examples.extraction import extract_example_problems
from examples.grading import grade_example_attempt

__all__ = ["extract_example_problems", "grade_example_attempt"]
