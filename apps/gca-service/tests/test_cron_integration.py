import unittest
import tempfile
import shutil
import os
import json
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 1. Setup global mocks BEFORE imports
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['textblob'] = MagicMock()
sys.modules['yaml'] = MagicMock()
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
sys.modules['qwen_vl_utils.process_vision_info'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()

# 2. Add gca-service to path
SERVICE_DIR = Path(__file__).parents[1].resolve()
sys.path.insert(0, str(SERVICE_DIR))

# 3. Import modules under test
from gca_core.cron_reader import CronReader
from gca_core.pulse import PulseSystem

class TestCronIntegration(unittest.TestCase):
    def setUp(self):
        # Create temp dir for cron store
        self.test_dir = tempfile.mkdtemp()
        self.cron_dir = Path(self.test_dir) / "cron"
        self.cron_dir.mkdir(parents=True)
        self.jobs_file = self.cron_dir / "jobs.json"

        # Set ENV var
        os.environ["OPENCLAW_STATE_DIR"] = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if "OPENCLAW_STATE_DIR" in os.environ:
            del os.environ["OPENCLAW_STATE_DIR"]

    def test_cron_reader_reads_job(self):
        # Write job
        now_ms = time.time() * 1000
        next_run = now_ms + 60000 # 1 minute from now

        job = {
            "id": "job1",
            "name": "Test Job",
            "enabled": True,
            "state": {
                "nextRunAtMs": next_run
            }
        }

        with open(self.jobs_file, "w") as f:
            json.dump({"jobs": [job]}, f)

        reader = CronReader()
        upcoming = reader.get_upcoming_jobs()

        self.assertEqual(len(upcoming), 1)
        self.assertEqual(upcoming[0]["id"], "job1")
        # Allow small floating point diff
        self.assertAlmostEqual(upcoming[0]["next_run_ms"], next_run, delta=1.0)

    def test_pulse_perceives_job(self):
        # Mock Memory and GlassBox
        mock_memory = MagicMock()
        mock_glassbox = MagicMock()

        # Write job
        now_ms = time.time() * 1000
        next_run = now_ms + 120000 # 2 minutes from now

        job = {
            "id": "job2",
            "name": "Pulse Job",
            "enabled": True,
            "state": {
                "nextRunAtMs": next_run
            }
        }

        with open(self.jobs_file, "w") as f:
            json.dump({"jobs": [job]}, f)

        # Init Pulse
        pulse = PulseSystem(mock_memory, mock_glassbox)

        # Mock internal components to prevent actual computation
        pulse.active_loop = MagicMock()
        pulse.active_loop.compute_free_energy.return_value = MagicMock(value=0.1, mode="homeostatic")

        # Mock memory state to prevent crash
        mock_memory.working_memory = [MagicMock(vector=None)]

        # Force check vitals
        pulse._check_vitals()

        # Verify perceive was called
        mock_memory.perceive.assert_called()
        call_args = mock_memory.perceive.call_args
        # perceive(text=...) or perceive("text")
        # args[0] or kwargs['text']

        text_arg = call_args.kwargs.get('text')
        if not text_arg and call_args.args:
            text_arg = call_args.args[0]

        self.assertIn("[SCHEDULE] Upcoming Task: 'Pulse Job'", text_arg)

if __name__ == '__main__':
    unittest.main()
