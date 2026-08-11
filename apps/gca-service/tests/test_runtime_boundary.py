from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SERVICE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_DIR.parents[1]

spec = importlib.util.spec_from_file_location(
    "runtime_boundary", SERVICE_DIR / "runtime_boundary.py"
)
runtime_boundary = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(runtime_boundary)


class RuntimeBoundaryUnitTests(unittest.TestCase):
    def test_experimental_runtime_is_explicit_opt_in(self):
        self.assertFalse(runtime_boundary.env_flag("X", {}))
        self.assertFalse(runtime_boundary.env_flag("X", {"X": "0"}))
        self.assertTrue(runtime_boundary.env_flag("X", {"X": "true"}))
        self.assertTrue(runtime_boundary.env_flag("X", {"X": "1"}))

    def test_api_key_fails_closed(self):
        self.assertEqual(runtime_boundary.api_key_status(None, None), 503)
        self.assertEqual(runtime_boundary.api_key_status("expected", None), 403)
        self.assertEqual(runtime_boundary.api_key_status("expected", "wrong"), 403)
        self.assertEqual(runtime_boundary.api_key_status("expected", "expected"), 200)

    def test_configured_key_has_no_default(self):
        self.assertIsNone(runtime_boundary.configured_api_key({}, {}))
        self.assertEqual(
            runtime_boundary.configured_api_key(
                {"security": {"api_key": "config-key"}}, {}
            ),
            "config-key",
        )
        self.assertEqual(
            runtime_boundary.configured_api_key(
                {"security": {"api_key": "config-key"}},
                {"GCA_API_KEY": "env-key"},
            ),
            "env-key",
        )

    def test_network_and_governance_mutations_default_off(self):
        for path in runtime_boundary.EXPERIMENTAL_SIDE_EFFECT_PATHS:
            self.assertFalse(runtime_boundary.side_effect_allowed(path, False), path)
            self.assertTrue(runtime_boundary.side_effect_allowed(path, True), path)
        self.assertTrue(runtime_boundary.side_effect_allowed("/v1/reason", False))


class SourceContractTests(unittest.TestCase):
    def test_provider_requires_api_key_and_does_not_mint_authority_token(self):
        provider = (REPO_ROOT / "extensions/gca-brain/index.ts").read_text()
        self.assertIn("'X-GCA-API-Key': apiKey", provider)
        self.assertIn("GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS", provider)
        self.assertIn("GCA_API_KEY is not configured", provider)
        self.assertNotIn("_gca_token", provider)

    def test_api_server_has_global_control_auth_and_default_off_runtime(self):
        source = (SERVICE_DIR / "api_server.py").read_text()
        self.assertIn("@app.middleware(\"http\")", source)
        self.assertIn("EXPERIMENTAL_RUNTIME_ENABLED", source)
        self.assertIn("side_effect_allowed", source)
        self.assertIn("configured_api_key", source)
        self.assertNotIn("swarm_network.mesh.start()\n\n# Late broadcast", source)

    def test_reason_memory_broadcast_is_guarded(self):
        source = (SERVICE_DIR / "api_server.py").read_text()
        self.assertIn(
            "if EXPERIMENTAL_RUNTIME_ENABLED and new_memories:",
            source,
        )

    def test_service_tool_calls_are_default_off(self):
        source = (SERVICE_DIR / "api_server.py").read_text()
        self.assertIn(
            'EXPERIMENTAL_TOOL_CALLS_ENABLED = env_flag("GCA_ENABLE_EXPERIMENTAL_TOOL_CALLS")',
            source,
        )
        self.assertGreaterEqual(
            source.count("if not EXPERIMENTAL_TOOL_CALLS_ENABLED:"),
            2,
        )
        self.assertIn("tool_suggestion_suppressed", source)
        self.assertIn("Suggested tool call", source)


if __name__ == "__main__":
    unittest.main()
