"""
Test SkillRL Integration
------------------------
Verifies that the Skill Evolution Engine creates and updates logs and registry.
"""
import sys
import os
import unittest
import json
import torch
from pathlib import Path
from unittest.mock import MagicMock, patch

# Adjust path to find gca-service modules
SERVICE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SERVICE_ROOT))

from gca_pilot_v3_skillrl import GCAPilot

class TestSkillRL(unittest.TestCase):
    def setUp(self):
        # Set up temporary paths for testing
        self.test_registry = "test_skill_registry.json"
        self.test_history = "test_trajectory_history.jsonl"

        # Monkey patch the paths in skillrl module
        from gca_core import skillrl
        skillrl.REGISTRY_PATH = self.test_registry
        skillrl.HISTORY_PATH = self.test_history

        # Clean up previous test runs
        if os.path.exists(self.test_registry):
            os.remove(self.test_registry)
        if os.path.exists(self.test_history):
            os.remove(self.test_history)

    def tearDown(self):
        # Clean up
        if os.path.exists(self.test_registry):
            os.remove(self.test_registry)
        if os.path.exists(self.test_history):
            os.remove(self.test_history)

    @patch('gca_pilot_v3_skillrl.GlassBox')
    @patch('gca_pilot_v3_skillrl.IsotropicMemory')
    @patch('gca_pilot_v3_skillrl.ResourceManager')
    def test_evolution_cycle(self, MockRM, MockMemory, MockGlassBox):
        # Setup Mocks
        mock_glassbox = MockGlassBox.return_value
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_basis = torch.randn(16, 768) # 16 skills, 768 dim

        mock_glassbox.model = mock_model
        mock_glassbox.tokenizer = mock_tokenizer
        mock_glassbox.device = "cpu"
        mock_glassbox.get_hidden_size.return_value = 768
        mock_glassbox.generate_steered.return_value = "Test response"

        # Ensure mock_model doesn't trip up hasattr checks for other architectures
        del mock_model.transformer
        del mock_model.model

        # Mock Memory
        mock_memory = MockMemory.return_value
        mock_memory.get_or_create_basis.return_value = mock_basis

        # Mock Model Layers for Hook (simulate structure with layers attribute)
        mock_layer = MagicMock()
        # Create a list of mocks long enough to include layer 6
        mock_model.layers = [MagicMock() for _ in range(10)]
        mock_model.layers[6] = mock_layer

        # Capture the hook when it's registered
        captured_hook = []
        def register_hook_side_effect(hook):
            captured_hook.append(hook)
            handle = MagicMock()
            handle.remove.side_effect = lambda: captured_hook.remove(hook) if hook in captured_hook else None
            return handle
        mock_layer.register_forward_hook.side_effect = register_hook_side_effect

        # Simulate model forward pass triggering the hook
        def model_forward_side_effect(**kwargs):
            for h in list(captured_hook): # Use list() copy to avoid modification during iteration issues
                # Run the hook with dummy output
                # Output tuple (hidden_states, ...)
                dummy_output = torch.randn(1, 5, 768) # Batch 1, Seq 5, Dim 768
                # hook(module, input, output)
                h(mock_layer, None, (dummy_output,))
            return None
        mock_model.side_effect = model_forward_side_effect

        # Mock Tokenizer return
        class MockEncoding(dict):
            def to(self, device):
                return self

        mock_encoding = MockEncoding({"input_ids": torch.tensor([[1, 2, 3]])})
        mock_tokenizer.return_value = mock_encoding

        # Initialize Pilot
        pilot = GCAPilot()

        # Run a mission with a high score to trigger evolution
        prompt = "Explain the concept of entropy in information theory."
        pilot.run_mission(prompt, skill_name="test_skill", score=0.9)

        # Verify History Log
        self.assertTrue(os.path.exists(self.test_history), "History log not created")
        with open(self.test_history, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            entry = json.loads(lines[0])
            self.assertEqual(entry['skill'], "test_skill")
            self.assertEqual(entry['score'], 0.9)

        # Verify Skill Registry
        self.assertTrue(os.path.exists(self.test_registry), "Skill registry not created")
        with open(self.test_registry, 'r') as f:
            registry = json.load(f)
            self.assertIn("test_skill", registry)
            self.assertEqual(registry["test_skill"]["evolution_generations"], 1)
            self.assertTrue("vector_coeffs" in registry["test_skill"])
            # Coeffs should be length 16 (basis dim)
            self.assertEqual(len(registry["test_skill"]["vector_coeffs"]), 16)

        # Run another mission to verify evolution (update)
        pilot.run_mission(prompt, skill_name="test_skill", score=0.8)

        with open(self.test_registry, 'r') as f:
            registry = json.load(f)
            self.assertEqual(registry["test_skill"]["evolution_generations"], 2)

        print("\nTest passed: Trajectory logged and Skill evolved.")

if __name__ == '__main__':
    unittest.main()
