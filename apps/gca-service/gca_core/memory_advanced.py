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

class SensoryBuffer:
    """
    Tier 1: Transient sensory input (Milliseconds/Seconds).
    Rapid decay. Stores raw inputs before processing.
    """
    def __init__(self, decay_rate=0.5):
        self.buffer: List[Engram] = []
        self.decay_rate = decay_rate

    def add(self, engram: Engram):
        self.buffer.append(engram)
        self._decay()

    def _decay(self):
        # Remove items older than X seconds or keeping only last N items
        # For simplicity, keep last 3 items
        if len(self.buffer) > 3:
            self.buffer.pop(0)

    def flush(self) -> List[Engram]:
        """Move items to next tier."""
        items = list(self.buffer)
        self.buffer.clear()
        return items

class EpisodicHippocampus:
    """
    Tier 2: Short-term / Working Memory (Days/Sessions).
    Capacity limited (7 +/- 2). Handles rehearsal and consolidation.
    """
    def __init__(self, capacity=WORKING_MEMORY_CAPACITY):
        self.capacity = capacity
        self.engrams: List[Engram] = []
        self.lock = threading.Lock()

    def add(self, engram: Engram) -> Optional[Engram]:
        """
        Adds engram. Returns dropped engram if full.
        """
        with self.lock:
             # Check for existing (Rehearsal)
            for existing in self.engrams:
                sim = torch.nn.functional.cosine_similarity(existing.vector, engram.vector, dim=0)
                if sim > 0.85:
                    existing.activation_count += 1
                    existing.last_accessed = time.time()
                    if engram.content not in existing.content:
                        existing.content = f"{existing.content} -> {engram.content}"
                    return None

            self.engrams.append(engram)

            if len(self.engrams) > self.capacity:
                # Evict LRU
                self.engrams.sort(key=lambda x: x.last_accessed, reverse=True)
                return self.engrams.pop() # Return dropped item
            return None

    def retrieve(self, query_vector: torch.Tensor, threshold=0.6) -> List[Engram]:
        results = []
        with self.lock:
            for engram in self.engrams:
                sim = torch.dot(engram.vector, query_vector)
                if sim > threshold:
                    results.append(engram)
                    engram.last_accessed = time.time()
        return results

