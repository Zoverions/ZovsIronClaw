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
from gca_core.horizon import HorizonScanner, Outlier

class TestHorizonScanner(unittest.TestCase):
    def setUp(self):
        self.mock_glassbox = MagicMock()
        self.mock_glassbox.generate_steered.return_value = "The strange attractor is AI Singularity."

        # Mock Causal Engine
        self.mock_causal = MagicMock()
        self.mock_causal.analyze_text.return_value = {"beta_c": 0.2, "topology": "emergent"}

        # Mock QPT
        self.mock_qpt = MagicMock()
        self.mock_qpt.restructure.return_value = "[QPT STRUCTURED PROMPT]"

        self.scanner = HorizonScanner(
            self.mock_glassbox,
            causal_engine=self.mock_causal,
            qpt=self.mock_qpt,
            window_size=10,
            variance_threshold=0.1
        )

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

        # Create a scanner without mocks for simplicity in this specific test
        # (or just reuse self.scanner since update logic is mostly math)
        for i in range(15):
            val = 0.0 if i % 2 == 0 else 1.0
            state = self.scanner.update(val, "chaos context")

        self.assertTrue(state.is_critical_variance)
        self.assertGreater(state.variance, 0.1)

    def test_outlier_detection_with_causal_analysis(self):
        """Test that values far from mean are captured as outliers and analyzed for causality."""
        # Feed stable baseline with slight jitter to enable std_dev calculation
        for _ in range(20):
             self.scanner.update(0.5 + random.uniform(-0.01, 0.01), "baseline")

        # Now inject massive outlier
        # Mean ~0.5, StdDev ~0.005.
        # Value 2.0 -> Z = 1.5 / 0.005 = 300.
        state = self.scanner.update(2.0, "Black Swan Event")

        # Check if outlier count increased
        self.assertGreater(state.outliers_count, 0)

        # Check that Causal Engine was called
        self.mock_causal.analyze_text.assert_called()

        # Check that Outlier object has correct beta_c
        last_outlier = self.scanner.outliers[-1]
        self.assertEqual(last_outlier.beta_c, 0.2)
        self.assertIn("Black Swan Event", last_outlier.context)

    def test_predict_geodesic_with_qpt(self):
        """Test prediction logic uses QPT and prioritizes emergent signals."""
        # Needs 3 outliers
        # Add mixed beta_c values to test sorting

        o1 = Outlier(timestamp=0, free_energy=1.0, z_score=3.0, context="Noise", beta_c=-0.1)
        o2 = Outlier(timestamp=0, free_energy=1.0, z_score=3.0, context="Emergent Signal", beta_c=0.5)
        o3 = Outlier(timestamp=0, free_energy=1.0, z_score=3.0, context="Neutral", beta_c=0.0)

        self.scanner.outliers.append(o1)
        self.scanner.outliers.append(o2)
        self.scanner.outliers.append(o3)

        prediction = self.scanner.predict_geodesic()

        self.assertEqual(prediction, "The strange attractor is AI Singularity.")

        # Verify QPT was used
        self.mock_qpt.restructure.assert_called_once()
        args, kwargs = self.mock_qpt.restructure.call_args
        raw_prompt = kwargs['raw_prompt']

        # "Emergent Signal" (beta_c=0.5) should be first in the prompt list due to sorting
        self.assertIn("Emergent Signal", raw_prompt)

        # Verify Glassbox was called with Structured Prompt
        self.mock_glassbox.generate_steered.assert_called_with("[QPT STRUCTURED PROMPT]", max_tokens=300)

if __name__ == '__main__':
    unittest.main()
