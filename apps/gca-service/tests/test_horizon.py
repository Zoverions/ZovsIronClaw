import unittest
from unittest.mock import MagicMock
import sys
import os
import random

# Mock heavy dependencies BEFORE import
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()

import numpy as np

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import HorizonScanner directly to avoid loading gca_core.__init__
# If that fails due to package structure, we rely on the mocks above.
from gca_core.horizon import HorizonScanner

class TestHorizonScanner(unittest.TestCase):
    def setUp(self):
        self.mock_glassbox = MagicMock()
        self.mock_glassbox.generate_steered.return_value = "The strange attractor is AI Singularity."
        self.scanner = HorizonScanner(self.mock_glassbox, window_size=10, variance_threshold=0.1)

    def test_update_stable_variance(self):
        """Test that stable input results in low variance and no alarm."""
        # Feed stable values (mean=0.5, var~0)
        for _ in range(15):
            state = self.scanner.update(0.5, "stable context")

        self.assertFalse(state.is_critical_variance)
        self.assertAlmostEqual(state.variance, 0.0, places=2)

    def test_update_critical_variance(self):
        """Test that oscillating input triggers variance alarm."""
        # Feed oscillating values: 0.0, 1.0, 0.0, 1.0...
        # Mean = 0.5. Diff = 0.5. Variance = 0.25 > 0.1

        self.scanner = HorizonScanner(self.mock_glassbox, window_size=10, variance_threshold=0.1)
        for i in range(15):
            val = 0.0 if i % 2 == 0 else 1.0
            state = self.scanner.update(val, "chaos context")

        self.assertTrue(state.is_critical_variance)
        self.assertGreater(state.variance, 0.1)

    def test_outlier_detection(self):
        """Test that values far from mean are captured as outliers."""
        # Feed stable baseline with slight jitter to enable std_dev calculation
        for _ in range(20):
             self.scanner.update(0.5 + random.uniform(-0.01, 0.01), "baseline")

        # Now inject massive outlier
        # Mean ~0.5, StdDev ~0.005.
        # Value 2.0 -> Z = 1.5 / 0.005 = 300.
        state = self.scanner.update(2.0, "Black Swan Event")

        # Check if outlier count increased
        self.assertGreater(state.outliers_count, 0)
        self.assertIn("Black Swan Event", self.scanner.outliers[-1])

    def test_predict_geodesic(self):
        """Test prediction logic."""
        # Needs 3 outliers
        self.scanner.outliers.append("Outlier 1")
        self.scanner.outliers.append("Outlier 2")
        self.scanner.outliers.append("Outlier 3")

        prediction = self.scanner.predict_geodesic()

        self.assertEqual(prediction, "The strange attractor is AI Singularity.")
        self.mock_glassbox.generate_steered.assert_called_once()
        args, kwargs = self.mock_glassbox.generate_steered.call_args
        self.assertIn("SYSTEM: Horizon Scanning Protocol Initiated", args[0])

if __name__ == '__main__':
    unittest.main()
