import logging
import threading
import time
import torch
from pathlib import Path
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

        # Determine Goal Path
        # Typically run from gca-service/api_server.py, so parent is gca-service
        # We need to find .agent/prompts/GOAL.md relative to project root
        # If __file__ is gca-service/gca_core/pulse.py -> ../../../.agent/prompts/GOAL.md
        self.goal_path = Path(__file__).parents[2] / ".agent" / "prompts" / "GOAL.md"
        self.cached_goal_text = "Focus, productivity, code generation, precision."
        self._load_goal()

    def _load_goal(self):
        """Loads goal text from file if available."""
        if self.goal_path.exists():
            try:
                with open(self.goal_path, 'r') as f:
                    content = f.read()
                    # Simple heuristic: Use the whole file as context
                    # or extract specific sections. For now, use the whole file.
                    self.cached_goal_text = content.strip()
                logger.info(f"[💓] Goal loaded from {self.goal_path}")
            except Exception as e:
                logger.error(f"[💓] Failed to load goal file: {e}")
        else:
            logger.warning(f"[💓] Goal file not found at {self.goal_path}. Using default.")

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

        # 2. Get Goal Vector
        # Refresh goal periodically? For now, use cached.
        goal_vec = self.glassbox.get_activation(self.cached_goal_text).to(device)

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
            logger.warning(f"[💓] HIGH ENTROPY DETECTED ({entropy:.2f}). Triggering Active Inference.")
            self._trigger_intervention(entropy)

    def _trigger_intervention(self, entropy_score):
        """
        Injects a correction vector via callback using Active Inference principles.
        Minimizing free energy -> maximizing alignment with the goal.
        """
        if self.intervention_callback:
            # Active Inference: The correction is not just a warning, but a restatement of the goal
            # weighted by the deviation (entropy).

            # We construct a 'Correction' Soul Prompt
            # In a full vector system, we would calculate the difference vector.
            # Here, we reinforce the semantic goal.

            correction_msg = (
                f"[SYSTEM PULSE | Entropy: {entropy_score:.2f}] "
                f"Active Inference Intervention: Re-align with Goal:\n"
                f"\"{self.cached_goal_text[:200]}...\""
            )
            try:
                self.intervention_callback(correction_msg)
            except Exception as e:
                logger.error(f"Intervention callback failed: {e}")

# Alias for backward compatibility if needed, though we will update usages.
Pulse = PulseSystem
