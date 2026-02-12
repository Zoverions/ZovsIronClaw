
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
sys.modules['networkx'] = MagicMock()

# Adjust path to import gca_core
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

from gca_core.optimizer import GCAOptimizer

class TestOptimizerCache(unittest.TestCase):
    def test_cache_limit(self):
        glassbox = MagicMock()
        memory = MagicMock()

        # Mock memory find_similar to always return something
        # find_similar returns list of (skill_name, score)
        memory.find_similar.return_value = [("MOCK_SKILL", 0.9)]

        optimizer = GCAOptimizer(glassbox, memory)

        # Ensure cache starts empty
        self.assertEqual(len(optimizer.intent_cache), 0)

        limit = 1000
        extra = 50

        for i in range(limit + extra):
            # Unique input each time
            input_text = f"intent_{i}"

            # Call route_intent
            optimizer.route_intent(input_text)

            # Check size periodically
            current_size = len(optimizer.intent_cache)
            if i >= limit:
                # With logic: if > 1000 delete one, then add new.
                # So max is 1001?
                # Let's trace:
                # 1000 items. Insert 1001st. Before insert, len=1000. Not > 1000. Insert. len=1001.
                # Next call. len=1001. > 1000. Delete one. len=1000. Insert. len=1001.
                # So size should be oscillating between 1000 and 1001.
                self.assertLessEqual(current_size, 1001)
                self.assertGreaterEqual(current_size, 1000)

        # print(f"Cache size after {limit+extra} inserts: {len(optimizer.intent_cache)}")

        # Check specific eviction
        # intent_0 should be gone (oldest)
        self.assertNotIn("intent_0", optimizer.intent_cache)
        # intent_1049 should be present (newest)
        self.assertIn(f"intent_{limit+extra-1}", optimizer.intent_cache)

    def test_lru_behavior(self):
        glassbox = MagicMock()
        memory = MagicMock()
        memory.find_similar.return_value = [("MOCK_SKILL", 0.9)]

        optimizer = GCAOptimizer(glassbox, memory)

        # Fill cache to limit (1000)
        limit = 1000
        for i in range(limit):
            optimizer.route_intent(f"key_{i}")

        # Cache has key_0 ... key_999.
        # Access key_0. This should move it to the end (newest).
        optimizer.route_intent("key_0")

        # Now cache is key_1 ... key_999, key_0.

        # Insert one more item (key_new).
        # This triggers eviction. The oldest is key_1.
        optimizer.route_intent("key_new")

        # key_1 should be evicted.
        self.assertNotIn("key_1", optimizer.intent_cache)

        # key_0 should still be there because it was recently accessed.
        self.assertIn("key_0", optimizer.intent_cache)
        self.assertIn("key_new", optimizer.intent_cache)

if __name__ == "__main__":
    unittest.main()
