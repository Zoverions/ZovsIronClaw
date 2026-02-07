"""
Observer Module: The Senses of IronClaw.
Bridges sensory input (text, audio, vision) to the GlassBox for latent space projection.
"""

import logging
import torch
import time
from typing import Dict, Any, Optional, Union, List
from .glassbox import GlassBox

logger = logging.getLogger("GCA.Observer")

class Observer:
    def __init__(self, glassbox: GlassBox):
        self.glassbox = glassbox
        logger.info("Observer module initialized.")

    def process_input(self, modality: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process raw input into a state vector.
        """
        logger.info(f"Observer received input: modality={modality}, size={len(content)}")

        vector = None
        state_description = "neutral"

        try:
            if modality in ["text", "audio"]:
                # Audio is assumed to be pre-transcribed text here, or we'd use a speech model
                # Swabble sends transcribed text
                vector = self.glassbox.get_activation(content)
                state_description = "processing_text"

            elif modality == "vision":
                # Placeholder for vision model
                logger.warning("Vision modality not fully implemented. Using placeholder projection.")
                # We need a vector of the same size as GlassBox output.
                # Projecting a description of the fact it's an image.
                vector = self.glassbox.get_activation("Visual input received but vision encoder is offline.")
                state_description = "vision_stub"

            else:
                logger.warning(f"Unknown modality: {modality}")
                vector = self.glassbox.get_activation("unknown input")
                state_description = "unknown"

            # Check if vector is a Tensor (it should be)
            if isinstance(vector, torch.Tensor):
                vector_list = vector.tolist()
            else:
                vector_list = []

            return {
                "vector": vector_list,
                "state": state_description,
                "timestamp": time.time(),
                "modality": modality,
                "metadata": metadata or {}
            }

        except Exception as e:
            logger.error(f"Observer processing error: {e}", exc_info=True)
            return {
                "error": str(e),
                "state": "error"
            }

    def analyze_input(self, content: Any, modality: str) -> Dict[str, Any]:
        """
        Analyze input to determine user state and description.
        Currently a wrapper around process_input but intended for deeper analysis.
        """
        # If content is bytes (file upload), we need to handle it.
        # process_input expects string content for text/audio (transcribed).
        # api_server passes bytes for 'observe_user'.

        text_content = ""
        if isinstance(content, bytes):
            try:
                text_content = content.decode("utf-8")
            except:
                text_content = "[Binary Data]"
        else:
            text_content = str(content)

        # For now, just call process_input
        result = self.process_input(modality, text_content)

        # Enrich result for API expectation
        result["description"] = f"Processed {modality} input"
        if "state" not in result:
             result["state"] = "active"

        return result

    def check_goal_alignment(self, current_state: Union[str, List[float]], goal_text: str) -> float:
        """
        Check alignment between current state and goal.
        Returns cosine similarity (0.0 to 1.0, or -1.0 to 1.0).
        """
        try:
            # 1. Get Goal Vector
            goal_vec = self.glassbox.get_activation(goal_text)

            # 2. Get State Vector
            state_vec = None
            if isinstance(current_state, str):
                state_vec = self.glassbox.get_activation(current_state)
            elif isinstance(current_state, list):
                state_vec = torch.tensor(current_state, device=self.glassbox.device)

            if state_vec is None:
                return 0.0

            # Ensure same device
            if goal_vec.device != state_vec.device:
                state_vec = state_vec.to(goal_vec.device)

            # 3. Compute Cosine Similarity
            sim = torch.nn.functional.cosine_similarity(state_vec, goal_vec, dim=0).item()
            return sim

        except Exception as e:
            logger.error(f"Alignment check failed: {e}")
            return 0.0
