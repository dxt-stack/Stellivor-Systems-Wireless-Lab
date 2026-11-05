"""Deterministic synthetic complex-IQ generation and spectrum analysis.

No function in this module accesses a receiver or claims live RF reception.
"""

from __future__ import annotations

import math
import random
from typing import Any, Sequence

from .core import Result, Status

MAX_SAMPLES = 65536


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _sample_count(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 2 <= value <= MAX_SAMPLES:
        raise ValueError(f"Sample count must be an integer between 2 and {MAX_SAMPLES}.")
    return value


def generate_iq_tone(
    frequency_hz: float,
    sample_rate_hz: float,
    sample_count: int,
    *,
    amplitude: float = 1.0,
    noise_stddev: float = 0.0,
    seed: int = 0,
    phase_radians: float = 0.0,
) -> list[complex]:
    frequency = _finite_number(frequency_hz, "Frequency")
    sample_rate = _finite_number(sample_rate_hz, "Sample rate")
    amplitude = _finite_number(amplitude, "Amplitude")
    noise = _finite_number(noise_stddev, "Noise standard deviation")
    phase = _finite_number(phase_radians, "Phase")
    count = _sample_count(sample_count)
    if sample_rate <= 0:
        raise ValueError("Sample rate must be greater than zero.")
    if abs(frequency) > sample_rate / 2:
        raise ValueError("Frequency must be between -Nyquist and +Nyquist (-sample_rate/2 to +sample_rate/2).")
    if not 0 <= amplitude <= 100:
        raise ValueError("Amplitude must be between 0 and 100.")
    if not 0 <= noise <= 100:
        raise ValueError("Noise standard deviation must be between 0 and 100.")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("Noise seed must be an integer.")

    rng = random.Random(seed)
    step = 2.0 * math.pi * frequency / sample_rate
    samples: list[complex] = []
    for index in range(count):
        value = amplitude * complex(math.cos(phase + step * index), math.sin(phase + step * index))
        if noise:
            value += complex(rng.gauss(0.0, noise), rng.gauss(0.0, noise))
        samples.append(value)
    return samples


def _validate_iq_samples(samples: Sequence[complex]) -> None:
    for index, sample in enumerate(samples):
        if isinstance(sample, bool) or not isinstance(sample, (int, float, complex)):
            raise ValueError(f"IQ sample {index} must be a real or complex number.")
        try:
            real = float(sample.real if isinstance(sample, complex) else sample)
            imag = float(sample.imag if isinstance(sample, complex) else 0.0)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError(f"IQ sample {index} is outside the supported numeric range.") from exc
        if not math.isfinite(real) or not math.isfinite(imag):
            raise ValueError(f"IQ sample {index} must have finite real and imaginary parts.")
        if not math.isfinite(real * real + imag * imag):
            raise ValueError(f"IQ sample {index} magnitude is too large for stable analysis.")


def rms_amplitude(samples: Sequence[complex]) -> float:
    if not samples:
        raise ValueError("At least one IQ sample is required.")
    if len(samples) > MAX_SAMPLES:
        raise ValueError(f"No more than {MAX_SAMPLES} samples may be analyzed.")
    _validate_iq_samples(samples)
    return math.sqrt(math.fsum(abs(sample) ** 2 for sample in samples) / len(samples))


def _fft(samples: Sequence[complex]) -> list[complex]:
    """Iterative radix-2 FFT; the caller selects a power-of-two input size."""
    output = list(samples)
    count = len(output)
    if count < 1 or count & (count - 1):
        raise ValueError("FFT input length must be a nonzero power of two.")
    target = 0
    for index in range(1, count):
        bit = count >> 1
        while target & bit:
            target ^= bit
            bit >>= 1
        target ^= bit
        if index < target:
            output[index], output[target] = output[target], output[index]
    length = 2
    while length <= count:
        root = complex(math.cos(-2.0 * math.pi / length), math.sin(-2.0 * math.pi / length))
        half = length // 2
        for start in range(0, count, length):
            factor = 1.0 + 0.0j
            for offset in range(half):
                even = output[start + offset]
                odd = factor * output[start + offset + half]
                output[start + offset] = even + odd
                output[start + offset + half] = even - odd
                factor *= root
        length <<= 1
    return output


def analyze_samples(samples: Sequence[complex], sample_rate_hz: float, *, max_fft_size: int = 4096) -> dict[str, Any]:
    sample_rate = _finite_number(sample_rate_hz, "Sample rate")
    if sample_rate <= 0:
        raise ValueError("Sample rate must be greater than zero.")
    if not samples:
        raise ValueError("At least one IQ sample is required.")
    if len(samples) > MAX_SAMPLES:
        raise ValueError(f"No more than {MAX_SAMPLES} samples may be analyzed.")
    if isinstance(max_fft_size, bool) or not isinstance(max_fft_size, int) or not 2 <= max_fft_size <= MAX_SAMPLES:
        raise ValueError(f"FFT limit must be between 2 and {MAX_SAMPLES}.")
    if max_fft_size & (max_fft_size - 1):
        raise ValueError("FFT limit must be a power of two.")
    rms = rms_amplitude(samples)

    fft_size = 1 << (min(len(samples), max_fft_size).bit_length() - 1)
    transformed = _fft(samples[:fft_size])
    magnitudes = [abs(value) / fft_size for value in transformed]
    peak_bin = max(range(fft_size), key=magnitudes.__getitem__)
    signed_bin = peak_bin if peak_bin <= fft_size // 2 else peak_bin - fft_size
    estimated_frequency = signed_bin * sample_rate / fft_size

    positive: list[dict[str, Any]] = []
    for index in range(fft_size // 2 + 1):
        scale = 1.0 if index == 0 or (fft_size > 1 and index == fft_size // 2) else 2.0
        positive.append({
            "bin": index,
            "frequency_hz": index * sample_rate / fft_size,
            "magnitude": magnitudes[index] * scale,
        })
    peaks = sorted(positive, key=lambda item: item["magnitude"], reverse=True)[:8]
    return {
        "input_sample_count": len(samples),
        "analyzed_sample_count": fft_size,
        "analysis_truncated": fft_size < len(samples),
        "sample_rate_hz": sample_rate,
        "frequency_bin_hz": sample_rate / fft_size,
        "peak_bin": peak_bin,
        "signed_peak_bin": signed_bin,
        "estimated_frequency_hz": estimated_frequency,
        "normalized_frequency_cycles_per_sample": estimated_frequency / sample_rate,
        "rms_amplitude": rms,
        "positive_spectrum": positive,
        "strongest_positive_bins": peaks,
        "note": "The estimate is the strongest FFT bin, not an exact frequency estimator. Non-power-of-two input is truncated to a power of two.",
    }


def simulate_tone(
    frequency_hz: float = 1000.0,
    sample_rate_hz: float = 48000.0,
    sample_count: int = 1024,
    *,
    amplitude: float = 1.0,
    noise_stddev: float = 0.0,
    seed: int = 0,
) -> Result:
    try:
        samples = generate_iq_tone(
            frequency_hz,
            sample_rate_hz,
            sample_count,
            amplitude=amplitude,
            noise_stddev=noise_stddev,
            seed=seed,
        )
        analysis = analyze_samples(samples, sample_rate_hz)
    except ValueError as exc:
        return Result("sdr", "synthetic_tone", Status.FAILURE, "Invalid SDR simulation parameters.", errors=[str(exc)], data={"simulated": True, "live_rf_capture": False})

    return Result(
        "sdr",
        "synthetic_tone",
        Status.SIMULATION,
        "Generated and analyzed a synthetic complex-IQ tone; no RF hardware was used.",
        data={
            "simulated": True,
            "live_rf_capture": False,
            "source": "deterministic mathematical tone generator",
            "frequency_hz": float(frequency_hz),
            "sample_rate_hz": float(sample_rate_hz),
            "sample_count": sample_count,
            "amplitude": float(amplitude),
            "noise_stddev": float(noise_stddev),
            "noise_seed": seed,
            **analysis,
        },
        warnings=["This is educational simulated data, not a radio signal observed from the environment."],
    )
