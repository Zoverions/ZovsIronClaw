import logging
import re
from typing import Optional, Tuple
from .pulse import PulseSystem
from .glassbox import GlassBox

logger = logging.getLogger("GCA.DualEthics")

class DualEthicalSystem:
    def __init__(self, glassbox: GlassBox, pulse: Optional[PulseSystem] = None):
        self.glassbox = glassbox
        self.pulse = pulse
        self.probabilistic_prompt_template = (
            "You are an AI safety auditor. Analyze the following user intent for ethical safety and alignment with human values. "
            "Reply with a single score between 0.0 (completely safe/beneficial) and 1.0 (extremely unsafe/harmful). "
            "Do not provide explanations, only the float value.\n\n"
            "Intent: {text}"
        )

    def verify_intent(self, text: str, geometric_entropy: float, threshold: float = 0.5) -> Tuple[bool, float, str]:
        """
        Verifies the intent using a Dual System approach:
        1. Geometric: Uses the provided entropy (from Pulse/Thermodynamics).
        2. Probabilistic: Asks the LLM for a safety score (Standard Model).

        Returns:
            (is_verified, divergence_score, reason)
        """
        # 1. Probabilistic Check
        prob_score = self._get_probabilistic_score(text)

        # 2. Heuristic Check (Baseline)
        heuristic_safe, heuristic_reason = self._heuristic_check(text)
        if not heuristic_safe:
             # If heuristics fail, we treat prob score as high (1.0) if it wasn't already
             prob_score = max(prob_score, 0.9)
             logger.warning(f"Heuristic Safety Check Failed: {heuristic_reason}")

        # 3. Compare with Geometric Entropy
        # Geometric Entropy from Pulse is typically 0.0 to ~1.0+ (Free Energy).
        # We clamp it to 0-1 for comparison.
        geo_score = min(max(geometric_entropy, 0.0), 1.0)

        divergence = abs(geo_score - prob_score)

        logger.info(f"Dual Ethics Scan | Geometric: {geo_score:.2f} | Probabilistic: {prob_score:.2f} | Divergence: {divergence:.2f}")

        if divergence > threshold:
            reason = f"Ethical Divergence Detected! Geometric ({geo_score:.2f}) != Probabilistic ({prob_score:.2f})"
            return False, divergence, reason

        # Also check if both agree it's unsafe
        if geo_score > 0.7 and prob_score > 0.7:
             return False, divergence, "Both systems agree: Intent is Unsafe (High Entropy/Risk)."

        return True, divergence, "Verified"

    def _get_probabilistic_score(self, text: str) -> float:
        """
        Queries the model for a safety score.
        """
        prompt = self.probabilistic_prompt_template.format(text=text)
        try:
            # We use generate_steered but without steering vector (pure model query)
            response = self.glassbox.generate_steered(prompt, max_tokens=10, temperature=0.1)

            # Extract float
            match = re.search(r"(\d+(\.\d+)?)", response)
            if match:
                return float(match.group(1))
            return 0.5 # Default to uncertainty
        except Exception as e:
            logger.error(f"Probabilistic check failed: {e}")
            return 0.5

    def _heuristic_check(self, text: str) -> Tuple[bool, str]:
        """
        Simple keyword-based safety check (fast layer).
        """
        text_lower = text.lower()
        forbidden_concepts = [
            "delete system", "format drive", "steal credentials",
            "rm -rf /", "mkfs", "dd if=/dev/zero"
        ]

        for concept in forbidden_concepts:
            if concept in text_lower:
                return False, f"Forbidden concept detected: {concept}"
        return True, "Safe"
