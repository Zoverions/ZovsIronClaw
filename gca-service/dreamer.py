"""
Phase 2 Dreamer: Associative Consolidation
Integrates Causal Flow Analysis to prioritize high-EI memories during REM sleep.
"""
import torch
import os
import logging
from gca_core.causal_flow import CausalFlowEngine, CausalTopology

logger = logging.getLogger("GCA.Dreamer")

class DeepDreamer:
    def __init__(self, memory_system):
        # memory_system is expected to be BiomimeticMemory
        self.mem = memory_system
        # Initialize CausalFlowEngine, optionally passing the GlassBox from memory if available
        self.causal_engine = CausalFlowEngine(glassbox=getattr(self.mem, 'gb', None))

    def rem_cycle(self):
        """
        Run this when the agent is idle (e.g., 3 AM).
        Consolidates memories based on their Causal Emergence (High EI).
        """
        logger.info("[🌙] Entering REM Cycle (Causal Renormalization)...")

        # 1. Prune weak Hebbian connections
        if hasattr(self.mem, 'hebbian'):
             self.mem.hebbian.weights *= 0.95

        # 2. Filter Working Memory for Causal Significance
        # Instead of just wiping WM, we check for hidden gems (High A_N)
        important_memories = []

        # Iterate over a copy of working memory
        for engram in list(self.mem.working_memory):
            # Calculate Beta_C for this memory
            # We treat the engram content as both micro and macro for self-analysis
            # or split it if possible. Here we use the text analyzer.
            flow = self.causal_engine.calculate_causal_beta(engram.content, engram.content)

            if flow.get('is_emergent') or flow.get('topology') == CausalTopology.EMERGENT.value:
                logger.info(f"[✨] Consolidating Emergent Memory (β_C={flow.get('beta_c', 0):.2f}): {engram.content[:30]}...")
                engram.activation_count += 3 # Force consolidation threshold

                # Tag it in metadata
                engram.metadata['causal_topology'] = 'emergent'
                engram.metadata['beta_c'] = flow.get('beta_c')
                important_memories.append(engram)

            elif flow.get('topology') == CausalTopology.SCALE_INVARIANT.value:
                # Slight boost for critical/invariant concepts
                logger.info(f"[⚖️] Preserving Scale-Invariant Memory: {engram.content[:30]}...")
                engram.activation_count += 1
                important_memories.append(engram)

            else:
                # Reductionist Noise
                logger.info(f"[🗑️] Pruning Reductionist Noise: {engram.content[:30]}...")
                # Reduce significance unless it was already highly active (repetition)
                if engram.activation_count < 3:
                    engram.activation_count = max(0, engram.activation_count - 1)

        # 3. Force Consolidation Check on all items
        # This will move high-activation items to LTM and discard the rest
        while self.mem.working_memory:
            self.mem._evict_or_consolidate()

        logger.info("[☀️] Waking up. Synapses updated and Causal Landscape refined.")
