
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies (must match what GlassBox expects)
sys.modules['torch'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['transformers'] = MagicMock()

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../gca-service')))
from gca_core.glassbox import GlassBox

class TestLazyLoading(unittest.TestCase):
    def test_lazy_loading_mechanics(self):
        """
        Verify that GlassBox initializes without loading the model,
        and loads it only when needed.
        """
        # Mock configuration
        config = {
            'system': {'model_id': 'test-model', 'device': 'cpu', 'dtype': 'float32'},
            'geometry': {'layer_idx': 0}
        }

        print("Initializing GlassBox...")
        gb = GlassBox(config=config)

        self.assertIsNone(gb.model, "Model should be None initially")
        self.assertIsNone(gb.tokenizer, "Tokenizer should be None initially")
        print("PASS: Model is lazy.")

        with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model_cls, \
             patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer_cls:

            mock_model = MagicMock()
            mock_model_cls.return_value = mock_model
            mock_tokenizer = MagicMock()
            mock_tokenizer_cls.return_value = mock_tokenizer

            print("Calling _ensure_model_loaded()...")
            gb._ensure_model_loaded()

            self.assertIsNotNone(gb.model, "Model should be loaded now")
            mock_model_cls.assert_called_once()
            print("PASS: Model loaded on demand.")

    def test_dtype_auto_selection(self):
        """
        Verify that 'auto' dtype selects float16 for cuda/mps and float32 for cpu.
        """
        # Case 1: CPU -> float32
        config_cpu = {'system': {'model_id': 'test', 'device': 'cpu', 'dtype': 'auto'}}
        gb_cpu = GlassBox(config=config_cpu)
        # Verify gb_cpu.dtype matches torch.float32 (mocked)
        # Since torch is mocked, let's just check the logic
        # But wait, torch.float32 is a mock object now.
        # We can't compare directly to real torch types easily.
        # Let's inspect the code logic or trust the mock behavior if we set attributes on torch mock.

        # Mock torch attributes
        sys.modules['torch'].float32 = 'float32_obj'
        sys.modules['torch'].float16 = 'float16_obj'

        # Re-init to pick up mocked torch attributes
        gb_cpu = GlassBox(config=config_cpu)
        self.assertEqual(gb_cpu.dtype, 'float32_obj', "CPU should default to float32")
        print("PASS: CPU -> float32")

        # Case 2: CUDA -> float16
        config_cuda = {'system': {'model_id': 'test', 'device': 'cuda', 'dtype': 'auto'}}
        gb_cuda = GlassBox(config=config_cuda)
        self.assertEqual(gb_cuda.dtype, 'float16_obj', "CUDA should default to float16")
        print("PASS: CUDA -> float16")

        # Case 3: MPS -> float16
        config_mps = {'system': {'model_id': 'test', 'device': 'mps', 'dtype': 'auto'}}
        gb_mps = GlassBox(config=config_mps)
        self.assertEqual(gb_mps.dtype, 'float16_obj', "MPS should default to float16")
        print("PASS: MPS -> float16")

if __name__ == '__main__':
    unittest.main()
