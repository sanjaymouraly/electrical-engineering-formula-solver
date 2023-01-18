"""Centralised exception types for the toolkit."""

from __future__ import annotations


class EEError(ValueError):
    """Base error for all toolkit validation/calculation failures."""


class InvalidInputError(EEError):
    """Raised when an input is outside its physically valid domain."""


class InsufficientInputError(EEError):
    """Raised when too few independent inputs are supplied to solve a problem."""


class IncompatibleUnitError(EEError):
    """Raised when a unit conversion is dimensionally impossible."""


class PhysicalImpossibilityError(EEError):
    """Raised when inputs contradict physics (e.g. efficiency > 100%)."""
