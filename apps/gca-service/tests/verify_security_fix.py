import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock heavy dependencies
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.decomposition'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['textblob'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['qwen_vl_utils'] = MagicMock()
sys.modules['networkx'] = MagicMock()

# Import GlassBox
# Adjust path to ensure it can import gca_core
sys.path.insert(0, "./apps/gca-service")

from gca_core.glassbox import GlassBox
import init_system

class TestSecurityFix(unittest.TestCase):
    def test_glassbox_default_trust_remote_code_is_false(self):
        # Mock config without trust_remote_code
        mock_config = {
            'system': {'model_id': 'test-model', 'device': 'cpu'},
            'geometry': {'layer_idx': 12}
        }

        gb = GlassBox(config=mock_config)
        self.assertFalse(gb.trust_remote_code, "trust_remote_code should default to False")

    def test_glassbox_can_enable_trust_remote_code(self):
        # Mock config with trust_remote_code=True
        mock_config = {
            'system': {'model_id': 'test-model', 'device': 'cpu', 'trust_remote_code': True},
            'geometry': {'layer_idx': 12}
        }

        gb = GlassBox(config=mock_config)
        self.assertTrue(gb.trust_remote_code, "trust_remote_code should be True when configured")

    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_ensure_model_loading_uses_config_value(self, mock_tokenizer, mock_model):
        mock_config = {
            'system': {'model_id': 'test-model', 'device': 'cpu', 'trust_remote_code': False},
            'geometry': {'layer_idx': 12}
        }

        gb = GlassBox(config=mock_config)
        # Mock self.dtype
        gb.dtype = "float32"
        gb._ensure_model_loaded()

        # Verify tokenizer call
        mock_tokenizer.assert_called()
        args, kwargs = mock_tokenizer.call_args
        self.assertFalse(kwargs.get('trust_remote_code'), "Tokenizer should be called with trust_remote_code=False")

        # Verify model call
        mock_model.assert_called()
        args, kwargs = mock_model.call_args
        self.assertFalse(kwargs.get('trust_remote_code'), "Model should be called with trust_remote_code=False")

    @patch('transformers.AutoModelForCausalLM.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_init_system_uses_config_value(self, mock_tokenizer, mock_model):
        # Setup init_system.CFG
        init_system.CFG = {
            'system': {'model_id': 'test-model', 'trust_remote_code': False, 'dtype': 'float32'},
            'geometry': {'layer_idx': 0, 'basis_size': 32, 'assets_dir': './assets'}
        }

        # Mocking PCA and other things needed by map_brain
        with patch('sklearn.decomposition.PCA'), patch('torch.save'), patch('os.makedirs'):
             try:
                init_system.map_brain()
             except Exception as e:
                # We expect some errors because we mocked too much, but we only care about the call
                pass

        # Verify tokenizer call in init_system
        mock_tokenizer.assert_called()
        args, kwargs = mock_tokenizer.call_args
        self.assertFalse(kwargs.get('trust_remote_code'), "init_system Tokenizer should use trust_remote_code=False")

        # Verify model call in init_system
        mock_model.assert_called()
        args, kwargs = mock_model.call_args
        self.assertFalse(kwargs.get('trust_remote_code'), "init_system Model should use trust_remote_code=False")

if __name__ == '__main__':
    unittest.main()
