import sys
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Mock EVERYTHING
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.fernet'] = MagicMock()
sys.modules['yaml'] = MagicMock()

# Setup Fernet mock return values
fernet_mock = MagicMock()
fernet_mock.generate_key.return_value = b'test_key_12345678901234567890123456789012='
sys.modules['cryptography.fernet'].Fernet = fernet_mock

# Ensure we can import gca_core
sys.path.insert(0, ".")

# Now import modules under test
from gca_core.memory_advanced import BiomimeticMemory, Engram
from gca_core.pulse import PulseSystem
from gca_core.secure_storage import SecureStorage

# Re-mock torch after import just in case
import torch

# Mock GlassBox
class MockGlassBox:
    def __init__(self):
        self.device = "cpu"
        self.model_name = "test"
    def get_hidden_size(self):
        return 10
    def get_activation(self, text):
        return MagicMock()

# Mock Base Memory
class MockBaseMemory:
    def __init__(self):
        self.storage_path = Path("./gca_assets_test")
        self.storage_path.mkdir(exist_ok=True)
    def get_or_create_basis(self, input_dim, output_dim):
        return MagicMock()

def test_biomimetic_memory_ltm_save():
    print("\n--- Testing BiomimeticMemory LTM Save ---")
    gb = MockGlassBox()
    base = MockBaseMemory()

    # Init BioMem (Should init SecureStorage internally now)
    try:
        bio = BiomimeticMemory(gb, base)
        print("BiomimeticMemory initialized.")
    except Exception as e:
        print(f"FAIL: Initialization error: {e}")
        return

    if not hasattr(bio, 'secure_storage'):
        print("FAIL: secure_storage attribute missing!")
        return
    else:
        print("PASS: secure_storage attribute present.")

    # Mock the secure storage instance methods to avoid file I/O
    bio.secure_storage.append_jsonl = MagicMock()

    # Create an engram manually
    engram = Engram(
        content="Test Memory",
        vector=MagicMock(),
        activation_count=5 # High count to trigger consolidation
    )

    # Force save
    try:
        bio._save_long_term(engram)
        bio.secure_storage.append_jsonl.assert_called_once()
        print("PASS: _save_long_term executed and called append_jsonl.")
    except Exception as e:
        print(f"FAIL: _save_long_term crashed: {e}")

def test_pulse_goal_loading():
    print("\n--- Testing PulseSystem Goal Loading ---")
    gb = MockGlassBox()
    mem = MockBaseMemory()

    pulse = PulseSystem(mem, gb)

    print(f"Pulse Goal Path: {pulse.goal_path}")
    # We might need to mock open() if file access is restricted, but usually read is fine.
    # However, if path calculation is wrong, it won't find the file.

    if pulse.cached_goal_text:
         print(f"Pulse Cached Goal Text (first 50 chars): {pulse.cached_goal_text[:50]}...")
         if "stoic" in pulse.cached_goal_text.lower():
             print("PASS: Goal text loaded correctly.")
         else:
             print("WARN: Goal text seems default or unexpected.")
    else:
         print("FAIL: No goal text loaded.")

if __name__ == "__main__":
    try:
        test_biomimetic_memory_ltm_save()
        test_pulse_goal_loading()
    finally:
        # Cleanup
        if Path("./gca_assets_test").exists():
            shutil.rmtree("./gca_assets_test")
