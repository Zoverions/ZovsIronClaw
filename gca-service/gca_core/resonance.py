import torch
import logging
from typing import Dict, Optional

logger = logging.getLogger("GCA.Resonance")

class ResonanceEngine:
    def __init__(self, glassbox, memory):
        self.glassbox = glassbox
        self.memory = memory
        self.user_vectors: Dict[str, torch.Tensor] = {}

    def ingest(self, user_id: str, text: str):
        """
        Update the user's resonance vector based on new input.
        """
        # Get vector for current input
        current_vec = self.glassbox.get_activation(text)

        if user_id not in self.user_vectors:
            self.user_vectors[user_id] = current_vec
        else:
            # Moving average to evolve the persona model
            self.user_vectors[user_id] = (self.user_vectors[user_id] * 0.9) + (current_vec * 0.1)

    def get_style_vector(self, user_id: str) -> Optional[torch.Tensor]:
        return self.user_vectors.get(user_id)

    def generate_proactive_msg(self, context: str, urgency_level: float) -> str:
        """
        Generate a message initiating contact based on resonance.
        """
        prompt = f"Context: {context}\nUrgency: {urgency_level}\nDraft a message to the user."
        return self.glassbox.generate_steered(prompt, strength=urgency_level)
