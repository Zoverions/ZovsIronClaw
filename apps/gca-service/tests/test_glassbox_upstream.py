import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies before import
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()

# Add apps/gca-service to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import GlassBox after mocking
try:
    from gca_core.glassbox import GlassBox
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from gca_core.glassbox import GlassBox

class TestGlassBoxUpstream(unittest.TestCase):
    def setUp(self):
        # Clear relevant env vars
        if "GCA_UPSTREAM_URL" in os.environ:
            del os.environ["GCA_UPSTREAM_URL"]
        if "GCA_UPSTREAM_KEY" in os.environ:
            del os.environ["GCA_UPSTREAM_KEY"]
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

    @patch("gca_core.glassbox.requests.post")
    def test_upstream_url_override(self, mock_post):
        # Setup
        os.environ["GCA_UPSTREAM_URL"] = "http://localhost:11434/v1/chat/completions"
        os.environ["GCA_UPSTREAM_KEY"] = "ollama"

        # Init GlassBox with a model name that is normally local
        gb = GlassBox(model_name="Qwen/Qwen2.5-0.5B-Instruct")

        # Verify it detected API mode due to upstream URL
        self.assertTrue(gb.is_api_model, "Should be in API mode when GCA_UPSTREAM_URL is set")

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response from Upstream"}}]
        }
        mock_post.return_value = mock_response

        # Generate
        response = gb.generate_steered("Test prompt")

        self.assertEqual(response, "Response from Upstream")

        # Verify request
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:11434/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "Qwen/Qwen2.5-0.5B-Instruct")
        self.assertIn("Authorization", kwargs["headers"])

    @patch("gca_core.glassbox.requests.post")
    def test_model_override(self, mock_post):
        # Setup
        os.environ["GCA_UPSTREAM_URL"] = "http://proxy:8000/v1"
        gb = GlassBox(model_name="default-model")

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_post.return_value = mock_response

        # Generate with model override
        gb.generate_steered("Test", model="gpt-4-override")

        # Verify request payload
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["model"], "gpt-4-override")

    @patch("gca_core.glassbox.requests.post")
    def test_default_openai(self, mock_post):
        # Setup
        os.environ["OPENAI_API_KEY"] = "sk-test"
        # Init with GPT model
        gb = GlassBox(model_name="gpt-3.5-turbo")

        self.assertTrue(gb.is_api_model)

        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OpenAI Response"}}]
        }
        mock_post.return_value = mock_response

        gb.generate_steered("Test")

        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(kwargs["json"]["model"], "gpt-3.5-turbo")

if __name__ == '__main__':
    unittest.main()
