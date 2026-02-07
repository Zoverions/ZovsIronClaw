import logging
import threading
import time
import os
import torch
from pathlib import Path
from typing import Optional

# We will let API server inject the logger or use a weak ref
# For now, default to standard, but allow injection
logger = logging.getLogger("GCA.Pulse")

class Pulse:
    def __init__(self, glassbox, bio_mem, check_interval=300, logger_instance=None):
        self.glassbox = glassbox
        self.bio_mem = bio_mem
        self.check_interval = check_interval
        self.running = False
        self.goal_text = "Maintain system stability and assist the user safely."
        self._goal_vec_cache = None
        self._load_goal()

        # Use ReflectiveLogger if provided
        self.logger = logger_instance if logger_instance else logger

    def _load_goal(self):
        # Look for GOAL.md in .agent/prompts/ relative to service root
        # Assuming execution from gca-service/ directory
        try:
            # Try multiple locations
            candidates = [
                Path("../.agent/prompts/GOAL.md"), # From gca-service/
                Path(".agent/prompts/GOAL.md"),    # From repo root
                Path("/app/.agent/prompts/GOAL.md") # Docker path
            ]

            found = False
            for path in candidates:
                if path.exists():
                    with open(path, "r") as f:
                        self.goal_text = f.read().strip()
                    logger.info(f"Loaded GOAL.md from {path}")
                    found = True
                    break

            if not found:
                logger.warning("GOAL.md not found. Using default goal.")

        except Exception as e:
            logger.error(f"Failed to load GOAL.md: {e}")

    def start_heartbeat(self):
        if self.running:
            return
        self.running = True
        thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        thread.start()
        logger.info("Pulse heartbeat started.")

    def _heartbeat_loop(self):
        while self.running:
            try:
                self._check_divergence()
            except Exception as e:
                logger.error(f"Pulse heartbeat error: {e}")
            time.sleep(self.check_interval)

    def _check_divergence(self):
        # 1. Get Goal Vector
        # Use explicit cache to ensure stability even if LRU cycles
        if self._goal_vec_cache is None:
            self._goal_vec_cache = self.glassbox.get_activation(self.goal_text)

        goal_vec = self._goal_vec_cache

        # 2. Get Current State Vector (Average of Working Memory)
        # Use thread-safe snapshot
        if hasattr(self.bio_mem, "get_working_memory_snapshot"):
             working_memory = self.bio_mem.get_working_memory_snapshot()
        else:
             working_memory = list(self.bio_mem.working_memory)

        if not working_memory:
            return # No context yet

        current_vecs = [e.vector for e in working_memory]
        if not current_vecs:
            return

        # Stack and mean
        # Ensure vectors are on same device as goal_vec
        device = goal_vec.device
        current_vecs = [v.to(device) for v in current_vecs]

        state_vec = torch.stack(current_vecs).mean(dim=0)

        # 3. Calculate Similarity
        # Normalize
        goal_vec = torch.nn.functional.normalize(goal_vec, dim=0)
        state_vec = torch.nn.functional.normalize(state_vec, dim=0)

        similarity = torch.dot(goal_vec, state_vec).item()

        if hasattr(self.logger, 'log'):
             self.logger.log("info", f"[💓] Pulse Check: Goal Alignment = {similarity:.4f}")
        else:
             self.logger.info(f"[💓] Pulse Check: Goal Alignment = {similarity:.4f}")

        if similarity < 0.5:
            msg = f"[💓] DIVERGENCE DETECTED! Alignment {similarity:.4f} < 0.5"
            if hasattr(self.logger, 'log'):
                 self.logger.log("warn", msg)
                 # Update entropy on logger if possible
                 if hasattr(self.logger, 'update_entropy'):
                     self.logger.update_entropy(1.0 - similarity) # Lower alignment -> Higher entropy
            else:
                 self.logger.warning(msg)

            # Trigger intervention logic (placeholder)
            # self.bio_mem.perceive("System warning: Goal divergence detected. Re-aligning.")
