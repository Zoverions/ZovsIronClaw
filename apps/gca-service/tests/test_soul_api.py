import sys
import os
from unittest.mock import MagicMock

# --- 1. MOCK HEAVY LIBRARIES ---
# We mock these BEFORE importing api_server to avoid ImportError or heavy loading

modules_to_mock = [
    "torch", "transformers", "accelerate", "numpy", "scikit-learn",
    "textblob", "sentence_transformers", "faster_whisper", "cv2",
    "PIL", "einops", "moviepy", "qwen_vl_utils", "networkx",
    "pydub", # Maybe needed
    "sklearn.metrics.pairwise" # Specifically
]

for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

# --- 2. MOCK GCA CORE MODULES ---
# We mock most of the core to avoid dependencies on config, models, etc.
# But we need to be careful with 'api_server' imports.

# gca_core.glassbox
sys.modules["gca_core.glassbox"] = MagicMock()
# gca_core.resource_manager
mock_rm = MagicMock()
mock_rm.ResourceManager.return_value.get_active_config.return_value = {"active_profile": "TEST"}
sys.modules["gca_core.resource_manager"] = mock_rm
# gca_core.moral
sys.modules["gca_core.moral"] = MagicMock()
# gca_core.optimizer
sys.modules["gca_core.optimizer"] = MagicMock()
# gca_core.memory
sys.modules["gca_core.memory"] = MagicMock()
# gca_core.resonance
sys.modules["gca_core.resonance"] = MagicMock()
# gca_core.qpt
sys.modules["gca_core.qpt"] = MagicMock()
# gca_core.arena
sys.modules["gca_core.arena"] = MagicMock()
# gca_core.memory_advanced
sys.modules["gca_core.memory_advanced"] = MagicMock()
# gca_core.perception
sys.modules["gca_core.perception"] = MagicMock()
# gca_core.observer
sys.modules["gca_core.observer"] = MagicMock()
# gca_core.pulse
sys.modules["gca_core.pulse"] = MagicMock()
# gca_core.causal_flow
sys.modules["gca_core.causal_flow"] = MagicMock()
# gca_core.swarm
sys.modules["gca_core.swarm"] = MagicMock()
# gca_core.reflective_logger
sys.modules["gca_core.reflective_logger"] = MagicMock()
# gca_core.security
sys.modules["gca_core.security"] = MagicMock()
# dreamer
sys.modules["dreamer"] = MagicMock()

# Specifically for soul_loader, we want to control it
mock_soul_loader_module = MagicMock()
sys.modules["gca_core.soul_loader"] = mock_soul_loader_module

# --- 3. IMPORT APP ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Need to ensure os.path.expanduser doesn't fail if mocked? No, that's standard lib.
# But api_server uses open() on config files. We might need to patch builtins open if it fails.
# Let's try importing first.

try:
    from api_server import app
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

from fastapi.testclient import TestClient

client = TestClient(app)

# --- 4. TESTS ---

def test_list_souls():
    # Setup the mock for get_soul_loader
    mock_loader_instance = MagicMock()
    mock_loader_instance.list_souls.return_value = ["Architect", "Stoic"]
    mock_loader_instance.get_soul_info.return_value = {"name": "Test", "description": "Test Soul"}

    mock_soul_loader_module.get_soul_loader.return_value = mock_loader_instance

    response = client.get("/v1/soul/list")
    assert response.status_code == 200
    data = response.json()

    print(f"Response: {data}")

    assert "souls" in data
    assert data["souls"] == ["Architect", "Stoic"]
    assert "details" in data
    assert data["details"]["Architect"]["name"] == "Test"
    print("test_list_souls passed")

def test_compose_soul():
    # Setup mock
    mock_loader_instance = MagicMock()
    mock_loader_instance.create_composite_soul.return_value.name = "Composite-Soul"
    mock_loader_instance.create_composite_soul.return_value.traits = ["Adaptable"]

    mock_soul_loader_module.get_soul_loader.return_value = mock_loader_instance

    payload = {
        "base_style": "Architect",
        "blend_styles": ["Stoic"],
        "blend_weights": [0.5]
    }

    response = client.post("/v1/soul/compose", json=payload)
    assert response.status_code == 200
    data = response.json()

    print(f"Compose Response: {data}")

    assert data["status"] == "composed"
    assert data["name"] == "Composite-Soul"
    print("test_compose_soul passed")

if __name__ == "__main__":
    test_list_souls()
    test_compose_soul()
    print("All tests passed!")
