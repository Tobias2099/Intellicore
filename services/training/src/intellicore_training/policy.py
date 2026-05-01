from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrefetchDecision:
    address: int | None
    confidence: float


class StridePrefetchPolicy:
    """Simple baseline policy used until learned agents are integrated."""

    def __init__(self, block_size: int = 64) -> None:
        self.block_size = block_size

    def predict_next(self, current_address: int, previous_address: int | None) -> PrefetchDecision:
        if previous_address is None:
            return PrefetchDecision(address=current_address + self.block_size, confidence=0.25)

        stride = current_address - previous_address
        return PrefetchDecision(address=current_address + stride, confidence=0.6)
