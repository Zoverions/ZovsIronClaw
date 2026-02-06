"""
Moral Kernel: Thermodynamic Ethics Engine for GCA Framework
Evaluates actions based on entropy, reversibility, and harm potential.
"""

from enum import Enum
from dataclasses import dataclass
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


class MoralKernel:
    """
    The Moral Kernel evaluates actions using thermodynamic principles.
    It acts as a hard gate preventing high-entropy, irreversible actions.
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
        
        return min(entropy, 1.0)
        
    def calculate_risk_score(self, action: Action) -> float:
        """
        Calculate overall risk score combining multiple factors.
        
        Args:
            action: Action to evaluate
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        entropy = self.calculate_entropy_score(action)
        
        # Time horizon factor (longer horizon = more uncertainty)
        time_factor = 1.0 - math.exp(-action.time_horizon_yrs / 5.0)
        
        # Combined risk
        risk = (entropy * 0.6) + (action.prob_harm * 0.3) + (time_factor * 0.1)
        
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
            risk = self.calculate_risk_score(action)
            total_risk += risk
            
            logger.info(
                f"Action: {action.type} | "
                f"Entropy: {action.entropy_class.value} | "
                f"Risk: {risk:.3f}"
            )
            
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
            reason = f"High-risk actions detected: {', '.join(reasons)}"
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
            
        reason = f"All actions approved (avg risk: {avg_risk:.2f})"
        logger.info(f"APPROVED: {reason}")
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
