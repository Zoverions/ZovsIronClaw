"""
Isotropic Memory: Vector Storage and Retrieval for GCA Framework
Manages skill vectors, soul configurations, and geometric knowledge.
"""

import torch
from typing import Dict, Optional, List
import json
import logging
from pathlib import Path

logger = logging.getLogger("GCA.Memory")


class IsotropicMemory:
    """
    Isotropic Memory stores and retrieves vectors in a geometry-preserving manner.
    It maintains the "skill library" and "soul templates" for the GCA system.
    """
    
    def __init__(self, device: str = "cpu", storage_path: Optional[str] = None):
        """
        Initialize the memory system.
        
        Args:
            device: Computing device (cpu/cuda)
            storage_path: Path to persistent storage directory
        """
        self.device = device
        self.storage_path = Path(storage_path) if storage_path else Path("./gca_assets")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory vector store
        self.vectors: Dict[str, torch.Tensor] = {}
        self.metadata: Dict[str, dict] = {}
        
        # Load existing vectors if available
        self._load_vectors()
        logger.info(f"Isotropic Memory initialized with {len(self.vectors)} vectors")
        
    def _load_vectors(self):
        """Load vectors from persistent storage."""
        vector_file = self.storage_path / "vectors.pt"
        metadata_file = self.storage_path / "metadata.json"
        
        if vector_file.exists():
            try:
                data = torch.load(vector_file)
                self.vectors = data
                logger.info(f"Loaded {len(self.vectors)} vectors from storage")
            except Exception as e:
                logger.warning(f"Failed to load vectors: {e}")
                
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata)} vectors")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                
    def save_vectors(self):
        """Save vectors to persistent storage."""
        vector_file = self.storage_path / "vectors.pt"
        metadata_file = self.storage_path / "metadata.json"
        
        try:
            torch.save(self.vectors, vector_file)
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"Saved {len(self.vectors)} vectors to storage")
        except Exception as e:
            logger.error(f"Failed to save vectors: {e}")
            
    def store_vector(self, name: str, vector: torch.Tensor, metadata: Optional[dict] = None):
        """
        Store a vector with associated metadata.
        
        Args:
            name: Unique identifier for the vector
            vector: The vector to store
            metadata: Optional metadata dictionary
        """
        self.vectors[name] = vector.to(self.device)
        if metadata:
            self.metadata[name] = metadata
        logger.debug(f"Stored vector: {name}")
        
    def get_vector(self, name: str) -> Optional[torch.Tensor]:
        """
        Retrieve a vector by name.
        
        Args:
            name: Vector identifier
            
        Returns:
            The vector if found, None otherwise
        """
        if name in self.vectors:
            return self.vectors[name]
            
        # Try composite vectors (e.g., "LOGIC+PYTHON")
        if "+" in name:
            return self._compose_vectors(name.split("+"))
            
        logger.warning(f"Vector not found: {name}")
        return None
        
    def _compose_vectors(self, names: List[str]) -> Optional[torch.Tensor]:
        """
        Compose multiple vectors through addition.
        
        Args:
            names: List of vector names to combine
            
        Returns:
            Combined vector or None if any component is missing
        """
        vectors = []
        for name in names:
            vec = self.vectors.get(name.strip())
            if vec is None:
                logger.warning(f"Cannot compose: {name} not found")
                return None
            vectors.append(vec)
            
        # Simple addition (could be weighted in advanced version)
        combined = torch.stack(vectors).mean(dim=0)
        return combined
        
    def find_similar(self, query_vector: torch.Tensor, top_k: int = 5) -> List[tuple]:
        """
        Find the most similar vectors to a query vector.
        
        Args:
            query_vector: Vector to compare against
            top_k: Number of results to return
            
        Returns:
            List of (name, similarity_score) tuples
        """
        if not self.vectors:
            return []
            
        similarities = []
        query_norm = query_vector / (query_vector.norm() + 1e-8)
        
        for name, vec in self.vectors.items():
            vec_norm = vec / (vec.norm() + 1e-8)
            similarity = torch.dot(query_norm, vec_norm).item()
            similarities.append((name, similarity))
            
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
        
    def create_skill_vector(
        self,
        name: str,
        positive_examples: List[str],
        negative_examples: List[str],
        glassbox
    ):
        """
        Create a skill vector from positive and negative examples.
        
        Args:
            name: Name for the skill vector
            positive_examples: Examples of desired behavior
            negative_examples: Examples of undesired behavior
            glassbox: GlassBox instance for activation extraction
        """
        pos_activations = [glassbox.get_activation(ex) for ex in positive_examples]
        neg_activations = [glassbox.get_activation(ex) for ex in negative_examples]
        
        pos_mean = torch.stack(pos_activations).mean(dim=0)
        neg_mean = torch.stack(neg_activations).mean(dim=0)
        
        # The skill vector is the difference
        skill_vector = pos_mean - neg_mean
        
        self.store_vector(name, skill_vector, {
            "type": "skill",
            "positive_count": len(positive_examples),
            "negative_count": len(negative_examples)
        })
        
        logger.info(f"Created skill vector: {name}")
        
    def list_vectors(self) -> List[str]:
        """Get a list of all stored vector names."""
        return list(self.vectors.keys())
