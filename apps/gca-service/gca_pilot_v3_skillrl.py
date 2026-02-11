"""
GCA Pilot V3: SkillRL Integration
---------------------------------
Implements the pilot loop with recursive skill augmentation.
"""

import sys
import logging
import os

# Add current directory to path so we can import gca_core if run as script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gca_core.glassbox import GlassBox
from gca_core.memory import IsotropicMemory
from gca_core.skillrl import SkillEvolutionEngine
from gca_core.resource_manager import ResourceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GCAPilotV3")

class GCAPilot:
    def __init__(self):
        # Initialize Core Components
        self.rm = ResourceManager()
        self.cfg = self.rm.get_active_config()

        # Override device if needed for quick testing or leave as config
        self.glassbox = GlassBox(config=self.cfg)
        self.memory = IsotropicMemory(device=self.glassbox.device)

        # Ensure model is loaded so we can access it
        self.glassbox._ensure_model_loaded()

        # Ensure basis exists for SkillRL
        # Basis shape: [16, 768] (or whatever hidden size is)
        hidden_size = self.glassbox.get_hidden_size()

        # We need a basis of shape (16, hidden_size)
        # IsotropicMemory.get_or_create_basis(input_dim, output_dim) creates (input_dim, output_dim)
        self.basis = self.memory.get_or_create_basis(16, hidden_size)

        # Initialize Skill Evolution Engine
        self.evolver = SkillEvolutionEngine(
            model=self.glassbox.model,
            tokenizer=self.glassbox.tokenizer,
            basis=self.basis
        )

    def run_mission(self, prompt: str, skill_name: str = "general_reasoning", score: float = None):
        """
        Executes a single mission (trajectory) and learns from it.
        """
        logger.info(f"Starting Mission: {prompt[:50]}...")

        # 1. Reasoning (Forward Pass)
        response = self.glassbox.generate_steered(prompt, strength=1.0)

        print(f"\n[Pilot] Response:\n{response}\n")

        # 2. Feedback Loop
        if score is None:
            try:
                score_input = input("Rate this response (0.0 - 1.0): ")
                score = float(score_input)
            except ValueError:
                print("Invalid score. Defaulting to 0.5")
                score = 0.5

        # 3. Evolution (Backward Pass / Update)
        self.evolver.log_trajectory(
            skill_name=skill_name,
            user_prompt=prompt,
            final_response=response,
            success_score=score
        )

if __name__ == "__main__":
    pilot = GCAPilot()

    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        print("Usage: python gca_pilot_v3_skillrl.py <prompt>")
        sys.exit(1)

    pilot.run_mission(prompt)
