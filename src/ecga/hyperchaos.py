"""
Layer 2: 4D Hyperchaotic Keystream Generator.

Paper Section 3.4 & Section 5.2 (Eq. 4 & Eq. 8):
  System equations (Eq. 4):
    dx/dt = a*(y - x) + w
    dy/dt = c*x - x*z - y
    dz/dt = x*y - b*z
    dw/dt = -d*x + e*w

  Integration: RK4 with step size h = 0.01.
  Warm-up: 1000 steps discarded.
  State reduction: fmod(xi, 1000) applied after every step.
  Keystream byte (Eq. 8):
    KSi = floor((|xi| - floor(|xi|)) * 2^32) mod 256,
    cycling through state variables (x, y, z, w) in turn.

Default certified parameters theta* = (30.175, 3.585, 29.642, 6.168, 0.622).
"""

import math
import struct
from typing import List, Tuple

# Certified hyperchaotic parameter vector theta* (Section 8.3 Table 7)
CERTIFIED_THETA = (30.175, 3.585, 29.642, 6.168, 0.622)


def hyperchaotic_system_derivatives(
    state: Tuple[float, float, float, float], theta: Tuple[float, float, float, float, float]
) -> Tuple[float, float, float, float]:
    """Compute derivatives (dx/dt, dy/dt, dz/dt, dw/dt) according to Eq. 4."""
    x, y, z, w = state
    a, b, c, d, e = theta

    dxdt = a * (y - x) + w
    dydt = c * x - x * z - y
    dzdt = x * y - b * z
    dwdt = -d * x + e * w
    return (dxdt, dydt, dzdt, dwdt)


def rk4_step(
    state: Tuple[float, float, float, float],
    theta: Tuple[float, float, float, float, float],
    h: float = 0.01,
) -> Tuple[float, float, float, float]:
    """
    Perform one 4th-order Runge-Kutta integration step with state reduction fmod 1000.
    """
    k1 = hyperchaotic_system_derivatives(state, theta)

    state_k2 = tuple(s + 0.5 * h * k for s, k in zip(state, k1))
    k2 = hyperchaotic_system_derivatives(state_k2, theta)

    state_k3 = tuple(s + 0.5 * h * k for s, k in zip(state, k2))
    k3 = hyperchaotic_system_derivatives(state_k3, theta)

    state_k4 = tuple(s + h * k for s, k in zip(state, k3))
    k4 = hyperchaotic_system_derivatives(state_k4, theta)

    new_state = []
    for s, k1_i, k2_i, k3_i, k4_i in zip(state, k1, k2, k3, k4):
        val = s + (h / 6.0) * (k1_i + 2.0 * k2_i + 2.0 * k3_i + k4_i)
        # Apply fmod 1000 state reduction to keep state bounded
        val = math.fmod(val, 1000.0)
        new_state.append(val)

    return (new_state[0], new_state[1], new_state[2], new_state[3])


def derive_initial_state_from_key(ks: bytes) -> Tuple[float, float, float, float]:
    """Derive non-zero initial state (x0, y0, z0, w0) from 32-byte session key Ks."""
    if len(ks) < 32:
        raise ValueError("Session key Ks must be 32 bytes")

    # Split 32 bytes into 4 8-byte unsigned integers
    u64s = struct.unpack(">4Q", ks[:32])
    # Map uint64 to float in range [1.0, 100.0]
    initial_state = []
    for u in u64s:
        val = 1.0 + (u % 990000) / 10000.0
        initial_state.append(val)
    return (initial_state[0], initial_state[1], initial_state[2], initial_state[3])


class HyperchaoticGenerator:
    """4D Hyperchaotic Keystream Generator with RK4 integration and fmod 1000 reduction."""

    def __init__(
        self,
        theta: Tuple[float, float, float, float, float] = CERTIFIED_THETA,
        h: float = 0.01,
        warmup_steps: int = 1000,
    ) -> None:
        self.theta = theta
        self.h = h
        self.warmup_steps = warmup_steps

    def generate_keystream(
        self, length: int, ks: bytes, initial_state: Tuple[float, float, float, float] = None
    ) -> bytes:
        """
        Generate `length` keystream bytes (Eq. 8) starting from initial state derived from Ks.

        Args:
            length: Number of bytes to generate (L = 2N).
            ks: 32-byte session key.
            initial_state: Optional explicit initial state (x0, y0, z0, w0).

        Returns:
            bytes object of length L containing pseudo-random keystream bytes.
        """
        if initial_state is None:
            state = derive_initial_state_from_key(ks)
        else:
            state = initial_state

        # Warm-up phase: discard first warmup_steps steps
        for _ in range(self.warmup_steps):
            state = rk4_step(state, self.theta, self.h)

        keystream_bytes = bytearray()
        var_idx = 0  # Cycle through 0=x, 1=y, 2=z, 3=w

        while len(keystream_bytes) < length:
            state = rk4_step(state, self.theta, self.h)
            xi = state[var_idx]
            var_idx = (var_idx + 1) % 4

            # Eq. 8: KSi = floor((|xi| - floor(|xi|)) * 2^32) mod 256
            abs_xi = abs(xi)
            frac_part = abs_xi - math.floor(abs_xi)
            scaled = math.floor(frac_part * (2**32))
            byte_val = scaled % 256
            keystream_bytes.append(byte_val)

        return bytes(keystream_bytes)
