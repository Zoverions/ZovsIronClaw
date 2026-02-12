
import unittest
from unittest.mock import MagicMock, patch
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
sys.modules['textblob'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()
sys.modules['networkx'] = MagicMock()
sys.modules['moviepy'] = MagicMock()

# Mock numpy
# We need numpy to be usable for math
import builtins
class MockNumpy:
    def mean(self, x):
        if not x: return 0.0
        return sum(x) / len(x)
    def std(self, x):
        return 0.1 # Default small std
    def var(self, x):
        return 0.01

    class random:
        @staticmethod
        def rand():
            return 0.5

np_mock = MockNumpy()
sys.modules['numpy'] = np_mock

# Adjust path to import gca_core
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from gca_core.horizon import HorizonScanner, HorizonState

class TestHorizonIO(unittest.TestCase):
    @patch("gca_core.horizon.Path")
    def test_save_throttling(self, mock_path):
        glassbox = MagicMock()

        # Instantiate
        scanner = HorizonScanner(glassbox)
        scanner.save_state = MagicMock()

        # Calls 1-9: history fills, update_count=0
        for _ in range(9):
            scanner.update(0.5, "ctx")
        self.assertEqual(scanner.save_state.call_count, 0)
        self.assertEqual(scanner.update_count, 0)

        # Call 10: history=10. update_count=1. No save.
        scanner.update(0.5, "ctx")
        self.assertEqual(scanner.save_state.call_count, 0)
        self.assertEqual(scanner.update_count, 1)

        # Calls 11-18: update_count 2..9. No save.
        for _ in range(8):
            scanner.update(0.5, "ctx")
        self.assertEqual(scanner.save_state.call_count, 0)
        self.assertEqual(scanner.update_count, 9)

        # Call 19: update_count 10. Should save.
        scanner.update(0.5, "ctx")
        self.assertEqual(scanner.save_state.call_count, 1)
        self.assertEqual(scanner.update_count, 10)

        # Call 20: update_count 11. No save.
        scanner.update(0.5, "ctx")
        self.assertEqual(scanner.save_state.call_count, 1) # Still 1

    @patch("gca_core.horizon.Path")
    def test_critical_save(self, mock_path):
        glassbox = MagicMock()

        # Create scanner
        scanner = HorizonScanner(glassbox)
        scanner.save_state = MagicMock()

        # Manually fill history to avoid early return
        scanner.history.extend([0.5]*20)

        # We need variance > 0.15. Our MockNumpy.std returns 0.1 -> var 0.01.
        # We need to force a high variance.
        # We can mock np.std inside the context.
        # Since 'numpy' is already mocked globally in sys.modules, we can change the method on that instance.

        original_std = np_mock.std
        np_mock.std = lambda x: 1.0 # High variance

        try:
            # Critical update
            scanner.update(0.5, "ctx")

            # Should save immediately
            scanner.save_state.assert_called_once()
        finally:
            np_mock.std = original_std

if __name__ == "__main__":
    unittest.main()
