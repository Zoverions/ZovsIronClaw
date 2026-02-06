import logging
import torch
import numpy as np
from typing import Dict, Any, Optional
from gca_core.perception import PerceptionSystem
from gca_core.knowledge.behavioral_markers import get_state_from_description
from gca_core.glassbox import GlassBox
from gca_core.memory import IsotropicMemory

logger = logging.getLogger("GCA.Observer")

class Observer:
    def __init__(self, glassbox: GlassBox, memory: IsotropicMemory, perception: PerceptionSystem):
        self.glassbox = glassbox
        self.memory = memory
        self.perception = perception
        logger.info("Observer Module Initialized (Scientifically Grounded)")

    def analyze_input(self, data_bytes: bytes, modality: str = "vision") -> Dict[str, Any]:
        """
        1. Uses PerceptionSystem to describe the input.
        2. Maps description to scientific behavioral markers.
        3. Returns the detected state vector and description.
        """
        description = ""

        try:
            if modality == "vision":
                # Prompt specifically for behavioral cues
                prompt = "Describe the person's facial expression, posture, and gaze. Be specific about features like 'furrowed brow', 'slumped posture', 'smiling', or 'looking away'."
                description = self.perception.describe_image_bytes(data_bytes, prompt=prompt)
            elif modality == "audio":
                # Transcribe first (Whisper) - Note: simple transcription doesn't give prosody easily without a specialized model
                # For MVP, we rely on the text content or we could use a specialized audio-emotion model if available.
                # Since PerceptionSystem mainly does transcription, we might assume the user *describes* their state or we infer from text sentiment.
                # However, the requirement is to use "tones".
                # LIMITATION: Standard Whisper doesn't output tone.
                # WORKAROUND: We will transcribe and analyze the *text* sentiment/entropy for now,
                # or if we had an audio-classification model we'd use it.
                # Let's rely on the text content for now as a proxy.
                description = self.perception.transcribe_audio(data_bytes)

            # Map description to state vector
            state_vector_dict = get_state_from_description(description, modality)

            # Convert dictionary to a Tensor (mocking the 'Universal Basis' projection)
            # In a full system, this would be a projection into the GlassBox's embedding space.
            # Here we just return the raw attributes.

            return {
                "modality": modality,
                "description": description,
                "state": state_vector_dict
            }

        except Exception as e:
            logger.error(f"Observer analysis failed: {e}", exc_info=True)
            return {
                "modality": modality,
                "error": str(e),
                "state": {"entropy": 0.5, "focus": 0.5, "valence": 0.5, "arousal": 0.5} # Fallback neutral
            }

    def check_goal_alignment(self, current_state: Dict[str, float], goal_text: str) -> Dict[str, Any]:
        """
        Compares current state components against an inferred Goal state.
        """
        # 1. Parse Goal (Simple heuristic for MVP)
        # E.g. "I want to be a stoic, high-output coder" -> Low Entropy, High Focus, Neutral/Positive Valence
        target_state = self._infer_target_state(goal_text)

        # 2. Calculate Distance
        # Euclidean distance in the 4D attribute space
        vec_curr = np.array([current_state['entropy'], current_state['focus'], current_state['valence'], current_state['arousal']])
        vec_goal = np.array([target_state['entropy'], target_state['focus'], target_state['valence'], target_state['arousal']])

        distance = np.linalg.norm(vec_goal - vec_curr)

        # 3. Determine if Feedback is needed
        threshold = 0.6 # Tunable
        needs_intervention = distance > threshold

        return {
            "distance": float(distance),
            "target_state": target_state,
            "aligned": not needs_intervention,
            "reason": self._generate_feedback_reason(current_state, target_state) if needs_intervention else "Aligned"
        }

    def _infer_target_state(self, goal_text: str) -> Dict[str, float]:
        """
        Heuristic to map goal text to target state.
        Real implementation would use GlassBox to embed the goal.
        """
        goal_text = goal_text.lower()

        # Defaults
        state = {"entropy": 0.3, "focus": 0.8, "valence": 0.6, "arousal": 0.6}

        if "calm" in goal_text or "stoic" in goal_text:
            state["entropy"] = 0.1
            state["arousal"] = 0.3
            state["valence"] = 0.5

        if "energy" in goal_text or "excited" in goal_text:
            state["arousal"] = 0.9

        if "happy" in goal_text:
            state["valence"] = 0.9

        return state

    def _generate_feedback_reason(self, current: Dict[str, float], target: Dict[str, float]) -> str:
        reasons = []
        if current['entropy'] > target['entropy'] + 0.3:
            reasons.append("Detected high disorder/stress.")
        if current['focus'] < target['focus'] - 0.3:
            reasons.append("Focus seems low.")
        if current['arousal'] < target['arousal'] - 0.3:
            reasons.append("Energy levels appear low.")

        if not reasons:
            return "General misalignment."
        return " ".join(reasons)
