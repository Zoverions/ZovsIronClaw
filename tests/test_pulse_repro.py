
import unittest
from unittest.mock import MagicMock, patch
import torch
import time
from gca_core.pulse import PulseSystem
from gca_core.memory_advanced import BiomimeticMemory, Engram
from gca_core.active_inference import FreeEnergyState

class MockGlassBox:
    def __init__(self):
        self.device = "cpu"

    def get_activation(self, text):
        # Return a random vector for testing
        return torch.randn(32)

    def get_hidden_size(self):
        return 32

class TestPulseSystem(unittest.TestCase):
    def setUp(self):
        self.glassbox = MockGlassBox()
        self.base_memory = MagicMock()
        from pathlib import Path
        self.base_memory.storage_path = Path(".")

        # Mock SecureStorage to avoid file I/O issues during test
        with patch('gca_core.memory_advanced.SecureStorage'):
            self.memory = BiomimeticMemory(self.glassbox, self.base_memory)

        # Manually add something to working memory
        engram = Engram(content="Test thought", vector=torch.randn(32))
        self.memory.working_memory.append(engram)

        self.pulse = PulseSystem(self.memory, self.glassbox, check_interval=1)
        # Mock goal loading
        self.pulse.cached_goal_text = "Goal text"

    def test_entropy_calculation(self):
        # Run one check
        self.pulse._check_vitals()
        print(f"Current Entropy: {self.pulse.current_entropy}")
        self.assertTrue(0.0 <= self.pulse.current_entropy <= 2.0)

    def test_intervention(self):
        # Force high entropy
        self.pulse.current_entropy = 0.8
        callback = MagicMock()
        self.pulse.set_intervention_callback(callback)
        fe_state = FreeEnergyState(0.8, "reflexive")
        self.pulse._trigger_intervention(fe_state)
        callback.assert_called_once()
        print("Intervention triggered successfully")

if __name__ == '__main__':
    unittest.main()
