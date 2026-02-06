import logging

logger = logging.getLogger("GCA-Pulse")

class Pulse:
    def __init__(self, resonance_engine=None):
        self.resonance = resonance_engine
        self.entropy_threshold = 0.7

    def check_vitals(self, system_status_text: str):
        """
        Analyzes the 'state of the world' text.
        If entropy is high (chaos), it returns a Trigger Signal.
        """
        # In a real system, we'd use the Glassbox to measure the entropy of the status text
        # Here we use a heuristic mock

        urgency = 0.0
        if "error" in system_status_text.lower(): urgency += 0.4
        if "critical" in system_status_text.lower(): urgency += 0.5
        if "offline" in system_status_text.lower(): urgency += 0.3

        if urgency > self.entropy_threshold:
            logger.info(f"[💓] Pulse Triggered: Entropy {urgency}")
            return {
                "trigger": True,
                "vector_modifier": "URGENCY",
                "message": "System entropy is rising. Intervention recommended."
            }

        return {"trigger": False}
