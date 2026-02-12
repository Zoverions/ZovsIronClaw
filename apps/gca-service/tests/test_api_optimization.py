
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
import asyncio

# 1. Mock heavy external dependencies BEFORE importing api_server
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['numpy'] = MagicMock() # Added numpy
sys.modules['textblob'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()
sys.modules['networkx'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()
sys.modules['python_multipart'] = MagicMock()

# Mock Pydantic
class MockBaseModel:
    def __init__(self, **kwargs):
        pass
    def dict(self): return {}
    def json(self): return "{}"
    @classmethod
    def parse_obj(cls, x): return cls()

pydantic_mock = MagicMock()
pydantic_mock.BaseModel = MockBaseModel
pydantic_mock.Field = MagicMock(return_value=None)
sys.modules['pydantic'] = pydantic_mock

# Mock gca_core components
# Note: api_server imports them like `from gca_core.glassbox import GlassBox`
# We need to mock the MODULES so imports work.
# And inside those modules, the CLASSES.

# Helper to mock a module with a class
def mock_module_class(module_name, class_name):
    mod = MagicMock()
    cls = MagicMock()
    setattr(mod, class_name, cls)
    sys.modules[module_name] = mod
    return cls

glassbox_cls = mock_module_class('gca_core.glassbox', 'GlassBox')
res_man_cls = mock_module_class('gca_core.resource_manager', 'ResourceManager')
moral_cls = mock_module_class('gca_core.moral', 'MoralKernel')
opt_cls = mock_module_class('gca_core.optimizer', 'GCAOptimizer')
tools_cls = mock_module_class('gca_core.tools', 'Tool') # And ToolRegistry?
mem_cls = mock_module_class('gca_core.memory', 'IsotropicMemory')
res_eng_cls = mock_module_class('gca_core.resonance', 'ResonanceEngine')
qpt_cls = mock_module_class('gca_core.qpt', 'QuaternionArchitect')
arena_cls = mock_module_class('gca_core.arena', 'ArenaProtocol')
bio_mem_cls = mock_module_class('gca_core.memory_advanced', 'BiomimeticMemory')
perc_cls = mock_module_class('gca_core.perception', 'PerceptionSystem')
obs_cls = mock_module_class('gca_core.observer', 'Observer')
pulse_cls = mock_module_class('gca_core.pulse', 'PulseSystem')
causal_cls = mock_module_class('gca_core.causal_flow', 'CausalFlowEngine')
swarm_cls = mock_module_class('gca_core.swarm', 'SwarmNetwork')
log_cls = mock_module_class('gca_core.reflective_logger', 'ReflectiveLogger')
sec_cls = mock_module_class('gca_core.security', 'SecurityManager')
chain_cls = mock_module_class('gca_core.blockchain', 'Blockchain') # Also Transaction
guard_cls = mock_module_class('gca_core.security_guardrail', 'SecurityGuardrail')
soul_cls = mock_module_class('gca_core.soul_loader', 'SoulLoader')
dreamer_cls = mock_module_class('dreamer', 'DeepDreamer')

# Need to handle specific imports in api_server like `from gca_core.moral import MoralKernel, Action, EntropyClass`
sys.modules['gca_core.moral'].Action = MagicMock()
sys.modules['gca_core.moral'].EntropyClass = MagicMock()
sys.modules['gca_core.blockchain'].Transaction = MagicMock()
sys.modules['gca_core.tools'].ToolRegistry = MagicMock()
sys.modules['gca_core.soul_loader'].get_soul_loader = MagicMock()

# Configure PulseSystem mock instance
pulse_instance = MagicMock()
pulse_instance.cached_goal_text = "MOCK_GOAL_TEXT"
pulse_instance.current_entropy = 0.5
pulse_instance.horizon_scanner.get_status.return_value = {}
pulse_cls.return_value = pulse_instance

# Configure other mocks to avoid attribute errors during init
res_man_cls.return_value.get_active_config.return_value = {'active_profile': 'test'}
res_man_cls.return_value.profile = 'test' # needed for swarm
sec_cls.return_value.private_key = "mock_key"
sec_cls.return_value.get_public_key_b64.return_value = "mock_pub"
chain_cls.return_value.verify_identity.return_value = True
swarm_cls.return_value.mesh.agent_id = "test_agent"
swarm_cls.return_value.mesh.get_active_nodes.return_value = []
chain_cls.return_value.chain = []
chain_cls.return_value.pending_transactions = []
mem_cls.return_value.list_vectors.return_value = []

# Mock FastAPI
fastapi_mock = MagicMock()
sys.modules['fastapi'] = fastapi_mock
sys.modules['fastapi.middleware.cors'] = MagicMock()

# Mock concurrency properly
async def mock_run_in_threadpool(func, *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)

fastapi_concurrency_mock = MagicMock()
fastapi_concurrency_mock.run_in_threadpool = mock_run_in_threadpool
sys.modules['fastapi.concurrency'] = fastapi_concurrency_mock

# Also api_server does `from fastapi import FastAPI, HTTPException...`

# Mock FastAPI app decorator behavior so functions aren't replaced by Mocks
class MockApp:
    def post(self, path, **kwargs):
        def decorator(func):
            return func
        return decorator
    def get(self, path, **kwargs):
        def decorator(func):
            return func
        return decorator
    def add_middleware(self, *args, **kwargs):
        pass

fastapi_mock.FastAPI = MagicMock(return_value=MockApp())

class MockHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

fastapi_mock.HTTPException = MockHTTPException
fastapi_mock.UploadFile = MagicMock
fastapi_mock.File = MagicMock()
fastapi_mock.Form = MagicMock()
fastapi_mock.Request = MagicMock()

# Adjust path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))

# Import api_server
try:
    import api_server
except ImportError as e:
    print(f"ImportError: {e}")
    raise
except Exception as e:
    print(f"Init Error: {e}")
    raise

class TestAPIOptimization(unittest.TestCase):
    def test_observe_goal_cache(self):
        # We need to call the endpoint function `observe_user`
        # But api_server creates the app.
        # We can access `api_server.observe_user` directly if it's defined.
        # It is decorated with @app.post.

        # Verify pulse mock is injected
        self.assertEqual(api_server.pulse.cached_goal_text, "MOCK_GOAL_TEXT")

        # Verify observer mock
        api_server.observer.analyze_input.return_value = {'state': 'calm', 'description': 'desc'}
        api_server.observer.check_goal_alignment.return_value = 0.9

        # Mock file
        file_mock = AsyncMock()
        file_mock.read.return_value = b"data"
        file_mock.filename = "test.jpg"

        # Run
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # api_server.observe_user is an async function
            response = loop.run_until_complete(
                api_server.observe_user(file=file_mock, modality="vision")
            )

            # Assertions
            api_server.observer.analyze_input.assert_called()
            # Most important: check_goal_alignment called with MOCK_GOAL_TEXT
            api_server.observer.check_goal_alignment.assert_called_with('calm', "MOCK_GOAL_TEXT")

            print("SUCCESS: observe_user used cached goal text.")

        finally:
            loop.close()

if __name__ == "__main__":
    unittest.main()
