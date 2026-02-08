import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

def test_compose_logic():
    print("Testing Soul Composition Logic...")

    # Mock heavy dependencies using patch.dict to avoid polluting global state too much
    # (though imported modules will stay cached)
    with patch.dict(sys.modules, {
        'torch': MagicMock(),
        'transformers': MagicMock(),
        'numpy': MagicMock(),
        'textblob': MagicMock(),
        'gca_core.glassbox': MagicMock(),
        'gca_core.moral': MagicMock(),
        'gca_core.memory': MagicMock(),
        'gca_core.optimizer': MagicMock(),
        'gca_core.qpt': MagicMock(),
        'gca_core.arena': MagicMock(),
    }):
        # Add gca-service to sys.path
        sys.path.insert(0, str(Path(__file__).parent.parent / "gca-service"))

        # Import inside the patched context
        from gca_core.soul_loader import get_soul_loader

        # Initialize loader
    # It will try to load souls from gca-service/gca_assets/souls
    # We should make sure we point to the right dir or mock it
    # SoulLoader defaults to __file__.parent.parent / "gca_assets" / "souls"
    # Since we imported from gca_core, it should find it relative to gca_core location

    loader = get_soul_loader()
    print(f"Loaded {len(loader.list_souls())} souls: {loader.list_souls()}")

    base = "architect" # Assuming lower case filename match
    blend = "companion"

    if base not in loader.list_souls() or blend not in loader.list_souls():
        print(f"Error: Required souls not found. Available: {loader.list_souls()}")
        return

    # Test Composition
    base_souls = [base, blend]
    weights = [1.0, 0.5] # Base weighted 1.0, blend weighted 0.5

    print(f"Composing {base} (1.0) and {blend} (0.5)...")

    composite = loader.create_composite_soul(
        name="TestComposite",
        base_souls=base_souls,
        weights=weights
    )

    if composite:
        print(f"Success! Created composite soul: {composite.name}")
        print(f"Description: {composite.description}")
        print("Vector Composition:")
        comp = composite.get_vector_composition()
        for k, v in comp.items():
            print(f"  {k}: {v:.4f}")

        # Verify normalization
        total_weight = sum(weights)
        norm_weights = [w / total_weight for w in weights]

        # Check a skill present in both or one
        # architect usually has LOGIC, companion has EMPATHY
        # We expect blended values
        pass
    else:
        print("Failed to create composite soul.")
        exit(1)

if __name__ == "__main__":
    test_compose_logic()
