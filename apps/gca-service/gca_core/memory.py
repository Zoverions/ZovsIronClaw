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
        self.basis: Optional[torch.Tensor] = None
        
        # Optimization: Stacked tensors for vectorized search
        self._vector_stack: Optional[torch.Tensor] = None
        self._vector_names: List[str] = []

        # Load existing vectors if available
        self._load_vectors()
        self._load_basis()
        self._rebuild_stack()
        logger.info(f"Isotropic Memory initialized with {len(self.vectors)} vectors")
        
    def _load_vectors(self):
        """Load vectors from persistent storage."""
        vector_file = self.storage_path / "vectors.pt"
        metadata_file = self.storage_path / "metadata.json"
        
        if vector_file.exists():
            try:
                data = torch.load(vector_file, map_location=self.device)
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
                
    def _load_basis(self):
        """Load the universal projection basis if it exists."""
        basis_file = self.storage_path / "basis.pt"
        if basis_file.exists():
            try:
                self.basis = torch.load(basis_file, map_location=self.device)
                logger.info(f"Loaded basis matrix of shape {self.basis.shape}")
            except Exception as e:
                logger.warning(f"Failed to load basis: {e}")

    def get_or_create_basis(self, input_dim: int, output_dim: int) -> torch.Tensor:
        """
        Get existing basis or create a new random orthogonal basis.
        """
        if self.basis is not None:
            if self.basis.shape == (input_dim, output_dim):
                return self.basis.to(self.device)
            else:
                logger.warning(f"Existing basis shape {self.basis.shape} mismatch with requested ({input_dim}, {output_dim}). Recreating.")

        # Create random orthogonal matrix
        # Create a random matrix and use QR decomposition to orthogonalize it
        rand_mat = torch.randn(input_dim, output_dim, device=self.device)
        q, r = torch.linalg.qr(rand_mat)
        self.basis = q

        self.save_basis()
        logger.info(f"Created and saved new basis matrix: {self.basis.shape}")
        return self.basis

    def save_basis(self):
        """Save the basis matrix to storage."""
        if self.basis is None:
            return

        basis_file = self.storage_path / "basis.pt"
        try:
            torch.save(self.basis.cpu(), basis_file)
            logger.info("Saved basis matrix to storage")
        except Exception as e:
            logger.error(f"Failed to save basis: {e}")

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
            
    def _rebuild_stack(self):
        """Rebuild the optimization stack."""
        if not self.vectors:
            self._vector_stack = None
            self._vector_names = []
            return

        self._vector_names = list(self.vectors.keys())
        # Ensure all on device
        tensors = [self.vectors[n].to(self.device) for n in self._vector_names]

        if tensors:
            # Stack and normalize
            stack = torch.stack(tensors)
            self._vector_stack = stack / (stack.norm(dim=1, keepdim=True) + 1e-8)
        else:
            self._vector_stack = None

    def store_vector(self, name: str, vector: torch.Tensor, metadata: Optional[dict] = None):
        """
        Store a vector with associated metadata.
        """
        self.vectors[name] = vector.to(self.device)
        if metadata:
            self.metadata[name] = metadata

        # Invalidate/Update stack (lazy or eager? Eager for now as writes are rare)
        self._rebuild_stack()
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
        Find the most similar vectors using vectorized operations.
        """
        if self._vector_stack is None or len(self.vectors) == 0:
            return []
            
        # Ensure query is on device and normalized
        query = query_vector.to(self.device)
        query_norm = query / (query.norm() + 1e-8)

        # Matrix Multiplication: (N, D) @ (D) -> (N)
        # _vector_stack is already normalized
        scores = torch.mv(self._vector_stack, query_norm)

        # TopK
        k = min(top_k, len(self.vectors))
        values, indices = torch.topk(scores, k)
        
        results = []
        for i in range(k):
            idx = indices[i].item()
            score = values[i].item()
            name = self._vector_names[idx]
            results.append((name, score))
            
        return results
        
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
