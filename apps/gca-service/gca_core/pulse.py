import logging
import threading
import time
import torch
from pathlib import Path
from typing import Callable, Optional
from .active_inference import GenerativeModel, ActiveInferenceLoop
from .cron_reader import CronReader
from .horizon import HorizonScanner

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

        # Initialize Active Inference Components
        # Pass memory basis if available (Biomimetic Memory) to ensure dimensions match
        basis = getattr(self.memory, "basis", None)
        self.gen_model = GenerativeModel(self.glassbox, self.cached_goal_text, projection_matrix=basis)
        self.active_loop = ActiveInferenceLoop(self.gen_model)

        # Initialize Horizon Scanner
        self.horizon_scanner = HorizonScanner(self.glassbox)
        self._last_horizon_scan = 0

        # Initialize Cron Reader for Automation Awareness
        self.cron_reader = CronReader()

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

        # Update Generative Model if initialized
        if hasattr(self, 'gen_model'):
            self.gen_model.update_goal(self.cached_goal_text)

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
        1. Measure Free Energy (User State vs Goal).
        2. Check Schedule (Automation Awareness).
        3. Trigger intervention if necessary.
        """
        # 0. Check Schedule
        try:
            upcoming = self.cron_reader.get_upcoming_jobs()
            if upcoming:
                for job in upcoming:
                    minutes_due = int((job['next_run_ms'] - (time.time() * 1000)) / 60000)
                    msg = f"[SCHEDULE] Upcoming Task: '{job['name']}' due in {minutes_due} minutes."
                    logger.info(f"[💓] {msg}")
                    # Perceive the schedule
                    self.memory.perceive(text=msg)
        except Exception as e:
            logger.error(f"[💓] Schedule check failed: {e}")

        # 1. Get current user state vector from Short Term Memory
        if not hasattr(self.memory, "working_memory") or not self.memory.working_memory:
            return # Mind is empty

        try:
            # Check if it's new list-based memory or legacy
            if isinstance(self.memory.working_memory, list):
                 current_thought = self.memory.working_memory[-1].vector
            else:
                 # Assume it's the new EpisodicHippocampus which might expose a method or property
                 # For now, fallback to last item if iterable
                 current_thought = list(self.memory.working_memory)[-1].vector
        except (IndexError, AttributeError, TypeError):
            return

        if current_thought is None:
            return

        # 2. Compute Free Energy
        fe_state = self.active_loop.compute_free_energy(current_thought)
        self.current_entropy = fe_state.value

        # 3. Horizon Scan (Detecting the Emergent Horizon)
        memory_content = "Unknown Context"
        try:
             # Try to retrieve content from last engram
             if hasattr(self.memory, "working_memory") and self.memory.working_memory:
                 # Check if iterable/list
                 wm = list(self.memory.working_memory)
                 if wm:
                     memory_content = wm[-1].content
        except Exception:
             pass

        h_state = self.horizon_scanner.update(fe_state.value, memory_content)

        if h_state.is_critical_variance:
             current_time = time.time()
             if current_time - self._last_horizon_scan > 300: # 5 min cooldown
                 logger.warning("[HORIZON] Variance Alarm Active. Scanning for Geodesic...")
                 prediction = self.horizon_scanner.predict_geodesic()
                 self._last_horizon_scan = current_time

                 logger.info(f"[HORIZON] Prediction: {prediction}")
                 # Inject insight into memory
                 self.memory.perceive(f"[HORIZON ALERT] System Variance Critical. Future Projection: {prediction}")

        # 4. Intervention Logic
        if fe_state.mode != "homeostatic":
            logger.warning(f"[💓] Free Energy High ({fe_state.value:.2f} | {fe_state.mode}). Triggering Active Inference.")
            self._trigger_intervention(fe_state)

    def _trigger_intervention(self, fe_state):
        """
        Injects a correction vector via callback using Active Inference principles.
        """
        if self.intervention_callback:
            prefix = "Reflexive Correction" if fe_state.mode == "reflexive" else "STRATEGIC RE-PLANNING REQUIRED"

            correction_msg = (
                f"[SYSTEM PULSE | FreeEnergy: {fe_state.value:.2f}] "
                f"Active Inference ({prefix}): Re-align with Goal:\n"
                f"\"{self.cached_goal_text[:300]}...\""
            )
            try:
                self.intervention_callback(correction_msg)
            except Exception as e:
                logger.error(f"Intervention callback failed: {e}")

# Alias for backward compatibility if needed, though we will update usages.
Pulse = PulseSystem
