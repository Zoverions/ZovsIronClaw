
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules['torch'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['numpy'] = MagicMock()

import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../gca-service')))

# Import after mocking
from gca_core.glassbox import GlassBox
from gca_core.memory_advanced import BiomimeticMemory
from gca_core.memory import IsotropicMemory

class TestComponents(unittest.TestCase):
    def test_biomimetic_memory_init(self):
        """
        Verify BiomimeticMemory initializes correctly with lazy GlassBox,
        fetching hidden_size via config without loading model.
        """
        # Mock GlassBox config
        config = {
            'system': {'model_id': 'test-model', 'device': 'cpu', 'dtype': 'float32'},
            'geometry': {'layer_idx': 0}
        }

        # Init GlassBox
        gb = GlassBox(config=config)

        # Mock base memory
        base_mem = MagicMock()
        base_mem.storage_path = MagicMock()
        # Mock Path / operator
        base_mem.storage_path.__truediv__.return_value = MagicMock()
        base_mem.storage_path.__truediv__.return_value.exists.return_value = False # insights file

        # Mock AutoConfig loading in GlassBox.get_hidden_size
        # We need to mock 'transformers.AutoConfig' BEFORE GlassBox attempts to use it in get_hidden_size
        # But get_hidden_size imports it locally: "from transformers import AutoConfig"
        # Since we mocked sys.modules['transformers'], that import will return our mock.

        mock_transformers = sys.modules['transformers']
        mock_config_cls = mock_transformers.AutoConfig.from_pretrained
        mock_config = MagicMock()
        mock_config.hidden_size = 2048
        mock_config_cls.return_value = mock_config

        print("Initializing BiomimeticMemory...")
        try:
            bio_mem = BiomimeticMemory(gb, base_mem)
        except Exception as e:
            self.fail(f"Initialization failed: {e}")

        # Verify hidden_size was fetched from config
        mock_config_cls.assert_called_once()

        # Verify basis creation used correct dimension
        base_mem.get_or_create_basis.assert_called_with(2048, 32)

        # Verify model is STILL lazy (None)
        self.assertIsNone(gb.model, "Model should still be None")
        print("PASS: BiomimeticMemory initialized without loading model.")

if __name__ == '__main__':
    unittest.main()
