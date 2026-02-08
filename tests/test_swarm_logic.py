import unittest
from unittest.mock import MagicMock
import hashlib
from gca_core.swarm import SwarmNetwork

class MockGlassBox:
    def get_activation(self, text):
        import torch
        return torch.randn(32)

class TestSwarmLogic(unittest.TestCase):
    def setUp(self):
        self.glassbox = MockGlassBox()
        self.logger = MagicMock()
        self.swarm = SwarmNetwork(self.glassbox, self.logger)
        self.swarm.register_node("agent1", "worker", [])

    def test_submit_valid_pol(self):
        cot = "This is a valid reasoning chain because it has markers."
        cot_hash = hashlib.sha256(cot.encode()).hexdigest()

        success = self.swarm.submit_result("agent1", "result", cot, cot_hash)
        self.assertTrue(success)
        self.assertEqual(self.swarm.nodes["agent1"].status, "idle")

    def test_submit_invalid_hash(self):
        cot = "Valid reasoning."
        cot_hash = "wronghash"

        success = self.swarm.submit_result("agent1", "result", cot, cot_hash)
        self.assertFalse(success)

    def test_submit_weak_logic(self):
        cot = "bad"
        cot_hash = hashlib.sha256(cot.encode()).hexdigest()

        success = self.swarm.submit_result("agent1", "result", cot, cot_hash)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
