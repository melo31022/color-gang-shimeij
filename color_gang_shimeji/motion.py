"""Small, independently testable helpers for pet movement."""
import random


def clamp(value: float, minimum: float, maximum: float) -> float:
    if minimum > maximum:
        raise ValueError("minimum cannot be greater than maximum")
    return max(minimum, min(maximum, value))


def choose_direction(rng=random) -> int:
    """Return -1 (left) or 1 (right)."""
    return rng.choice((-1, 1))
