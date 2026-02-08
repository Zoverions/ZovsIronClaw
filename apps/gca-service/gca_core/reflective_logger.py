"""
Reflective Logger: Axiomatic Introspection System
Steers logging verbosity and focus based on System Entropy and User Intent.
"""

import logging
import torch
import time
from typing import Optional, List, Any
from enum import Enum

# Default logger fallback
logger = logging.getLogger("GCA.ReflectiveLogger")

class LogLevel(Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

class ReflectiveLogger:
    def __init__(self, glassbox, bio_mem, moral_kernel):
        self.glassbox = glassbox
        self.bio_mem = bio_mem
        self.moral_kernel = moral_kernel

        # Base settings
        self.base_level = LogLevel.INFO
        self.current_entropy = 0.0
        self.focus_vectors: List[torch.Tensor] = []
        self.focus_topics: List[str] = []

        # Internal monologue buffer
        self.monologue_buffer: List[str] = []

        logger.info("Reflective Logger initialized.")

    def set_focus(self, focus_text: str):
        """
        Steer the logger's attention.
        Example: "Debug memory system"
        """
        if not focus_text:
            return

        vec = self.glassbox.get_activation(focus_text)
        self.focus_vectors.append(vec)
        self.focus_topics.append(focus_text)
        logger.info(f"Logger focus set to: {focus_text}")

    def update_entropy(self, entropy_score: float):
        """
        Update internal entropy state.
        High entropy -> Lower log threshold (More Verbose)
        """
        self.current_entropy = entropy_score

        # Dynamic adjustment logic
        if self.current_entropy > 0.7:
            self.base_level = LogLevel.DEBUG
        elif self.current_entropy > 0.4:
            self.base_level = LogLevel.INFO
        else:
            self.base_level = LogLevel.INFO

    def _is_relevant(self, message: str, context: Optional[str] = None) -> bool:
        if not self.focus_vectors:
            return False # Default to not SPECIALLY relevant

        try:
            full_text = message + (context or "")
            msg_vec = self.glassbox.get_activation(full_text)
            msg_vec = torch.nn.functional.normalize(msg_vec, dim=0)

            for focus_vec in self.focus_vectors:
                focus_vec = focus_vec.to(msg_vec.device)
                focus_vec = torch.nn.functional.normalize(focus_vec, dim=0)
                sim = torch.dot(msg_vec, focus_vec).item()
                if sim > 0.6:
                    return True
        except Exception:
            pass # Fallback

        return False

    def log(self, level: str, message: str, context: Optional[str] = None):
        """
        Smart log function.
        Decides whether to print/store based on relevance and entropy.
        """
        lvl_enum = getattr(LogLevel, level.upper(), LogLevel.INFO)
        is_relevant = self._is_relevant(message, context)

        # If no focus is set, everything INFO+ is "relevant enough" to standard log
        # If focus IS set, we only elevate DEBUG logs if they match focus.

        # 2. Decision Matrix
        should_log = False

        # Always log ERROR/WARN
        if lvl_enum.value >= LogLevel.WARN.value:
            should_log = True

        # If High Entropy, log DEBUG/TRACE
        elif self.current_entropy > 0.7 and lvl_enum.value >= LogLevel.DEBUG.value:
            should_log = True

        # If Relevant to User Focus, Log it even if DEBUG
        elif is_relevant and lvl_enum.value >= LogLevel.DEBUG.value:
            should_log = True

        # Standard Baseline
        elif lvl_enum.value >= self.base_level.value:
            should_log = True

        if should_log:
            # Emit to standard logging
            method = getattr(logger, level.lower(), logger.info)
            prefix = ""
            if is_relevant and self.focus_vectors:
                prefix = "[FOCUS] "
            if self.current_entropy > 0.7:
                prefix += "[CHAOS] "

            method(f"{prefix}{message}")

            # 3. Introspection (Symbiosis)
            # If relevant or high entropy, maybe "think" about it?
            if is_relevant or lvl_enum.value >= LogLevel.WARN.value:
                self.monologue_buffer.append(f"[{level}] {message}")
                if len(self.monologue_buffer) > 5:
                    self._flush_introspection()

    def bind_observer(self, observer_callback):
        self._observer_callback = observer_callback

    def _flush_introspection(self):
        if not hasattr(self, '_observer_callback'):
            return

        thought_block = "\n".join(self.monologue_buffer)
        self.monologue_buffer = []

        try:
            # Self-Reflect: Inject logs as "text" modality with "internal_monologue" source
            # This allows the Observer to "see" the system's own thoughts/errors
            self._observer_callback(
                modality="text",
                content=f"Internal System Log Analysis:\n{thought_block}",
                metadata={"source": "reflective_logger", "type": "introspection"}
            )
        except Exception as e:
            # Avoid infinite loop of error logging
            print(f"Introspection failed: {e}")
