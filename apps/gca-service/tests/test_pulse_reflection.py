import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Mock heavy dependencies BEFORE import
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["transformers"] = MagicMock()

import numpy as np

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gca_core.pulse import PulseSystem
from gca_core.active_inference import GenerativeModel, ActiveInferenceLoop, FreeEnergyState

class TestPulseReflection(unittest.TestCase):
    def setUp(self):
        self.mock_glassbox = MagicMock()
        self.mock_glassbox.generate_steered.return_value = "Reflection: I am doing great on ethics."

        self.mock_memory = MagicMock()
        self.mock_memory.basis = None
        # Mock working_memory as a list of mock objects with .vector and .content
        mock_engram = MagicMock()
        mock_engram.vector = np.array([0.1, 0.2])
        mock_engram.content = "Some thought"
        self.mock_memory.working_memory = [mock_engram]

        self.mock_causal = MagicMock()
        self.mock_qpt = MagicMock()

        # Mock CronReader since Pulse initializes it
        with patch('gca_core.pulse.CronReader') as MockCron:
             self.pulse = PulseSystem(
                 self.mock_memory,
                 self.mock_glassbox,
                 causal_engine=self.mock_causal,
                 qpt=self.mock_qpt,
                 check_interval=1
             )

        # Mock active_loop to return a safe FreeEnergyState
        self.pulse.active_loop = MagicMock()
        self.pulse.active_loop.compute_free_energy.return_value = FreeEnergyState(0.1, "homeostatic")

        # Mock HorizonScanner update to avoid side effects
        self.pulse.horizon_scanner = MagicMock()
        self.pulse.horizon_scanner.update.return_value = MagicMock(is_critical_variance=False)

    def test_reflection_triggered(self):
        """Test that reflection is triggered every 5 ticks."""
        # Initial state
        self.assertEqual(self.pulse._ticks, 0)

        # 4 ticks - should not reflect
        for _ in range(4):
            self.pulse._check_vitals()

        self.assertEqual(self.pulse._ticks, 4)
        self.mock_glassbox.generate_steered.assert_not_called()

        # 5th tick - should reflect
        self.pulse._check_vitals()
        self.assertEqual(self.pulse._ticks, 5)

        # Verify glassbox call
        self.mock_glassbox.generate_steered.assert_called_once()
        args, kwargs = self.mock_glassbox.generate_steered.call_args
        prompt = args[0]
        self.assertIn("Primary Goal", prompt)
        self.assertIn("Ethical Wealth Generation", prompt)

        # Verify memory injection
        self.mock_memory.perceive.assert_called()
        call_args = self.mock_memory.perceive.call_args
        self.assertIn("[SELF_REFLECTION]", call_args[0][0])

    def test_reflection_error_handling(self):
        """Test that reflection errors are handled gracefully."""
        # Set tick to 4
        self.pulse._ticks = 4

        # Make glassbox raise exception
        self.mock_glassbox.generate_steered.side_effect = Exception("Generation failed")

        # 5th tick
        try:
            self.pulse._check_vitals()
        except Exception:
            self.fail("PulseSystem crashed on reflection error")

        self.assertEqual(self.pulse._ticks, 5)
        # Should not have crashed

if __name__ == '__main__':
    unittest.main()
