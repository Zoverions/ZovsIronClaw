import unittest
import sys
from pathlib import Path
import os
from unittest.mock import MagicMock

# Mock torch and other heavy dependencies
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['accelerate'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['einops'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['qwen_vl_utils'] = MagicMock()
sys.modules['networkx'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['textblob'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.decomposition'] = MagicMock()

# Add gca-service to path
# This file is in apps/gca-service/tests/
# We want to add apps/gca-service to sys.path
SERVICE_DIR = Path(__file__).parents[1].resolve()
sys.path.insert(0, str(SERVICE_DIR))

from gca_core.tools import ToolRegistry

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_bash_tool_exists(self):
        """Verify that the bash tool is registered with correct parameters."""
        tool = self.registry.get("bash")
        self.assertIsNotNone(tool, "Bash tool should be registered")
        self.assertEqual(tool.name, "bash")
        self.assertEqual(tool.intent_vector, "SYSTEM")

        # Verify params
        params = tool.parameters
        props = params.get("properties", {})

        self.assertIn("command", props)
        self.assertIn("pty", props)
        self.assertIn("workdir", props)
        self.assertIn("background", props)
        self.assertIn("timeout", props)

        # Verify required
        required = params.get("required", [])
        self.assertIn("command", required)

    def test_tool_list_contains_bash(self):
        """Verify bash tool is in the list of all tools."""
        tools = self.registry.list_tools()
        names = [t.name for t in tools]
        self.assertIn("bash", names)

    def test_tool_schema_format(self):
        """Verify the schema format for OpenAI compatibility."""
        tool = self.registry.get("bash")
        schema = tool.to_schema()

        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "bash")
        self.assertTrue("description" in schema["function"])
        self.assertTrue("parameters" in schema["function"])

if __name__ == '__main__':
    unittest.main()
