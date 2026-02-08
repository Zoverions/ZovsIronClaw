import logging
import time
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
from gca_core.secure_storage import SecureStorage

logger = logging.getLogger("GCA.EvolutionEngine")

class EvolutionEngine:
    """
    Manages the evolving 'Soul' of the digital entity.
    Tracks personality shifts, ethical alignment, and experience over time.
    All state is stored in a high-security encrypted format.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.state_file = self.storage_path / "soul_state.enc"
        self.secure_storage = SecureStorage()

        # Default state
        self.state = {
            "epoch": 0,
            "creation_time": time.time(),
            "last_update": time.time(),
            "experience_points": 0,
            "alignment_score": 1.0, # 1.0 = Perfectly Aligned
            "traits": {}, # e.g. {"curious": 0.5}
            "focus_areas": [],
            "ethical_drift_history": []
        }

        self._load_state()

    def _load_state(self):
        """Load encrypted state if it exists."""
        loaded = self.secure_storage.load_json(self.state_file)
        if loaded:
            self.state.update(loaded)
            logger.info(f"Loaded soul state (Epoch {self.state['epoch']})")
        else:
            logger.info("Initialized new soul state")
            self._save_state()

    def _save_state(self):
        """Save state securely."""
        self.state["last_update"] = time.time()
        self.secure_storage.save_json(self.state_file, self.state)

    def evolve(self, new_memories: List[str]):
        """
        Update the soul based on new consolidated memories.
        This is where the 'entity' grows and changes.
        """
        if not new_memories:
            return

        logger.info(f"Evolving based on {len(new_memories)} new memories...")

        # 1. Experience Growth
        self.state["epoch"] += 1
        self.state["experience_points"] += len(new_memories)

        # 2. Extract keywords for focus areas (Simple Heuristic)
        # In a real system, this would use the GlassBox to extract concepts.
        # Here we just do a simple word frequency on the memories.
        all_text = " ".join(new_memories).lower()
        words = [w for w in all_text.split() if len(w) > 4] # Filter short words
        common = Counter(words).most_common(3)

        current_focus = [w[0] for w in common]
        self.state["focus_areas"] = current_focus

        # 3. Trait Evolution (Placeholder)
        # If specific keywords appear, boost related traits.
        if "help" in all_text or "assist" in all_text:
            self.state["traits"]["helpful"] = self.state["traits"].get("helpful", 0) + 0.01
        if "learn" in all_text or "study" in all_text:
            self.state["traits"]["curious"] = self.state["traits"].get("curious", 0) + 0.01

        # 4. Ethical Alignment Check (Placeholder)
        # Ensure we "hold true" as requested.
        # If we detect potentially dangerous concepts, we might lower alignment slightly
        # but the MoralKernel handles the hard gates. This just tracks the 'drift'.

        self._save_state()
        logger.info(f"Soul evolved to Epoch {self.state['epoch']}. Focus: {self.state['focus_areas']}")

    def get_context_summary(self) -> str:
        """
        Returns a summary of the current state to inject into the context window.
        """
        return (
            f"State: Epoch {self.state['epoch']} | "
            f"Focus: {', '.join(self.state['focus_areas'])} | "
            f"Traits: {self.state['traits']}"
        )
