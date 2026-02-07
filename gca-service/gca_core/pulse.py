import logging
import threading
import time
import torch
from typing import Callable, Optional

logger = logging.getLogger("GCA.Pulse")

class PulseSystem:
    def __init__(self, memory_system, glassbox, check_interval: int = 60):
        self.memory = memory_system
        self.glassbox = glassbox
        self.interval = check_interval
        self._stop_event = threading.Event()
        self.current_entropy = 0.0
        self.intervention_callback: Optional[Callable] = None
        self.thread = None

    def start(self):
        """Starts the background heartbeat."""
        if self.thread and self.thread.is_alive():
            logger.warning("[💓] Pulse System is already running.")
            return

        logger.info("[💓] Pulse System Online.")
        self.thread = threading.Thread(target=self._beat_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the background heartbeat."""
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("[💓] Pulse System Stopped.")

    def set_intervention_callback(self, cb: Callable):
        self.intervention_callback = cb

    def _beat_loop(self):
        while not self._stop_event.is_set():
            try:
                self._check_vitals()
            except Exception as e:
                logger.error(f"[💓] Pulse Error: {e}", exc_info=True)
            time.sleep(self.interval)

    def _check_vitals(self):
        """
        1. Measure current cognitive entropy (User State vs Goal).
        2. Trigger intervention if divergence is high.
        """
        # 1. Get current user state vector from Short Term Memory
        # The bio_mem might not have 'working_memory' attribute directly if it's the advanced version.
        # Let's check compatibility. Assuming standard interface or list access.
        if not hasattr(self.memory, "working_memory") or not self.memory.working_memory:
            return # Mind is empty

        # Get the latest thought vector.
        # If working_memory is a list of objects with .vector attribute:
        try:
            current_thought = self.memory.working_memory[-1].vector
        except (IndexError, AttributeError):
            return

        if current_thought is None:
            return

        # Ensure tensor is on correct device
        device = self.glassbox.device
        current_thought = current_thought.to(device)

        # 2. Get Goal Vector (Assuming loaded in Memory LTM or Config)
        # For MVP, we synthesize "Productivity" if not available elsewhere
        # Ideally this comes from GOAL.md or similar, but per instructions:
        goal_text = "Focus, productivity, code generation, precision."
        goal_vec = self.glassbox.get_activation(goal_text).to(device)

        # 3. Calculate Divergence (Cosine Distance)
        # Cosine Sim: 1.0 = aligned, 0.0 = orthogonal, -1.0 = opposite
        # We need normalized vectors for dot product to be cosine similarity,
        # or use cosine_similarity function.
        sim = torch.nn.functional.cosine_similarity(current_thought, goal_vec, dim=0).item()

        # Entropy definition: 1.0 - sim.
        # If sim is 1.0 (perfect), entropy is 0.0.
        # If sim is 0.0 (orthogonal), entropy is 1.0.
        # If sim is -1.0 (opposite), entropy is 2.0.
        entropy = 1.0 - sim

        self.current_entropy = entropy
        logger.debug(f"[💓] Vital Check: Entropy {entropy:.3f}")

        # 4. Intervention Logic
        if entropy > 0.6: # Threshold
            logger.warning(f"[💓] HIGH ENTROPY DETECTED ({entropy:.2f}). Triggering Intervention.")
            self._trigger_intervention()

    def _trigger_intervention(self):
        """
        Injects a correction vector via callback.
        """
        if self.intervention_callback:
            # We construct a 'Correction' Soul Prompt
            correction_msg = "[SYSTEM PULSE] You are drifting. Re-align with the primary objective: Precision and Safety."
            try:
                self.intervention_callback(correction_msg)
            except Exception as e:
                logger.error(f"Intervention callback failed: {e}")

# Alias for backward compatibility if needed, though we will update usages.
Pulse = PulseSystem
