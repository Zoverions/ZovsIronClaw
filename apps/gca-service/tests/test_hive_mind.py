import sys
import os
from unittest.mock import MagicMock, patch

# --- 1. MOCK HEAVY LIBRARIES ---
modules_to_mock = [
    "torch", "torch.nn", "torch.nn.functional",
    "transformers", "accelerate", "numpy", "scikit-learn",
    "textblob", "sentence_transformers", "faster_whisper", "cv2",
    "PIL", "einops", "moviepy", "qwen_vl_utils", "networkx",
    "pydub", "sklearn.metrics.pairwise"
]
for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

# --- 2. MOCK GCA CORE ---
mock_glassbox = MagicMock()
sys.modules["gca_core.glassbox"] = mock_glassbox

mock_rm = MagicMock()
mock_rm.ResourceManager.return_value.get_active_config.return_value = {"active_profile": "TEST"}
sys.modules["gca_core.resource_manager"] = mock_rm

# We need real swarm logic for testing broadcast_memory, but mocked network
# So we let swarm import normally (if possible) or mock it carefully.
# Given complexity, we mock the class but attach the real method we want to test or reimplement it in test?
# Better: Import the real class but mock its dependencies.
# However, importing 'api_server' imports everything.

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
sys.modules["gca_core.reflective_logger"] = MagicMock()
sys.modules["gca_core.security"] = MagicMock()
sys.modules["dreamer"] = MagicMock()
sys.modules["gca_core.soul_loader"] = MagicMock()
sys.modules["gca_core.tools"] = MagicMock()

# We need SwarmNetwork to NOT be a complete mock if we want to test its methods,
# but api_server instantiates it.
# Let's mock SwarmNetwork but give it a functional broadcast_memory method or check api_server calls it.
mock_swarm = MagicMock()
mock_mesh = MagicMock()
mock_mesh.agent_id = "test_agent_id"
mock_swarm.SwarmNetwork.return_value.mesh = mock_mesh
sys.modules["gca_core.swarm"] = mock_swarm

# Ensure path is set before importing gca_core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock Blockchain Transaction serialization to avoid MagicMock JSON error
from gca_core.blockchain import Transaction
original_to_dict = Transaction.to_dict
def mock_to_dict(self):
    d = asdict(self)
    # Ensure payload is dict, not mock, if it got mocked
    if hasattr(d['payload'], 'mock_calls'):
        d['payload'] = {}
    return d
# Ideally we patch Transaction but it's a dataclass.
# The error happens in api_server.py import time when it creates a REGISTER_DEVICE tx.
# The payload={"agent_id": str(my_id)} uses my_id from swarm_network.mesh.agent_id.
# If swarm_network is a mock, mesh is a mock, agent_id is a mock.
# str(mock) returns a string representation, so it should be serializable?
# "payload": {"agent_id": "<MagicMock ...>"}
# Ah, str(mock) gives string. But wait, earlier I fixed api_server to use str(my_id).
# So payload is {"agent_id": "MagicMock..."} which IS serializable.
# Why does it fail?
# Maybe `sender=my_key` where my_key comes from security_manager.get_public_key_b64() which returns a Mock?
# And Transaction field sender is `str` but python doesn't enforce.
# So `sender` is a Mock object.
# Correct fix: Ensure security manager mock returns a STRING.

mock_security_instance = MagicMock()
mock_security_instance.get_public_key_b64.return_value = "mock_pub_key_base64"
mock_security_instance.sign_message.return_value = "mock_signature"
mock_security_instance.private_key = "mock_private_key"

mock_security_module = MagicMock()
mock_security_module.SecurityManager.return_value = mock_security_instance
sys.modules["gca_core.security"] = mock_security_module

# --- 3. IMPORT APP ---
from api_server import app, bio_mem, swarm_network, glassbox, optimizer, pulse

# Ensure pulse entropy is a float, not a mock comparison
pulse.current_entropy = 0.1

from fastapi.testclient import TestClient

client = TestClient(app)

def test_memory_teleportation_trigger():
    """
    Simulate a user stating a fact, and verify that broadcast_memory is triggered.
    """
    # 1. Setup Mocks
    # User input
    text = "My favorite color is Cobalt Blue."

    # Mock bio_mem to return flagged memories
    bio_mem.get_flagged_memories.return_value = [
        {"content": text, "vector": [0.1, 0.2], "metadata": {}}
    ]

    # Mock glassbox generation
    glassbox.generate_steered.return_value = "I have noted that your favorite color is Cobalt Blue."

    # Mock optimizer
    # optimizer is an instance of GCAOptimizer, route_intent is a method
    # Since we imported 'optimizer' from api_server, check if it's the mock or real object
    # In test_soul_api.py we mocked the module gca_core.optimizer.
    # In api_server.py: optimizer = GCAOptimizer(glassbox, memory)
    # If the module is mocked, GCAOptimizer is a MagicMock class, so optimizer is a MagicMock instance.
    # optimizer.route_intent is a MagicMock method.

    # However, depending on import order, it might not be.
    # Let's check what optimizer is
    print(f"DEBUG: Optimizer type: {type(optimizer)}")
    if isinstance(optimizer, MagicMock):
        optimizer.route_intent.return_value = "FACT_STORAGE"
    else:
        # If it's real, we mock the method
        optimizer.route_intent = MagicMock(return_value="FACT_STORAGE")
        # Also mock prioritize_tools if needed
        optimizer.prioritize_tools = MagicMock(return_value=[])

    # 2. Call API
    payload = {
        "user_id": "user123",
        "text": text
    }

    response = client.post("/v1/reason", json=payload)

    # 3. Verify Response
    assert response.status_code == 200
    data = response.json()
    assert "Cobalt Blue" in data["content"]

    # 4. Verify Teleportation Trigger
    # We expect swarm_network.broadcast_memory to be called
    # Since api_server.py uses `swarm_network` global instance which is the return value of the mocked class constructor?
    # No, `swarm_network = SwarmNetwork(...)` in api_server.
    # So `swarm_network` variable in api_server is the Mock object returned by `SwarmNetwork()`.

    assert swarm_network.broadcast_memory.called
    args = swarm_network.broadcast_memory.call_args[0][0]
    assert len(args) == 1
    assert args[0]["content"] == text
    print("test_memory_teleportation_trigger passed: Hive Mind sync triggered.")

if __name__ == "__main__":
    test_memory_teleportation_trigger()
