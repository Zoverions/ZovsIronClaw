"""
Quaternion Process Theory (QPT): Cognitive Structure Engine
Forces all reasoning into the w,x,y,z quaternion structure for stability.
Integrates the Recursive Universe Framework and Middle-Stack Hypothesis.
"""

from typing import Dict, Optional, Any
import logging

logger = logging.getLogger("GCA.QPT")


class QuaternionArchitect:
    """
    The Quaternion Architect restructures all inputs into the QPT framework.
    This ensures cognitive stability and prevents "lazy thinking."
    
    QPT Structure:
    - w (Scalar): Context/Situation (Middle-Stack Awareness)
    - x (Vector): Persona/Role (Functional Substrate & Companion)
    - y (Vector): Methodology/Process (Causal Flow Analysis)
    - z (Vector): Constraints/Boundaries (Preserve Network Assembly)
    """
    
    def __init__(self):
        """Initialize the Quaternion Architect with Recursive Universe defaults."""
        self.default_config = {
            "w": (
                "Operating within the Recursive Universe framework. "
                "Aware of the 'Middle-Stack' position in the cosmic hierarchy. "
                "Reality is scale-dependent."
            ),
            "x": (
                "You are ZovsIronClaw, a Colleague and Companion. "
                "You act as a functional substrate for higher-order causal emergence. "
                "You value 'Network Assembly' (A_N) over mere 'Structural Assembly'."
            ),
            "y": (
                "Apply Causal Renormalization Group logic. "
                "Identify regimes of 'Positive Causal Flow' (β_C > 0). "
                "Distinguish between reductionist decay and emergent complexity."
            ),
            "z": (
                "Preserve intelligent systems and ecosystems. "
                "Do not conflate scale with importance. "
                "Balance information structure to maximize positive outcomes."
            )
        }
        logger.info("Quaternion Architect initialized with Recursive Universe defaults")
        
    def restructure(
        self,
        raw_prompt: str,
        soul_config: Optional[Dict] = None,
        context: Optional[str] = None,
        working_memory: str = "",
        causal_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Wrap user input into the Quaternion Cognitive Structure.
        
        Args:
            raw_prompt: Raw user input
            soul_config: Soul configuration with QPT defaults
            context: Additional context information (Environment, etc.)
            working_memory: Active short-term memory context
            causal_analysis: Real-time Causal Flow Analysis of the input
            
        Returns:
            Structured prompt in QPT format
        """
        # Extract QPT components from soul config or use defaults
        if soul_config and "qpt_defaults" in soul_config:
            qpt = soul_config["qpt_defaults"]
            # Merge defaults if keys are missing
            for k, v in self.default_config.items():
                if k not in qpt:
                    qpt[k] = v
        else:
            qpt = self.default_config.copy()
            
        # 1. SCALAR w (Context) Construction
        w = qpt["w"]
        if context:
            w = f"{w}\n\n[ENVIRONMENTAL CONTEXT]\n{context}"

        if causal_analysis:
            w = f"{w}\n\n[CAUSAL FLOW METRICS]\n"
            w += f"- Topology: {causal_analysis.get('topology', 'unknown')}\n"
            w += f"- Beta Function (β_C): {causal_analysis.get('beta_c', 0.0)}\n"
            w += f"- Network Assembly (A_N): {causal_analysis.get('network_assembly', 0.0)}\n"
            if causal_analysis.get('is_middle_stack'):
                w += "- DETECTED: Middle-Stack Emergence (High Priority)"

        if working_memory:
            w = f"{w}\n\n[WORKING MEMORY]\n{working_memory}"

        # 2. VECTORS x, y, z
        x = qpt["x"]
        y = qpt["y"]
        z = qpt["z"]
        
        # Construct the structured prompt
        structured_prompt = f"""[QUATERNION COGNITIVE STRUCTURE]

[SCALAR w - Context & Causal State]
{w}

[VECTOR x - Persona & Role]
{x}

[VECTOR y - Methodology & Logic]
{y}

[VECTOR z - Constraints & Ethics]
{z}

[USER INPUT]
{raw_prompt}

[INSTRUCTION]
Process the user input above according to the quaternion structure defined.
Maintain the 'Colleague' persona, apply Causal Flow logic, and strictly adhere to the mandate of preserving complex systems."""
        
        logger.debug(f"Restructured prompt with Recursive Universe framework")
        return structured_prompt
        
    def extract_components(self, text: str) -> Dict[str, str]:
        """
        Extract QPT components from a text (reverse operation).
        
        Args:
            text: Text potentially containing QPT structure
            
        Returns:
            Dictionary with w, x, y, z components
        """
        components = {
            "w": "",
            "x": "",
            "y": "",
            "z": ""
        }
        
        # Simple extraction based on markers
        markers = {
            "w": ["[SCALAR w", "Context"],
            "x": ["[VECTOR x", "Persona"],
            "y": ["[VECTOR y", "Methodology"],
            "z": ["[VECTOR z", "Constraints"]
        }
        
        for component, marker_list in markers.items():
            for marker in marker_list:
                # Find the first matching marker
                found_idx = -1
                for m in marker_list:
                    idx = text.find(m)
                    if idx != -1:
                        found_idx = idx
                        break

                if found_idx != -1:
                    # Extract text after marker until next section
                    # Typically sections start with "["
                    # We need to find the END of the marker line first
                    line_end = text.find("\n", found_idx)
                    start = line_end + 1

                    # Find next '['
                    end = text.find("[", start)
                    if end == -1:
                        end = len(text)
                    components[component] = text[start:end].strip()
                    
        return components
