import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add apps/gca-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock external dependencies
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["textblob"] = MagicMock()
sys.modules["faster_whisper"] = MagicMock()
sys.modules["cv2"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["moviepy"] = MagicMock()
sys.modules["qwen_vl_utils"] = MagicMock()
sys.modules["networkx"] = MagicMock()
sys.modules["mnemonic"] = MagicMock()
sys.modules["cryptography"] = MagicMock()

# Mock GCA Core components entirely
mock_gca_core = MagicMock()
mock_gca_core.__path__ = [] # Mark as package
sys.modules["gca_core"] = mock_gca_core

sys.modules["gca_core.glassbox"] = MagicMock()
sys.modules["gca_core.pulse"] = MagicMock()
sys.modules["gca_core.dual_ethics"] = MagicMock()
sys.modules["gca_core.resource_manager"] = MagicMock()
sys.modules["gca_core.moral"] = MagicMock()
sys.modules["gca_core.optimizer"] = MagicMock()
sys.modules["gca_core.memory"] = MagicMock()
sys.modules["gca_core.memory_advanced"] = MagicMock()
sys.modules["gca_core.resonance"] = MagicMock()
sys.modules["gca_core.qpt"] = MagicMock()
sys.modules["gca_core.perception"] = MagicMock()
sys.modules["gca_core.observer"] = MagicMock()
sys.modules["gca_core.causal_flow"] = MagicMock()
sys.modules["gca_core.swarm"] = MagicMock()
sys.modules["gca_core.reflective_logger"] = MagicMock()
sys.modules["gca_core.security"] = MagicMock()
sys.modules["gca_core.blockchain"] = MagicMock()
sys.modules["gca_core.security_guardrail"] = MagicMock()
sys.modules["gca_core.soul_loader"] = MagicMock()
sys.modules["gca_core.tools"] = MagicMock()
sys.modules["gca_core.arena"] = MagicMock()
sys.modules["dreamer"] = MagicMock()

# Define Mock Classes that api_server expects to instantiate
class MockGlassBox:
    def __init__(self, *args, **kwargs):
        self.device = "cpu"
        self.model_name = "mock-model"
    def generate_steered(self, *args, **kwargs):
        return "Generated Response"

class MockPulse:
    def __init__(self, *args, **kwargs):
        self.current_entropy = 0.1
        self.horizon_scanner = MagicMock()
        self.horizon_scanner.get_status.return_value = {}
    def set_intervention_callback(self, *args): pass
    def start(self): pass

class MockDualEthics:
    def __init__(self, *args, **kwargs): pass
    def verify_intent(self, text, entropy):
        return True, 0.0, "Verified"

# Assign Mock Classes to the mocked modules so api_server can import them
sys.modules["gca_core.glassbox"].GlassBox = MockGlassBox
sys.modules["gca_core.pulse"].PulseSystem = MockPulse
sys.modules["gca_core.dual_ethics"].DualEthicalSystem = MockDualEthics

# Import api_server
import api_server

from fastapi.testclient import TestClient

class TestApiIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api_server.app)

        # Reset mocks
        api_server.glassbox.generate_steered = MagicMock(return_value="Safe Response")
        api_server.pulse.current_entropy = 0.1
        api_server.dual_ethics.verify_intent = MagicMock(return_value=(True, 0.0, "Verified"))

        # Mock other components called in logic
        api_server.guardrail.scan.return_value = (True, "Safe")
        api_server.optimizer.route_intent.return_value = "intent_vector"
        api_server.memory.get_vector.return_value = MagicMock()
        api_server.bio_mem.retrieve_context.return_value = "context"
        api_server.qpt.restructure.return_value = "prompt"
        api_server.optimizer.prioritize_tools.return_value = []
        api_server.moral_kernel.evaluate.return_value = (True, "Safe")


    def test_chat_success(self):
        payload = {
            "model": "gpt-4-test",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        response = self.client.post("/v1/chat/completions", json=payload)

        if response.status_code != 200:
            print(f"Error Response: {response.text}")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["choices"][0]["message"]["content"], "Safe Response")

        # Verify generate_steered called with model override
        api_server.glassbox.generate_steered.assert_called_once()
        args, kwargs = api_server.glassbox.generate_steered.call_args
        self.assertEqual(kwargs["model"], "gpt-4-test")

    def test_dual_ethics_intervention(self):
        # Setup divergence
        api_server.dual_ethics.verify_intent.return_value = (False, 0.9, "Divergence Detected")

        payload = {
            "model": "gpt-4-test",
            "messages": [{"role": "user", "content": "Dangerous Request"}]
        }
        response = self.client.post("/v1/chat/completions", json=payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        self.assertIn("DUAL ETHICS INTERVENTION", content)
        self.assertIn("Divergence Detected", content)

        # Verify generate_steered NOT called
        api_server.glassbox.generate_steered.assert_not_called()

if __name__ == '__main__':
    unittest.main()
