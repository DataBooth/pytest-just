"""Custom exception types used by pytest-just."""

from __future__ import annotations


class JustfileError(Exception):
    """Base exception for pytest-just failures."""


class JustCommandError(JustfileError, RuntimeError):
    """Raised when invoking `just` fails."""


class JustJsonFormatError(JustfileError, RuntimeError):
    """Raised when `just --dump` JSON is malformed or incompatible."""


class UnknownRecipeError(JustfileError, ValueError):
    """Raised when a requested recipe does not exist."""
