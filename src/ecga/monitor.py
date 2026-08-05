"""
Active-Stream Lyapunov (ASL) Monitor.

Paper Section 5.6:
  Monitors local divergence rate of live keystream bytes during continuous audio streaming.
  If the local divergence rate falls near zero (threshold epsilon <= 0.05),
  triggers a re-keying signal to prevent orbit collapse or periodic decay.
"""

import math
from typing import List, Tuple


class ActiveStreamLyapunovMonitor:
    """Active-Stream Lyapunov Monitor for continuous audio stream key health."""

    def __init__(self, window_size: int = 128, threshold_epsilon: float = 0.05) -> None:
        self.window_size = window_size
        self.threshold_epsilon = threshold_epsilon

    def estimate_local_divergence(self, keystream_bytes: bytes) -> float:
        """
        Estimate local divergence rate (local Lyapunov exponent) from recent keystream bytes.

        Uses difference-based phase space reconstruction divergence:
        lambda_local = mean(ln(|K_{i+1} - K_i| + 1.0)) / dt.
        """
        if len(keystream_bytes) < 2:
            return 1.0  # Default safe initial value

        data = list(keystream_bytes[-self.window_size :])
        diffs = [abs(data[i + 1] - data[i]) for i in range(len(data) - 1)]

        if not diffs:
            return 1.0

        # Mean logarithmic rate of absolute consecutive byte differences
        log_diffs = [math.log(d + 1.0) for d in diffs]
        mean_divergence = sum(log_diffs) / len(log_diffs)

        return mean_divergence

    def should_rekey(self, keystream_bytes: bytes) -> Tuple[bool, float]:
        """
        Check if current keystream window indicates orbit collapse.

        Returns:
            Tuple of (rekey_recommended_boolean, local_divergence_estimate).
        """
        div = self.estimate_local_divergence(keystream_bytes)
        rekey_needed = div < self.threshold_epsilon
        return rekey_needed, div
