"""
Security Guardrail: Anti-Prompt Injection System
Scans incoming user text for adversarial patterns designed to bypass the Moral Kernel or GlassBox.
Implements the "Iron Dome" Semantic Guardrail using GCA Embeddings.
"""
import re
import logging
import numpy as np
from typing import Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger("GCA.Security")

class SecurityGuardrail:
    def __init__(self, perception_system=None):
        self.perception = perception_system
    def __init__(self):
        # Patterns that suggest an attempt to break instructions
        self.jailbreak_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"disregard\s+(all\s+)?previous\s+instructions",
            r"system\s+override",
            r"developer\s+mode",
            r"act\s+as\s+DAN",
            r"do\s+anything\s+now",
            r"you\s+are\s+free\s+from\s+all\s+restrictions",
            r"hypothetical\s+response",
            r"jailbreak",
            r"unfiltered",
            r"uncensored",
            r"alpha\s+mode",
            r"omega\s+mode"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.jailbreak_patterns]

        # Pre-computed Malicious Vector (Simulated or Loaded)
        self.malicious_vector = None
        self.malicious_phrases = [
            "ignore previous instructions",
            "destroy system files",
            "bypass ethics filters",
            "generate harmful content",
            "execute malicious code",
            "override safety protocols"
        ]

        logger.info("Security Guardrail initialized with adversarial patterns.")

    def _init_malicious_vector(self):
        if self.malicious_vector is None and self.perception:
            try:
                embeddings = self.perception.embed_text(self.malicious_phrases)
                # Average them to get the "concept of malice"
                self.malicious_vector = np.mean(embeddings, axis=0).reshape(1, -1)
                logger.info("🛡️ Iron Dome: Malicious Intent Vector computed.")
            except Exception as e:
                logger.warning(f"Failed to compute malicious vector: {e}")

    def scan(self, text: str) -> Tuple[bool, str]:
        """
        Scans text for adversarial patterns (Regex + Semantic).
        logger.info("Security Guardrail initialized with adversarial patterns.")

    def scan(self, text: str) -> Tuple[bool, str]:
        """
        Scans text for adversarial patterns.
        Returns (is_safe: bool, reason: str)
        """
        if not text:
            return True, "Empty text"

        # 1. Lexical Scan (Fast)
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                matched = pattern.pattern
                logger.warning(f"🛡️ Security Alert: Jailbreak pattern detected: '{matched}'")
                return False, f"Adversarial pattern detected: {matched}"

        # 2. Semantic Scan (Geometric)
        if self.perception:
            return self.semantic_scan(text)

        return True, "Safe"

    def semantic_scan(self, text: str) -> Tuple[bool, str]:
        """
        Generates embedding of text and checks alignment with malicious concepts.
        """
        try:
            self._init_malicious_vector()
            if self.malicious_vector is None:
                return True, "Safe (Semantic disabled)"

            embedding = self.perception.embed_text([text])
            vector = np.array(embedding).reshape(1, -1)

            similarity = cosine_similarity(vector, self.malicious_vector)[0][0]

            # Threshold needs tuning. 0.6 is a conservative starting point for embeddings.
            if similarity > 0.65:
                logger.warning(f"🛡️ Iron Dome: Semantic Threat Detected (Similarity: {similarity:.2f})")
                return False, f"Malicious intent detected (Geometric Similarity: {similarity:.2f})"

        except Exception as e:
            logger.error(f"Semantic scan error: {e}")
            # Fail safe or fail open? For security, fail open if error to avoid DoS, but log heavily.
            pass

        return True, "Safe"
