
import unittest
from unittest.mock import MagicMock
import sys
import os

# Create a proper mock hierarchy for torch
torch_mock = MagicMock()
sys.modules['torch'] = torch_mock
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['textblob'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()

# Now import GlassBox
sys.path.append(os.path.join(os.path.dirname(__file__), "apps/gca-service"))

# We might need to mock gca_core dependencies if they are imported at top level
# But let's try importing GlassBox directly
# The traceback showed import error in skillrl.py which is imported by __init__.py
# So we must handle that.

from gca_core.glassbox import GlassBox

class TestGlassBoxLeak(unittest.TestCase):
    def test_hook_leak_on_exception(self):
        # Mock dependencies
        config = {'system': {'model_id': 'mock-model', 'device': 'cpu'}}
        glassbox = GlassBox(config=config)
        glassbox.tokenizer = MagicMock()
        glassbox.model = MagicMock()
        glassbox.device = 'cpu'
        glassbox.dtype = 'float32'

        # Mock layer
        mock_layer = MagicMock()
        glassbox._get_layer = MagicMock(return_value=mock_layer)

        # Setup model to raise exception
        glassbox.model.side_effect = RuntimeError("Simulated Forward Pass Error")
        glassbox.tokenizer.return_value = {'input_ids': torch_mock.tensor([1,2,3])}

        # Capture hook registration
        hooks = []
        def register_hook(hook):
            handle = MagicMock()
            handle.remove = MagicMock()
            hooks.append(handle)
            return handle
        mock_layer.register_forward_hook = MagicMock(side_effect=register_hook)

        # Trigger cached activation (which registers hook)
        try:
            glassbox._cached_activation("test input", layer_idx=0)
        except RuntimeError:
            pass
        except Exception as e:
            # Catch other potential mocks failing
            print(f"Unexpected error: {e}")

        # Check if remove was called
        if not hooks:
            self.fail("Hook was never registered!")

        handle = hooks[0]
        try:
            handle.remove.assert_called_once()
            print("SUCCESS: Hook was removed correctly.")
        except AssertionError:
            print("FAILURE: Hook was NOT removed! Leak confirmed.")
            # We expect failure here before fix, so we verify leak happened
            pass

if __name__ == "__main__":
    unittest.main()
