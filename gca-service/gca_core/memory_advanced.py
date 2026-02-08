import torch
import json
import time
import os
import threading
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path
import numpy as np

from gca_core.secure_storage import SecureStorage

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
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserInsight:
    """Tracks the user's Causal Signature and patterns."""
    user_id: str
    avg_complexity: float = 0.5  # Tracking preference for depth
    mood_volatility: float = 0.1
    top_intents: Dict[str, int] = field(default_factory=dict)
    last_interaction: float = field(default_factory=time.time)

    def update(self, complexity_score: float, intent: str):
        # Exponential moving average for complexity
        self.avg_complexity = (self.avg_complexity * 0.9) + (complexity_score * 0.1)

        # Update intents
        if intent in self.top_intents:
            self.top_intents[intent] += 1
        else:
            self.top_intents[intent] = 1

        self.last_interaction = time.time()

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
        self.lock = threading.Lock()

        # Initialize Secure Storage for LTM
        self.secure_storage = SecureStorage()

        # User Modeling
        self.user_insights: Dict[str, UserInsight] = {}
        self.insights_path = self.base_mem.storage_path / "user_insights.json"
        self._load_insights()

        # Ensure basis exists
        input_dim = self.gb.get_hidden_size()
        self.basis = self.base_mem.get_or_create_basis(input_dim, self.basis_size)

    def perceive(self, text: str, env_context: Optional[str] = None):
        """
        Sensory Input -> Working Memory.
        If WM is full, the oldest/least-used item is pushed out (Forgotten or Consolidated).

        Args:
            text: The main input text.
            env_context: Optional string describing environment (weather, news, location).
        """
        if not text:
            return

        # Combine text with environment for vectorization, but keep content separate
        full_input = f"{env_context}\n{text}" if env_context else text
        raw_vector = self.gb.get_activation(full_input)

        # Project to concept space: (Hidden) @ (Hidden, 32) -> (32)
        basis = self.basis.to(raw_vector.device)
        concept_vector = torch.matmul(raw_vector, basis)
        concept_vector = torch.nn.functional.normalize(concept_vector, dim=0)

        # Create Engram
        metadata = {"has_env_context": bool(env_context)}
        engram = Engram(content=text, vector=concept_vector, metadata=metadata)

        # If specific environmental context exists, add it as a separate context engram too
        if env_context:
            env_vec = torch.matmul(self.gb.get_activation(env_context), basis)
            env_vec = torch.nn.functional.normalize(env_vec, dim=0)
            env_engram = Engram(content=f"[ENV] {env_context}", vector=env_vec)
            # Add environment directly to WM (bypass rehearsal check for now)
            self.working_memory.append(env_engram)

        with self.lock:
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

    def track_user_pattern(self, user_id: str, complexity_score: float, intent: str):
        """
        Update the persistent model of the user based on interaction analysis.
        """
        if user_id not in self.user_insights:
            self.user_insights[user_id] = UserInsight(user_id=user_id)

        self.user_insights[user_id].update(complexity_score, intent)
        logger.debug(f"Updated insight for {user_id}: Complexity={self.user_insights[user_id].avg_complexity:.2f}")

        # Periodically save (e.g., every update for now, or could throttle)
        self._save_insights()

    def get_user_insight(self, user_id: str) -> Optional[UserInsight]:
        return self.user_insights.get(user_id)

    def _load_insights(self):
        """Load user insights from disk."""
        if self.insights_path.exists():
            try:
                with open(self.insights_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for uid, udata in data.items():
                        self.user_insights[uid] = UserInsight(**udata)
                logger.info(f"Loaded insights for {len(self.user_insights)} users.")
            except Exception as e:
                logger.error(f"Failed to load user insights: {e}")

    def _save_insights(self):
        """Save user insights to disk."""
        try:
            data = {uid: asdict(insight) for uid, insight in self.user_insights.items()}
            with open(self.insights_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user insights: {e}")

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
        with self.lock:
            for engram in self.working_memory:
                sim = torch.dot(engram.vector, current_thought_vector)
                if sim > 0.6:
                    relevant_context.append(engram.content)
                    # Rehearsal: Reset decay timer
                    engram.last_accessed = time.time()

        return "\n".join(relevant_context)

    def get_working_memory_snapshot(self) -> List[Engram]:
        """Thread-safe copy of working memory."""
        with self.lock:
            return list(self.working_memory)

    def _save_long_term(self, engram):
        """
        Save consolidated memory to an encrypted file.
        """
        try:
            # Change extension to .enc to signify encryption
            memory_file = self.base_mem.storage_path / "memories.enc"
            entry = {
                "content": engram.content,
                "activation_count": engram.activation_count,
                "created_at": engram.creation_time,
                "consolidated_at": time.time(),
                # Store vector as list for JSON serialization if needed
                "vector_preview": engram.vector.tolist()[:5],
                "metadata": engram.metadata
            }

            self.secure_storage.append_jsonl(memory_file, entry)
            logger.info(f"Saved encrypted memory to {memory_file}")
        except Exception as e:
            logger.error(f"Failed to save long term memory: {e}")
