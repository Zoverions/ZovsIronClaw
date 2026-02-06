"""
Soul Loader: Load and manage soul templates for GCA
Souls define the personality, behavior, and ethical parameters of the agent.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger("GCA.SoulLoader")


class SoulTemplate:
    """Represents a loaded soul template."""
    
    def __init__(self, data: Dict):
        """Initialize from parsed YAML data."""
        self.name = data.get("name", "Unknown")
        self.description = data.get("description", "")
        self.base_vector_mix = data.get("base_vector_mix", [])
        self.qpt_defaults = data.get("qpt_defaults", {})
        self.entropy_tolerance = data.get("entropy_tolerance", "MEDIUM")
        self.risk_tolerance = data.get("risk_tolerance", 0.3)
        self.traits = data.get("traits", [])
        self.communication = data.get("communication", {})
        self.tool_preferences = data.get("tool_preferences", {})
        self.metadata = data.get("metadata", {})
        
        # Store full data for extensions
        self._data = data
        
    def get_vector_composition(self) -> Dict[str, float]:
        """
        Get the vector composition as a dictionary of skill names to weights.
        
        Returns:
            Dictionary mapping skill names to weights
        """
        composition = {}
        for item in self.base_vector_mix:
            skill = item.get("skill")
            weight = item.get("weight", 1.0)
            if skill:
                composition[skill] = weight
        return composition
        
    def get_qpt_config(self) -> Dict[str, str]:
        """Get the QPT (Quaternion Process Theory) configuration."""
        return self.qpt_defaults
        
    def get_tool_permission(self, tool_category: str, operation: str) -> str:
        """
        Get permission level for a tool operation.
        
        Args:
            tool_category: Category of tool (e.g., "file_operations")
            operation: Specific operation (e.g., "delete")
            
        Returns:
            Permission level: "ALLOWED", "CAUTIOUS", "BLOCKED"
        """
        if tool_category not in self.tool_preferences:
            return "CAUTIOUS"  # Default to cautious
            
        category_prefs = self.tool_preferences[tool_category]
        return category_prefs.get(operation, "CAUTIOUS")
        
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return self._data
        
    def __repr__(self) -> str:
        return f"SoulTemplate(name='{self.name}', entropy_tolerance='{self.entropy_tolerance}')"


class SoulLoader:
    """Loads and manages soul templates from YAML files."""
    
    def __init__(self, souls_dir: Optional[Path] = None):
        """
        Initialize the soul loader.
        
        Args:
            souls_dir: Directory containing soul YAML files
        """
        if souls_dir is None:
            souls_dir = Path(__file__).parent.parent / "gca_assets" / "souls"
        
        self.souls_dir = Path(souls_dir)
        self.souls_cache: Dict[str, SoulTemplate] = {}
        
        # Load all souls on initialization
        self._load_all_souls()
        
        logger.info(f"Soul Loader initialized with {len(self.souls_cache)} souls")
        
    def _load_all_souls(self):
        """Load all soul templates from the souls directory."""
        if not self.souls_dir.exists():
            logger.warning(f"Souls directory not found: {self.souls_dir}")
            self.souls_dir.mkdir(parents=True, exist_ok=True)
            return
            
        for yaml_file in self.souls_dir.glob("*.yaml"):
            try:
                soul_name = yaml_file.stem
                soul = self._load_soul_file(yaml_file)
                self.souls_cache[soul_name] = soul
                logger.info(f"Loaded soul: {soul_name}")
            except Exception as e:
                logger.error(f"Failed to load soul from {yaml_file}: {e}")
                
    def _load_soul_file(self, file_path: Path) -> SoulTemplate:
        """
        Load a soul template from a YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            SoulTemplate instance
        """
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return SoulTemplate(data)
        
    def get_soul(self, name: str) -> Optional[SoulTemplate]:
        """
        Get a soul template by name.
        
        Args:
            name: Soul name (without .yaml extension)
            
        Returns:
            SoulTemplate if found, None otherwise
        """
        soul = self.souls_cache.get(name)
        if soul is None:
            logger.warning(f"Soul not found: {name}")
        return soul
        
    def list_souls(self) -> List[str]:
        """Get a list of all available soul names."""
        return list(self.souls_cache.keys())
        
    def get_soul_info(self, name: str) -> Optional[Dict]:
        """
        Get information about a soul without loading it fully.
        
        Args:
            name: Soul name
            
        Returns:
            Dictionary with soul metadata
        """
        soul = self.get_soul(name)
        if soul is None:
            return None
            
        return {
            "name": soul.name,
            "description": soul.description,
            "entropy_tolerance": soul.entropy_tolerance,
            "risk_tolerance": soul.risk_tolerance,
            "traits": soul.traits,
            "metadata": soul.metadata
        }
        
    def reload_souls(self):
        """Reload all soul templates from disk."""
        self.souls_cache.clear()
        self._load_all_souls()
        logger.info("Reloaded all souls")
        
    def create_composite_soul(
        self,
        name: str,
        base_souls: List[str],
        weights: Optional[List[float]] = None
    ) -> Optional[SoulTemplate]:
        """
        Create a composite soul by blending multiple souls.
        
        Args:
            name: Name for the composite soul
            base_souls: List of soul names to blend
            weights: Optional weights for each soul (default: equal weights)
            
        Returns:
            Composite SoulTemplate
        """
        if not base_souls:
            logger.error("Cannot create composite soul: no base souls provided")
            return None
            
        # Load base souls
        loaded_souls = []
        for soul_name in base_souls:
            soul = self.get_soul(soul_name)
            if soul is None:
                logger.error(f"Cannot create composite: soul '{soul_name}' not found")
                return None
            loaded_souls.append(soul)
            
        # Default to equal weights
        if weights is None:
            weights = [1.0 / len(base_souls)] * len(base_souls)
        elif len(weights) != len(base_souls):
            logger.error("Number of weights must match number of base souls")
            return None
            
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Blend vector compositions
        blended_vectors = {}
        for soul, weight in zip(loaded_souls, weights):
            for skill, skill_weight in soul.get_vector_composition().items():
                if skill not in blended_vectors:
                    blended_vectors[skill] = 0.0
                blended_vectors[skill] += skill_weight * weight
                
        # Create composite data
        composite_data = {
            "name": name,
            "description": f"Composite of: {', '.join(base_souls)}",
            "base_vector_mix": [
                {"skill": skill, "weight": weight}
                for skill, weight in blended_vectors.items()
            ],
            "qpt_defaults": loaded_souls[0].qpt_defaults,  # Use first soul's QPT
            "entropy_tolerance": loaded_souls[0].entropy_tolerance,
            "risk_tolerance": sum(s.risk_tolerance * w for s, w in zip(loaded_souls, weights)),
            "traits": sum([s.traits for s in loaded_souls], []),  # Combine all traits
            "metadata": {
                "composite": True,
                "base_souls": base_souls,
                "weights": weights
            }
        }
        
        composite = SoulTemplate(composite_data)
        logger.info(f"Created composite soul: {name}")
        return composite


# Global soul loader instance
_soul_loader: Optional[SoulLoader] = None


def get_soul_loader() -> SoulLoader:
    """Get the global soul loader instance."""
    global _soul_loader
    if _soul_loader is None:
        _soul_loader = SoulLoader()
    return _soul_loader


def load_soul(name: str) -> Optional[SoulTemplate]:
    """
    Convenience function to load a soul by name.
    
    Args:
        name: Soul name
        
    Returns:
        SoulTemplate if found, None otherwise
    """
    loader = get_soul_loader()
    return loader.get_soul(name)
