import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
# import pytest

# Add path
sys.path.insert(0, os.path.abspath("apps/gca-service"))

# MOCK EVERYTHING before importing api_server
# We need to mock the classes that are instantiated at module level
mock_glassbox = MagicMock()
mock_glassbox.device = "cpu"
mock_glassbox.model_name = "mock-model"

sys.modules["gca_core.glassbox"] = MagicMock(GlassBox=MagicMock(return_value=mock_glassbox))
sys.modules["gca_core.resource_manager"] = MagicMock(ResourceManager=MagicMock(return_value=MagicMock(get_active_config=lambda: {})))
sys.modules["gca_core.moral"] = MagicMock()
sys.modules["gca_core.optimizer"] = MagicMock()
sys.modules["gca_core.tools"] = MagicMock()
sys.modules["gca_core.memory"] = MagicMock()
sys.modules["gca_core.resonance"] = MagicMock()
sys.modules["gca_core.qpt"] = MagicMock()
sys.modules["gca_core.arena"] = MagicMock()
sys.modules["gca_core.memory_advanced"] = MagicMock()
sys.modules["gca_core.perception"] = MagicMock()
sys.modules["gca_core.observer"] = MagicMock()
sys.modules["gca_core.pulse"] = MagicMock()
sys.modules["gca_core.causal_flow"] = MagicMock()
sys.modules["gca_core.swarm"] = MagicMock()
sys.modules["gca_core.reflective_logger"] = MagicMock()
sys.modules["gca_core.soul_loader"] = MagicMock()
sys.modules["gca_core.security"] = MagicMock()
sys.modules["gca_core.blockchain"] = MagicMock()
sys.modules["gca_core.security_guardrail"] = MagicMock()
sys.modules["gca_core.dual_ethics"] = MagicMock()
sys.modules["dreamer"] = MagicMock()

# Now import
import api_server
from fastapi import UploadFile

async def test_transcribe_vulnerability():
    # Setup
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.wav"
    mock_file.read = AsyncMock(return_value=b"fake_audio_content")

    # We need to mock run_in_threadpool because it's imported in api_server
    # And mock save_upload_to_tmp to avoid actual file creation and dependency on run_in_threadpool return value
    with patch("api_server.run_in_threadpool", new_callable=AsyncMock) as mock_run, \
         patch("api_server.save_upload_to_tmp", new_callable=AsyncMock) as mock_save:

        mock_run.return_value = "transcribed text"
        mock_save.return_value = "/tmp/fake_path.wav"

        # Call the endpoint function directly
        print("Calling transcribe_media...")
        response = await api_server.transcribe_media(file=mock_file)

        # Ensure save_upload_to_tmp was called
        mock_save.assert_called_once_with(mock_file)

        # ASSERT FIX: read() should NOT be called
        print(f"mock_file.read called: {mock_file.read.called}")
        if mock_file.read.called:
            print("FAILURE: file.read() was called! Fix not working.")
            exit(1)
        else:
            print("SUCCESS: file.read() was NOT called. Streaming usage confirmed.")
            # Verify save_upload_to_tmp logic (indirectly via run_in_threadpool calls)
            # We expect run_in_threadpool to be called with shutil.copyfileobj
            # run_in_threadpool was mocked, so we can check its calls
            pass

if __name__ == "__main__":
    asyncio.run(test_transcribe_vulnerability())
