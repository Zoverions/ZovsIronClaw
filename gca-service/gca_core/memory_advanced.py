import torch
import json
import time
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger("GCA.MemoryAdvanced")

# Tuning based on "The Magical Number Seven" (Miller, 1956)
WORKING_MEMORY_CAPACITY = 7
CONSOLIDATION_THRESHOLD = 3 # Times an item is accessed before moving to LTM

@dataclass
class Engram:
    """A single unit of memory (fact, concept, or context)."""
    content: str
    vector: torch.Tensor
    activation_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    creation_time: float = field(default_factory=time.time)

class HebbianNetwork:
    """
    Implements 'Cells that fire together, wire together'.
    Tracks co-occurrence of skills to create composite vectors automatically.
    """
    def __init__(self, basis_size, device="cpu"):
        self.device = device
        self.weights = torch.eye(basis_size, device=self.device) # Identity matrix to start
        self.usage_log = []

    def fire(self, vector_a: torch.Tensor, vector_b: torch.Tensor, learning_rate=0.01):
        """
        Strengthens the geometric connection between two active concepts.
        """
        # Ensure vectors are on the correct device
        vector_a = vector_a.to(self.device)
        vector_b = vector_b.to(self.device)

        # If both vectors are active, increase their cross-product weight
        # This makes activating A slightly activate B in the future
        correlation = torch.outer(vector_a, vector_b)
        self.weights += correlation * learning_rate
        # Normalize to prevent explosion
        self.weights = torch.nn.functional.normalize(self.weights, dim=1)

class BiomimeticMemory:
    def __init__(self, glassbox, base_memory):
        self.gb = glassbox
        self.base_mem = base_memory # The existing IsotropicMemory
        self.basis_size = 32

        # Initialize Hebbian Network
        self.hebbian = HebbianNetwork(basis_size=self.basis_size, device=self.gb.device)

        # The Workbench (Short Term / Working Memory)
        self.working_memory: List[Engram] = []

        # Ensure basis exists
        input_dim = 1024 # Default fallback
        if hasattr(self.gb.model, "config"):
             input_dim = self.gb.model.config.hidden_size

        self.basis = self.base_mem.get_or_create_basis(input_dim, self.basis_size)

    def perceive(self, text: str):
        """
        Sensory Input -> Working Memory.
        If WM is full, the oldest/least-used item is pushed out (Forgotten or Consolidated).
        """
        if not text:
            return

        raw_vector = self.gb.get_activation(text)

        # Project to concept space: (Hidden) @ (Hidden, 32) -> (32)
        # We need self.basis to be (Hidden, 32)
        # raw_vector is (Hidden)

        basis = self.basis.to(raw_vector.device)
        concept_vector = torch.matmul(raw_vector, basis)
        concept_vector = torch.nn.functional.normalize(concept_vector, dim=0)

        engram = Engram(content=text, vector=concept_vector)

        # Check if relevant to existing WM (Rehearsal)
        for existing in self.working_memory:
            sim = torch.nn.functional.cosine_similarity(existing.vector, concept_vector, dim=0)
            if sim > 0.85:
                existing.activation_count += 1
                existing.last_accessed = time.time()
                # Update content with new detail (Refinement)
                # Avoid infinite growth if it's just a repetition
                if text not in existing.content:
                    existing.content = f"{existing.content} -> {text}"

                # Hebbian Learning: Fire together
                self.hebbian.fire(existing.vector, concept_vector)
                return

        # Add to WM
        self.working_memory.append(engram)

        # Enforce Capacity Limits (Cognitive Load Management)
        if len(self.working_memory) > WORKING_MEMORY_CAPACITY:
            self._evict_or_consolidate()

    def _evict_or_consolidate(self):
        """
        Decides if an item dropping out of WM is worth saving to LTM.
        """
        # Sort by last accessed (LRU)
        # reverse=True means largest timestamp (most recent) is at index 0.
        # pop() removes the last item (least recent).
        self.working_memory.sort(key=lambda x: x.last_accessed, reverse=True)
        dropped = self.working_memory.pop()

        if dropped.activation_count >= CONSOLIDATION_THRESHOLD:
            logger.info(f"[🧠] Consolidating to LTM: {dropped.content[:30]}...")
            self._save_long_term(dropped)
        else:
            logger.info(f"[🗑️] Forgetting: {dropped.content[:30]}...")

    def retrieve_context(self, current_thought_vector_raw: torch.Tensor):
        """
        Retrieves context from WM based on geometric relevance.
        """
        if current_thought_vector_raw is None:
            return ""

        # Project query vector too
        basis = self.basis.to(current_thought_vector_raw.device)
        current_thought_vector = torch.matmul(current_thought_vector_raw, basis)
        current_thought_vector = torch.nn.functional.normalize(current_thought_vector, dim=0)

        relevant_context = []
        for engram in self.working_memory:
            sim = torch.dot(engram.vector, current_thought_vector)
            if sim > 0.6:
                relevant_context.append(engram.content)
                # Rehearsal: Reset decay timer
                engram.last_accessed = time.time()

        return "\n".join(relevant_context)

    def _save_long_term(self, engram):
        """
        Save consolidated memory to a JSONL file.
        """
        try:
            memory_file = self.base_mem.storage_path / "memories.jsonl"
            entry = {
                "content": engram.content,
                "activation_count": engram.activation_count,
                "created_at": engram.creation_time,
                "consolidated_at": time.time(),
                # Store vector as list for JSON serialization if needed
                "vector_preview": engram.vector.tolist()[:5]
            }

            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

            logger.info(f"Saved memory to {memory_file}")
        except Exception as e:
            logger.error(f"Failed to save long term memory: {e}")
