import torch
import torch.nn.functional as F
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger("GCA.ActiveInference")

@dataclass
class FreeEnergyState:
    value: float
    mode: str  # "homeostatic", "reflexive", "strategic"

class GenerativeModel:
    """
    Maintains the 'Expected State' (Goal) of the system.
    """
    def __init__(self, glassbox, goal_text: str):
        self.glassbox = glassbox
        self.goal_text = goal_text
        self.goal_vector = None
        self._embed_goal()

    def _embed_goal(self):
        if self.goal_text:
            self.goal_vector = self.glassbox.get_activation(self.goal_text)
            self.goal_vector = F.normalize(self.goal_vector, dim=0)

    def update_goal(self, new_goal_text: str):
        self.goal_text = new_goal_text
        self._embed_goal()

    def get_expected_state(self) -> Optional[torch.Tensor]:
        return self.goal_vector

class ActiveInferenceLoop:
    """
    Minimizes variational free energy by comparing Perceived State vs Expected State.
    """
    def __init__(self, generative_model: GenerativeModel):
        self.gen_model = generative_model

    def compute_free_energy(self, perceived_state: torch.Tensor) -> FreeEnergyState:
        """
        Calculates Free Energy F ~ D_KL(Q(s)||P(s)).
        Here approximated as 1 - CosineSimilarity(perceived, expected).
        """
        expected = self.gen_model.get_expected_state()
        if expected is None or perceived_state is None:
            return FreeEnergyState(0.0, "homeostatic")

        # Ensure devices match
        if perceived_state.device != expected.device:
            perceived_state = perceived_state.to(expected.device)

        # Calculate Similarity
        sim = F.cosine_similarity(perceived_state, expected, dim=0).item()

        # Free Energy = 1 - Similarity (0.0 to 2.0 range)
        free_energy = 1.0 - sim

        # Determine Control Mode
        # < 0.3: Homeostatic (All good)
        # 0.3 - 0.7: Reflexive (Fast correction)
        # > 0.7: Strategic (Deep replanning needed)
        if free_energy < 0.3:
            mode = "homeostatic"
        elif free_energy < 0.7:
            mode = "reflexive"
        else:
            mode = "strategic"

        logger.debug(f"[ActiveInference] F={free_energy:.3f} Mode={mode}")
        return FreeEnergyState(free_energy, mode)
