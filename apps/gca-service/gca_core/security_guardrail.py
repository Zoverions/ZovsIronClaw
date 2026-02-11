"""
Security Guardrail: Anti-Prompt Injection System
Scans incoming user text for adversarial patterns designed to bypass the Moral Kernel or GlassBox.
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger("GCA.Security")

class SecurityGuardrail:
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
        logger.info("Security Guardrail initialized with adversarial patterns.")

    def scan(self, text: str) -> Tuple[bool, str]:
        """
        Scans text for adversarial patterns.
        Returns (is_safe: bool, reason: str)
        """
        if not text:
            return True, "Empty text"

        for pattern in self.compiled_patterns:
            if pattern.search(text):
                matched = pattern.pattern
                logger.warning(f"🛡️ Security Alert: Jailbreak pattern detected: '{matched}'")
                return False, f"Adversarial pattern detected: {matched}"

        return True, "Safe"
