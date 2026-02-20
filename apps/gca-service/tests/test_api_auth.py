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
        self.cached_goal_text = "Goal"
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

class TestReasoningAuth(unittest.TestCase):
    def setUp(self):
        # We must re-create the TestClient because dependency overrides might persist if we modify app directly
        self.client = TestClient(api_server.app)

        # Reset mocks
        api_server.glassbox.generate_steered = MagicMock(return_value="Safe Response")
        api_server.pulse.current_entropy = 0.1
        api_server.dual_ethics.verify_intent = MagicMock(return_value=(True, 0.0, "Verified"))
        api_server.guardrail.scan.return_value = (True, "Safe")
        api_server.optimizer.route_intent.return_value = "intent_vector"
        api_server.causal_engine.calculate_causal_beta.return_value = {}

        # Default CFG Mock behavior: No key set in config
        # We need to access the CFG object in api_server. Since it's imported at module level, we can modify it.
        # However, api_server.CFG is already a Mock object (from mock_gca_core).
        # Let's ensure it behaves predictably.
        api_server.CFG.get.return_value = {} # Default: empty config

    def test_missing_config_returns_500(self):
        """
        If no API Key is configured on the server (Env or Config), requests should fail with 500.
        """
        # Ensure env is clean
        with patch.dict(os.environ, {}, clear=True):
             # Ensure config is clean
             api_server.CFG.get.side_effect = lambda k, default=None: {} if k == "security" else default

             payload = {"user_id": "u", "text": "t"}
             response = self.client.post("/v1/reason", json=payload)

             self.assertEqual(response.status_code, 500)
             self.assertIn("API Key not set", response.json()["detail"])

    def test_unauthenticated_request_returns_403(self):
        """
        If API Key is configured, but request is missing it, should fail with 403.
        """
        with patch.dict(os.environ, {"GCA_API_KEY": "secret-key"}):
            payload = {"user_id": "u", "text": "t"}
            response = self.client.post("/v1/reason", json=payload)

            self.assertEqual(response.status_code, 403)

    def test_authenticated_request_returns_200(self):
        """
        If API Key is configured and provided in header, should succeed.
        """
        with patch.dict(os.environ, {"GCA_API_KEY": "secret-key"}):
            payload = {"user_id": "u", "text": "t"}
            headers = {"X-GCA-API-Key": "secret-key"}
            response = self.client.post("/v1/reason", json=payload, headers=headers)

            if response.status_code != 200:
                print(f"Auth Test Failed: {response.text}")

            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
