import unittest
from unittest.mock import MagicMock, patch
import torch
import time
from gca_core.memory_advanced import BiomimeticMemory, Engram, SensoryBuffer, EpisodicHippocampus, SemanticNeocortex

class MockGlassBox:
    def __init__(self):
        self.device = "cpu"

    def get_activation(self, text):
        return torch.randn(32)

    def get_hidden_size(self):
        return 32

class TestMemoryHierarchy(unittest.TestCase):
    def setUp(self):
        self.glassbox = MockGlassBox()
        self.base_memory = MagicMock()
        from pathlib import Path
        self.base_memory.storage_path = Path(".")
        self.base_memory.get_or_create_basis.return_value = torch.eye(32) # Identity for testing

        # Mock SecureStorage
        with patch('gca_core.memory_advanced.SecureStorage'):
             self.memory = BiomimeticMemory(self.glassbox, self.base_memory)

    def test_sensory_buffer_decay(self):
        buffer = SensoryBuffer()
        for i in range(5):
             buffer.add(Engram(f"content{i}", torch.randn(32)))

        # Should only keep last 3
        self.assertEqual(len(buffer.buffer), 3)
        self.assertEqual(buffer.buffer[0].content, "content2")

    def test_episodic_capacity(self):
        # Default capacity 7
        for i in range(10):
            # We need vectors that are distinct enough to not trigger rehearsal update
            # random vectors are usually orthogonal enough in high dims, but here 32 dims.
            # let's hope so.
            self.memory._process_into_episodic(Engram(f"ep{i}", torch.randn(32)))

        self.assertEqual(len(self.memory.episodic.engrams), 7)

    def test_consolidation(self):
        # Create an item with high activation
        engram = Engram("Important", torch.randn(32), activation_count=5)

        # Mock SemanticNeocortex.consolidate
        self.memory.semantic.consolidate = MagicMock()

        self.memory._evict_or_consolidate(engram)
        self.memory.semantic.consolidate.assert_called_once_with(engram)

    def test_perceive_flow(self):
        # Test full flow
        self.memory.perceive("Hello World")
        self.assertEqual(len(self.memory.episodic.engrams), 1)
        self.assertEqual(self.memory.episodic.engrams[0].content, "Hello World")

if __name__ == '__main__':
    unittest.main()
