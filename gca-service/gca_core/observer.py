"""
Observer Module: The Senses of IronClaw.
Bridges sensory input (text, audio, vision) to the GlassBox for latent space projection.
"""

import logging
import torch
import time
from typing import Dict, Any, Optional
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
