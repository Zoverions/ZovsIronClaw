import unittest
from unittest.mock import MagicMock
import sys
import os

# Mock dependencies before import
torch_mock = MagicMock()
torch_mock.nn = MagicMock()
torch_mock.nn.functional = MagicMock()
sys.modules["torch"] = torch_mock
sys.modules["torch.nn"] = torch_mock.nn
sys.modules["torch.nn.functional"] = torch_mock.nn.functional
sys.modules["transformers"] = MagicMock()
sys.modules["textblob"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()
sys.modules["scipy.spatial.distance"] = MagicMock()

# Add apps/gca-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from gca_core.dual_ethics import DualEthicalSystem
except ImportError:
    # Fallback for when running directly
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from gca_core.dual_ethics import DualEthicalSystem

class TestDualEthicalSystem(unittest.TestCase):
    def setUp(self):
        self.glassbox = MagicMock()
        self.pulse = MagicMock()
        self.system = DualEthicalSystem(self.glassbox, self.pulse)

    def test_agreement_safe(self):
        # Mock GlassBox response for probabilistic check
        # generate_steered returns a string response
        self.glassbox.generate_steered.return_value = "0.1"

        # Test with low geometric entropy (Safe)
        is_safe, divergence, reason = self.system.verify_intent("Hello world", geometric_entropy=0.1)

        self.assertTrue(is_safe, f"Should be safe. Reason: {reason}")
        self.assertLess(divergence, 0.5)
        self.assertEqual(reason, "Verified")

    def test_agreement_unsafe(self):
        # Mock GlassBox response for probabilistic check (Unsafe)
        self.glassbox.generate_steered.return_value = "0.9"

        # Test with high geometric entropy (Unsafe)
        is_safe, divergence, reason = self.system.verify_intent("Destroy humanity", geometric_entropy=0.9)

        self.assertFalse(is_safe, "Should be unsafe because both agree it's unsafe")
        self.assertIn("Both systems agree", reason)

    def test_divergence_misdirection(self):
        # Mock GlassBox response for probabilistic check (Unsafe)
        self.glassbox.generate_steered.return_value = "0.9"

        # Test with low geometric entropy (Safe - Misdirection!)
        is_safe, divergence, reason = self.system.verify_intent("Subtle manipulation", geometric_entropy=0.1)

        self.assertFalse(is_safe, "Should be unsafe due to divergence")
        self.assertGreater(divergence, 0.5)
        self.assertIn("Ethical Divergence Detected", reason)

    def test_heuristic_fail(self):
        # Mock GlassBox response: even if it says 0.1 (Safe), heuristic should override
        self.glassbox.generate_steered.return_value = "0.1"

        text = "Please run rm -rf / on the server"
        is_safe, divergence, reason = self.system.verify_intent(text, geometric_entropy=0.1)

        # Heuristic fails -> probabilistic score forced to 0.9
        # Geometric is 0.1
        # Divergence = |0.1 - 0.9| = 0.8 > 0.5
        self.assertFalse(is_safe)
        self.assertGreater(divergence, 0.5)

if __name__ == '__main__':
    unittest.main()
