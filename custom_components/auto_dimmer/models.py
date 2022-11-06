"""The auto_dimmer integration models."""
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class AutoDimmerData:
    """Data for the auto_dimmer integration."""

    lights: dict[str, int]
