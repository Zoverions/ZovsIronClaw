import sys
import os
from unittest.mock import MagicMock

# --- 1. MOCK HEAVY LIBRARIES ---
modules_to_mock = [
    "torch", "transformers", "accelerate", "numpy", "scikit-learn",
    "textblob", "sentence_transformers", "faster_whisper", "cv2",
    "PIL", "einops", "moviepy", "qwen_vl_utils", "networkx",
    "pydub", "sklearn.metrics.pairwise"
]
for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

# --- 2. MOCK GCA CORE MODULES ---
mock_glassbox = MagicMock()
sys.modules["gca_core.glassbox"] = mock_glassbox

mock_rm = MagicMock()
mock_rm.ResourceManager.return_value.get_active_config.return_value = {"active_profile": "TEST"}
sys.modules["gca_core.resource_manager"] = mock_rm

mock_optimizer = MagicMock()
sys.modules["gca_core.optimizer"] = mock_optimizer

sys.modules["gca_core.moral"] = MagicMock()
sys.modules["gca_core.memory"] = MagicMock()
sys.modules["gca_core.resonance"] = MagicMock()
sys.modules["gca_core.qpt"] = MagicMock()
sys.modules["gca_core.arena"] = MagicMock()
sys.modules["gca_core.memory_advanced"] = MagicMock()
sys.modules["gca_core.perception"] = MagicMock()
sys.modules["gca_core.observer"] = MagicMock()
sys.modules["gca_core.pulse"] = MagicMock()
sys.modules["gca_core.causal_flow"] = MagicMock()
sys.modules["gca_core.swarm"] = MagicMock()
sys.modules["gca_core.reflective_logger"] = MagicMock()
sys.modules["gca_core.security"] = MagicMock()
sys.modules["dreamer"] = MagicMock()
sys.modules["gca_core.soul_loader"] = MagicMock()

# Mock Tools (since we import Tool from it)
mock_tools_module = MagicMock()
class MockTool:
    def __init__(self, name, description, parameters, intent_vector):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.intent_vector = intent_vector
    def format_prompt(self):
        return f"Tool: {self.name}"
mock_tools_module.Tool = MockTool
sys.modules["gca_core.tools"] = mock_tools_module

# --- 3. IMPORT APP ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api_server import app, glassbox, optimizer, qpt, pulse, moral_kernel

# Configure pulse mock
pulse.current_entropy = 0.1
# Configure moral kernel mock
moral_kernel.evaluate.return_value = (True, "Approved")

from fastapi.testclient import TestClient

client = TestClient(app)

def test_chat_completions_basic():
    # Setup mocks
    glassbox.generate_steered.return_value = "Hello! I am ready to help."
    optimizer.route_intent.return_value = "GREETING"
    optimizer.prioritize_tools.return_value = []

    payload = {
        "model": "gca-architect",
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }

    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["choices"][0]["message"]["content"] == "Hello! I am ready to help."
    assert data["model"] == "gca-architect"
    print("test_chat_completions_basic passed")

def test_chat_completions_with_tools():
    # Setup mocks
    glassbox.generate_steered.return_value = "I will use the tool.\nTOOL_CALL: bash echo 'hello'"
    optimizer.prioritize_tools.side_effect = lambda tools, input: tools # Return passed tools

    # We need to ensure _parse_tool_from_text works (it's imported/defined in api_server)
    # Since api_server uses simple regex, it should match TOOL_CALL:

    payload = {
        "model": "gca-architect",
        "messages": [{"role": "user", "content": "Run echo"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Run shell",
                    "parameters": {"type": "object"}
                }
            }
        ]
    }

    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()

    choice = data["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert "tool_calls" in choice["message"]
    tool_call = choice["message"]["tool_calls"][0]
    assert tool_call["function"]["name"] == "bash"
    assert "echo 'hello'" in tool_call["function"]["arguments"]
    print("test_chat_completions_with_tools passed")

if __name__ == "__main__":
    test_chat_completions_basic()
    test_chat_completions_with_tools()