class SemanticNeocortex:
    """
    Tier 3: Long-term abstract concepts (Lifetime).
    Stores consolidated patterns.
    """
    def __init__(self, secure_storage, storage_path):
        self.secure_storage = secure_storage
        self.storage_path = storage_path

    def consolidate(self, engram: Engram):
        """
        Store permanently.
        """
        try:
            # Change extension to .enc to signify encryption
            memory_file = self.storage_path / "memories.enc"
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

        # Initialize Secure Storage for LTM
        self.secure_storage = SecureStorage()

        # Hierarchy Initialization
        self.sensory = SensoryBuffer()
        self.episodic = EpisodicHippocampus(capacity=WORKING_MEMORY_CAPACITY)
        self.semantic = SemanticNeocortex(self.secure_storage, self.base_mem.storage_path)

        self.lock = threading.Lock() # Global lock for now

        # User Modeling
        self.user_insights: Dict[str, UserInsight] = {}
        self.insights_path = self.base_mem.storage_path / "user_insights.json"
        self._load_insights()

        # Ensure basis exists
        input_dim = self.gb.get_hidden_size()
        self.basis = self.base_mem.get_or_create_basis(input_dim, self.basis_size)

    @property
    def working_memory(self) -> List[Engram]:
        """Backward compatibility: exposes Episodic Hippocampus engrams."""
        return self.episodic.engrams

    def perceive(self, text: str, env_context: Optional[str] = None):
        """
        Sensory Input -> Sensory Buffer -> Episodic Hippocampus.
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

        # 1. Sensory Buffer
        self.sensory.add(engram)

        # If specific environmental context exists
        if env_context:
            env_vec = torch.matmul(self.gb.get_activation(env_context), basis)
            env_vec = torch.nn.functional.normalize(env_vec, dim=0)
            env_engram = Engram(content=f"[ENV] {env_context}", vector=env_vec)
            self.sensory.add(env_engram)

        # Flush Sensory to Episodic immediately for now (assuming attention pays attention to all)
        # In future, attention mechanism filters what moves from Sensory to Episodic
        items = self.sensory.flush()

        self.new_memories_flagged = [] # Reset or init buffer for current perception cycle

        for item in items:
            self._process_into_episodic(item)

    def _process_into_episodic(self, engram: Engram):
        # Iron Mesh: Flag significant memories for sync
        if self._is_significant(engram):
            self.new_memories_flagged.append(engram)

        dropped = self.episodic.add(engram)

        if dropped:
             # Hebbian Learning on dropped item (last chance to associate)
             # (Simplified)
             pass

             # Consolidate or Forget
             self._evict_or_consolidate(dropped)

        # Fire Hebbian for current items in episodic
        with self.lock: # Use simple lock for hebbian update
            for existing in self.episodic.engrams:
                if existing != engram:
                    self.hebbian.fire(existing.vector, engram.vector)

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

    def _evict_or_consolidate(self, dropped: Engram):
        """
        Decides if an item dropping out of WM is worth saving to LTM.
        """
        if dropped.activation_count >= CONSOLIDATION_THRESHOLD:
            logger.info(f"[🧠] Consolidating to LTM: {dropped.content[:30]}...")
            self.semantic.consolidate(dropped)
        else:
            logger.info(f"[🗑️] Forgetting: {dropped.content[:30]}...")

    def _is_significant(self, engram: Engram) -> bool:
        """Determines if a memory is worth teleporting to the Hive Mind."""
        c = engram.content.lower()
        triggers = ["my favorite", "i prefer", "remember that", "important:", "note:", "the code is", "password is", "key is"]
        if any(t in c for t in triggers):
            # Exclude transient chat noise
            if len(c.split()) < 3: return False
            return True
        return False

    def get_flagged_memories(self) -> List[Dict[str, Any]]:
        """Returns and clears memories flagged for swarm sync."""
        if not hasattr(self, "new_memories_flagged") or not self.new_memories_flagged:
            return []

        data = []
        for e in self.new_memories_flagged:
            data.append({
                "content": e.content,
                "vector": e.vector.tolist(),
                "metadata": e.metadata
            })
        self.new_memories_flagged = []
        return data

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

        # Delegate to Episodic
        engrams = self.episodic.retrieve(current_thought_vector, threshold=0.6)
        relevant_context = [e.content for e in engrams]

        return "\n".join(relevant_context)

    def inject_external(self, engrams_data: List[Dict[str, Any]]) -> int:
        """
        Injects engrams from external peers (Shared Consciousness).
        Directly adds to Episodic Memory without triggering perception loops.
        """
        count = 0
        for data in engrams_data:
            try:
                content = data.get("content")
                vector_list = data.get("vector")
                metadata = data.get("metadata", {}) or {}

                if not content or not vector_list:
                    continue

                # Reconstruct Vector
                # Handle nested list or flat list just in case
                if isinstance(vector_list, list) and len(vector_list) > 0 and isinstance(vector_list[0], list):
                    vector_list = vector_list[0]

                vector = torch.tensor(vector_list, device=self.gb.device)

                engram = Engram(
                    content=content,
                    vector=vector,
                    metadata=metadata
                )
                # Mark as external in metadata if not present
                if "source" not in engram.metadata:
                    engram.metadata["source"] = "swarm_sync"

                self.episodic.add(engram)
                count += 1

                # Trigger Hebbian learning with current context
                with self.lock:
                    for existing in self.episodic.engrams:
                        if existing != engram:
                            # Fire Hebbian: this connects the new thought to existing ones
                            self.hebbian.fire(existing.vector, engram.vector)

            except Exception as e:
                logger.error(f"Failed to inject engram: {e}")

        if count > 0:
            logger.info(f"Synced {count} memories from swarm.")
        return count

    def get_working_memory_snapshot(self) -> List[Engram]:
        """Thread-safe copy of working memory."""
        with self.lock:
            return list(self.episodic.engrams)

    def _save_long_term(self, engram):
        """Deprecated: Use semantic.consolidate"""
        self.semantic.consolidate(engram)
