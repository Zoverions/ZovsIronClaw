import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("GCA.CronReader")

class CronReader:
    """
    Reads the OpenClaw Cron schedule from the shared state directory.
    This provides direct, efficient access to the automation layer.
    """
    def __init__(self):
        # Resolve Cron Store Path
        # Default: ~/.openclaw/cron/jobs.json
        # Override: OPENCLAW_STATE_DIR env var

        state_dir = os.environ.get("OPENCLAW_STATE_DIR")
        if state_dir:
            self.cron_path = Path(state_dir) / "cron" / "jobs.json"
        else:
            self.cron_path = Path.home() / ".openclaw" / "cron" / "jobs.json"

        logger.info(f"CronReader initialized. Watching: {self.cron_path}")

    def get_upcoming_jobs(self, window_minutes: int = 15) -> List[Dict]:
        """
        Returns a list of jobs scheduled to run within the next `window_minutes`.
        """
        if not self.cron_path.exists():
            logger.debug(f"Cron store not found at {self.cron_path}")
            return []

        try:
            with open(self.cron_path, 'r', encoding='utf-8') as f:
                # Use standard json load (assuming OpenClaw writes compatible JSON)
                data = json.load(f)

            jobs = data.get("jobs", [])
            if not jobs:
                return []

            upcoming = []
            now_ms = time.time() * 1000
            window_ms = window_minutes * 60 * 1000
            limit_ms = now_ms + window_ms

            for job in jobs:
                if not job.get("enabled", True):
                    continue

                state = job.get("state", {})
                next_run = state.get("nextRunAtMs")

                if next_run:
                    # Check if it's in the future and within window
                    # Also include slightly overdue jobs (up to 5 mins past) just in case
                    if (now_ms - 5 * 60 * 1000) <= next_run <= limit_ms:
                        upcoming.append(self._format_job(job, next_run))

            return upcoming

        except Exception as e:
            logger.error(f"Failed to read cron store: {e}")
            return []

    def _format_job(self, job: Dict, next_run_ms: float) -> Dict:
        """Helper to format job for consumption."""
        return {
            "id": job.get("id"),
            "name": job.get("name", "Unnamed Task"),
            "next_run_ms": next_run_ms,
            "next_run_iso": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(next_run_ms / 1000)),
            "payload": job.get("payload", {})
        }
