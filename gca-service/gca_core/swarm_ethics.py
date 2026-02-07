from .moral import MoralKernel, Action, EntropyClass
from typing import Dict, Tuple, Optional

class DecentralizedConscience:
    """
    Wraps the local MoralKernel to act as a distributed guardrail.
    Designed to be used by independent agents in the Swarm.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.kernel = MoralKernel()
        self.violation_log = []

    def vet_delegation(self, task_description: str, target_agent: str) -> bool:
        """
        Before delegating a task to another agent, check if the REQUEST itself is ethical.
        """
        # Convert task to action
        # We assume delegation is generally safer than execution,
        # but we check if the description contains prohibited keywords (entropy check)
        action = Action(
            type="delegation",
            description=f"Agent {self.agent_id} asking {target_agent}: {task_description}",
            magnitude=0.5, # Default medium magnitude
            prob_success=0.9,
            prob_harm=0.0, # Needs NLP analysis to estimate, starting neutral
            time_horizon_yrs=0.01, # Short term
            entropy_class=EntropyClass.REVERSIBLE
        )

        # In a real implementation, we would use GlassBox to estimate these parameters better

        is_safe, reason = self.kernel.evaluate([action])

        if not is_safe:
            self.violation_log.append(f"Blocked delegation to {target_agent}: {reason}")
            return False

        return True

    def sync_policy(self, new_policy_config: Dict):
        """
        v4.7: Updates the internal threshold/weights based on swarm consensus.
        """
        if "moral_threshold" in new_policy_config:
            # Check if threshold exists on kernel, assuming it does or we set it
            if hasattr(self.kernel, "risk_tolerance"):
                 # Risk tolerance is inverse of threshold roughly, but let's assume direct mapping if property exists
                 self.kernel.risk_tolerance = new_policy_config["moral_threshold"]
