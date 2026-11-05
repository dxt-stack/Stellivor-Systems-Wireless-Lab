import math
import unittest

from stellivor.core import Status
from stellivor.sdr import analyze_samples, generate_iq_tone, rms_amplitude, simulate_tone


class SDRTests(unittest.TestCase):
    def test_noiseless_tone_hits_exact_bin(self):
        result = simulate_tone(1000, 8000, 256)
        self.assertEqual(result.status, Status.SIMULATION)
        self.assertAlmostEqual(result.data["estimated_frequency_hz"], 1000)
        self.assertAlmostEqual(result.data["frequency_bin_hz"], 31.25)
        self.assertAlmostEqual(result.data["normalized_frequency_cycles_per_sample"], 0.125)
        self.assertAlmostEqual(result.data["rms_amplitude"], 1.0)
        self.assertFalse(result.data["live_rf_capture"])

    def test_negative_tone(self):
        samples = generate_iq_tone(-1000, 8000, 256)
        analysis = analyze_samples(samples, 8000)
        self.assertAlmostEqual(analysis["estimated_frequency_hz"], -1000)

    def test_non_power_of_two_is_explicitly_truncated(self):
        samples = generate_iq_tone(1000, 8000, 300)
        analysis = analyze_samples(samples, 8000)
        self.assertEqual(analysis["analyzed_sample_count"], 256)
        self.assertTrue(analysis["analysis_truncated"])

    def test_noise_is_reproducible(self):
        first = generate_iq_tone(100, 8000, 64, noise_stddev=0.1, seed=42)
        second = generate_iq_tone(100, 8000, 64, noise_stddev=0.1, seed=42)
        third = generate_iq_tone(100, 8000, 64, noise_stddev=0.1, seed=43)
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_rms(self):
        self.assertEqual(rms_amplitude([3 + 4j]), 5.0)
        self.assertAlmostEqual(rms_amplitude([1 + 0j, -1 + 0j]), 1.0)

    def test_analysis_rejects_nonfinite_and_nonnumeric_samples(self):
        for samples in ([complex(float("nan"), 0)], ["not IQ"]):
            with self.subTest(samples=samples):
                with self.assertRaises(ValueError):
                    analyze_samples(samples, 8000)

    def test_invalid_parameters(self):
        invalid_calls = [
            lambda: generate_iq_tone(100, 0, 64),
            lambda: generate_iq_tone(5000, 8000, 64),
            lambda: generate_iq_tone(100, 8000, 1),
            lambda: generate_iq_tone(float("nan"), 8000, 64),
            lambda: generate_iq_tone(100, 8000, 64, noise_stddev=-1),
            lambda: generate_iq_tone(100, 8000, 64, amplitude=-1),
        ]
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()

    def test_invalid_simulation_returns_failure_not_simulation_success(self):
        result = simulate_tone(9000, 8000, 64)
        self.assertEqual(result.status, Status.FAILURE)
        self.assertTrue(result.data["simulated"])

    def test_fft_limit_must_be_power_of_two(self):
        with self.assertRaises(ValueError):
            analyze_samples([1 + 0j, 2 + 0j], 8000, max_fft_size=1000)


if __name__ == "__main__":
    unittest.main()
