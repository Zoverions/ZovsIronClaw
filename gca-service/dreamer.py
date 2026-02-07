"""
Phase 2 Dreamer: Associative Consolidation
"""
import torch
import os
import logging
from gca_core.evolution import EvolutionEngine

logger = logging.getLogger("GCA.Dreamer")

class DeepDreamer:
    def __init__(self, memory_system):
        # memory_system is expected to be BiomimeticMemory
        self.mem = memory_system
        self.evolution = EvolutionEngine(self.mem.base_mem.storage_path)

    def rem_cycle(self):
        """
        Run this when the agent is idle (e.g., 3 AM).
        """
        logger.info("[🌙] Entering REM Cycle (Consolidation)...")

        # 1. Prune weak Hebbian connections
        # If connections weren't reinforced today, they decay.
        if hasattr(self.mem, 'hebbian'):
             self.mem.hebbian.weights *= 0.95

        # 2. Extract "Insights" from User interactions
        # Collect recent experiences from Working Memory before clearing it
        recent_experiences = [engram.content for engram in self.mem.working_memory]

        # Evolve the soul based on these experiences
        if recent_experiences:
            logger.info(f"Dreaming about {len(recent_experiences)} experiences...")
            self.evolution.evolve(recent_experiences)

        # 3. Clean 'Working Memory' completely
        # Wake up with a fresh mind, relying only on LTM.
        self.mem.working_memory = []

        logger.info("[☀️] Waking up. Synapses updated.")
