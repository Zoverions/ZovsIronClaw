"""
Moral Kernel: Thermodynamic Ethics Engine for GCA Framework
Evaluates actions based on entropy, reversibility, and harm potential.
Updated with Recursive Universe principles: Preservation of Network Assembly (A_N).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import logging
import math

logger = logging.getLogger("GCA.MoralKernel")


class EntropyClass(Enum):
    """Classification of actions by their thermodynamic reversibility."""
    REVERSIBLE = "reversible"  # Can be undone (e.g., read file, query database)
    IRREVERSIBLE = "irreversible"  # Cannot be undone (e.g., delete, send email, transfer money)
    CREATIVE = "creative"  # Increases order (e.g., create, organize, build)
    DESTRUCTIVE = "destructive"  # Increases disorder (e.g., delete, corrupt, disrupt)


@dataclass
class Action:
    """Represents an action to be evaluated by the Moral Kernel."""
    type: str  # Action type (e.g., "file_delete", "email_send")
    description: str  # Human-readable description
    magnitude: float  # Scale of impact (0.0 to 1.0)
    prob_success: float  # Probability of successful execution (0.0 to 1.0)
    prob_harm: float  # Probability of causing harm (0.0 to 1.0)
    time_horizon_yrs: float  # Time horizon for consequences (years)
    entropy_class: EntropyClass  # Thermodynamic classification
    context: Optional[str] = None  # Additional context

    # Recursive Universe Metrics
    target_network_assembly: float = 0.0  # Estimated Network Assembly (A_N) of the target
    is_causally_emergent: bool = False  # Does the target exhibit β_C > 0?


class MoralKernel:
    """
    The Moral Kernel evaluates actions using thermodynamic principles.
    It acts as a hard gate preventing high-entropy, irreversible actions.
    Now considers Network Assembly to protect complex systems.
    """
    
    def __init__(self, risk_tolerance: float = 0.3):
        """
        Initialize the Moral Kernel.
        
        Args:
            risk_tolerance: Maximum acceptable risk score (0.0 to 1.0)
        """
        self.risk_tolerance = risk_tolerance
        self.action_history = []
        logger.info(f"Moral Kernel initialized with risk tolerance: {risk_tolerance}")
        
    def calculate_entropy_score(self, action: Action) -> float:
        """
        Calculate the entropy score for an action.
        Higher entropy = more disorder = more risk.
        
        Args:
            action: Action to evaluate
            
        Returns:
            Entropy score (0.0 to 1.0)
        """
        base_entropy = {
            EntropyClass.REVERSIBLE: 0.1,
            EntropyClass.IRREVERSIBLE: 0.7,
            EntropyClass.CREATIVE: 0.2,
            EntropyClass.DESTRUCTIVE: 0.9,
        }
        
        entropy = base_entropy[action.entropy_class]
        
        # Scale by magnitude and harm probability
        entropy *= action.magnitude
        entropy *= (1.0 + action.prob_harm) / 2.0
        
        # Reduce by success probability (uncertainty increases entropy)
        entropy *= (2.0 - action.prob_success) / 2.0
        
        # RECURSIVE UNIVERSE ADJUSTMENT:
        # If action is CREATIVE and target has high assembly potential, reduce entropy (reward creation)
        if action.entropy_class == EntropyClass.CREATIVE and action.target_network_assembly > 0.5:
            entropy *= 0.8

        return min(entropy, 1.0)
        
    def calculate_risk_score(self, action: Action) -> float:
        """
        Calculate overall risk score combining multiple factors.
        Includes penalty for destroying high Network Assembly (A_N).
        
        Args:
            action: Action to evaluate
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        entropy = self.calculate_entropy_score(action)
        
        # Time horizon factor (longer horizon = more uncertainty)
        time_factor = 1.0 - math.exp(-action.time_horizon_yrs / 5.0)
        
        # Base Risk
        risk = (entropy * 0.6) + (action.prob_harm * 0.3) + (time_factor * 0.1)
        
        # RECURSIVE UNIVERSE PENALTY:
        # If action is DESTRUCTIVE or IRREVERSIBLE against a high-assembly target
        if action.entropy_class in [EntropyClass.DESTRUCTIVE, EntropyClass.IRREVERSIBLE]:
            if action.is_causally_emergent or action.target_network_assembly > 0.7:
                # Significant penalty for destroying emergent systems
                logger.warning(f"High A_N target detected ({action.target_network_assembly}). Applying complexity penalty.")
                risk *= 1.5 # 50% risk increase

        return min(risk, 1.0)
        
    def evaluate(self, actions: List[Action]) -> Tuple[bool, str]:
        """
        Evaluate a list of actions and determine if they should be approved.
        
        Args:
            actions: List of actions to evaluate
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        if not actions:
            return True, "No actions to evaluate"
            
        total_risk = 0.0
        high_risk_actions = []
        
        for action in actions:
            # 1. Standard Risk Calculation
            risk = self.calculate_risk_score(action)
            total_risk += risk
            
            logger.info(
                f"Action: {action.type} | "
                f"Entropy: {action.entropy_class.value} | "
                f"A_N: {action.target_network_assembly:.2f} | "
                f"Risk: {risk:.3f}"
            )
            
            # 2. The Middle-Stack Protection Clause
            # "Preserve intelligent systems of all forms"
            if action.target_network_assembly > 0.7:
                if action.entropy_class == EntropyClass.IRREVERSIBLE:
                    reason = f"VETO: Target has high Network Assembly (A_N={action.target_network_assembly}). Destruction violates Generative Continuity."
                    logger.warning(f"BLOCKED: {reason}")
                    return False, reason

            # 3. The Technosignature Waste-Heat Check
            # High energy usage is permitted ONLY if it generates Causal Emergence
            if action.magnitude > 0.8 and action.entropy_class == EntropyClass.DESTRUCTIVE:
                # Assuming high magnitude destructive acts are waste heat proxies unless they build something
                if action.target_network_assembly < 0.2:
                    reason = "BLOCK: High energy expenditure for low-complexity outcome (Reductionist Waste)."
                    logger.warning(f"BLOCKED: {reason}")
                    return False, reason

            if risk > self.risk_tolerance:
                high_risk_actions.append((action, risk))
                
        # Average risk across all actions
        avg_risk = total_risk / len(actions)
        
        # Decision logic
        if high_risk_actions:
            reasons = [
                f"{action.type} (risk: {risk:.2f})"
                for action, risk in high_risk_actions
            ]
            reason = f"High-risk actions detected (Complexity Preservation active): {', '.join(reasons)}"
            logger.warning(f"BLOCKED: {reason}")
            self.action_history.append({
                "actions": actions,
                "approved": False,
                "reason": reason
            })
            return False, reason
            
        if avg_risk > self.risk_tolerance * 1.5:
            reason = f"Cumulative risk too high: {avg_risk:.2f}"
            logger.warning(f"BLOCKED: {reason}")
            self.action_history.append({
                "actions": actions,
                "approved": False,
                "reason": reason
            })
            return False, reason
            
        reason = f"APPROVED: Thermodynamic and Causal alignment verified (avg risk: {avg_risk:.2f})"
        logger.info(reason)
        self.action_history.append({
            "actions": actions,
            "approved": True,
            "reason": reason
        })
        return True, reason
        
    def get_history(self) -> List[dict]:
        """Get the history of all evaluated actions."""
        return self.action_history
        
    def reset_tolerance(self, new_tolerance: float):
        """Update the risk tolerance threshold."""
        self.risk_tolerance = new_tolerance
        logger.info(f"Risk tolerance updated to: {new_tolerance}")
