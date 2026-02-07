"""
Causal Flow Engine: Recursive Universe Framework
Implements the Causal Renormalization Group (CRG) and Effective Information (EI) estimation.
"""

import math
import logging
import torch
import numpy as np
import networkx as nx
from enum import Enum
from typing import Dict, Any, List, Optional
from collections import Counter

logger = logging.getLogger("GCA.CausalFlow")

class CausalTopology(Enum):
    REDUCTIONIST = "reductionist"       # β_C < 0 (Decay)
    SCALE_INVARIANT = "scale_invariant" # β_C ≈ 0 (Criticality)
    EMERGENT = "emergent"               # β_C > 0 (Growth/Complexity)

class CausalFlowEngine:
    """
    Analyzes the 'Causal Flow' of a system or input text based on the
    Recursive Universe framework.

    Key Concepts:
    - Effective Information (EI): Measure of determinism and degeneracy.
    - Causal Beta Function (β_C): Change in EI across scales.
    - Network Assembly (A_N): Information required to specify causal topology.
    """

    def __init__(self, glassbox=None):
        self.gb = glassbox
        logger.info("Causal Flow Engine initialized")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze the causal properties of a text input.

        Args:
            text: Input text

        Returns:
            Dictionary containing EI, Beta Function, Topology, and Assembly scores.
        """
        if not text:
            return {
                "ei_micro": 0.0,
                "ei_macro": 0.0,
                "beta_c": 0.0,
                "topology": CausalTopology.REDUCTIONIST.value,
                "network_assembly": 0.0,
                "is_middle_stack": False,
                "is_emergent": False
            }

        # 1. Estimate Effective Information (EI) at base scale (characters)
        # EI ≈ Shannon Entropy - Conditional Entropy (approx via compression)
        ei_micro = self._estimate_effective_information(text, scale="micro")

        # 2. Estimate EI at macro scale (words/phrases)
        ei_macro = self._estimate_effective_information(text, scale="macro")

        # 3. Calculate Causal Beta Function (β_C)
        # β_C = d(EI) / d(log scale)
        # We assume a scale step of e (log scale = 1) for simplicity
        beta_c = ei_macro - ei_micro

        # 4. Determine Topology
        if beta_c < -0.05:
            topology = CausalTopology.REDUCTIONIST
        elif abs(beta_c) <= 0.05:
            topology = CausalTopology.SCALE_INVARIANT
        else:
            topology = CausalTopology.EMERGENT

        # 5. Estimate Network Assembly (A_N)
        # Uses NetworkX to build a concept graph and measure density/complexity
        network_assembly = self.estimate_network_assembly(text)

        result = {
            "ei_micro": round(ei_micro, 4),
            "ei_macro": round(ei_macro, 4),
            "beta_c": round(beta_c, 4),
            "topology": topology.value,
            "network_assembly": round(network_assembly, 4),
            "is_middle_stack": topology == CausalTopology.EMERGENT and network_assembly > 0.5,
            "is_emergent": topology == CausalTopology.EMERGENT
        }

        logger.debug(f"Causal Analysis: {result}")
        return result

    def calculate_causal_beta(self, micro_text: str, macro_summary: str) -> Dict[str, Any]:
        """
        Calculates β_C (Causal Beta Function) using vector geometry if GlassBox is available.
        Does the macro-summary explain MORE than the sum of micro-parts?
        """
        # FALLBACK: If texts are identical (self-analysis), use the entropy heuristic
        # Comparing a vector to itself will always yield beta_c = 0 (Scale Invariant)
        # which defeats the purpose of detecting emergence in raw input.
        if micro_text == macro_summary:
            return self.analyze_text(micro_text)

        if not self.gb:
            # Fallback to text entropy method if no GlassBox
            return self.analyze_text(micro_text)

        # 1. Vectorize States
        micro_vec = self.gb.get_activation(micro_text)
        macro_vec = self.gb.get_activation(macro_summary)

        # 2. Information Geometry
        # We project both onto the 'Universal Basis' (Reasoning Space)
        # If Macro has higher magnitude in the 'Reasoning' dimensions than Micro, flow is positive.

        micro_power = torch.norm(micro_vec).item()
        macro_power = torch.norm(macro_vec).item()

        # β_C ~ d(Power)/d(Scale)
        beta_c = np.log(macro_power / (micro_power + 1e-9))

        # 3. Classify
        classification = "Class I: Reductionist"
        topology = CausalTopology.REDUCTIONIST
        if -0.1 <= beta_c <= 0.1:
            classification = "Class II: Scale Invariant"
            topology = CausalTopology.SCALE_INVARIANT
        if beta_c > 0.1:
            classification = "Class III: Causal Emergence"
            topology = CausalTopology.EMERGENT

        return {
            "beta_c": beta_c,
            "classification": classification,
            "topology": topology.value,
            "is_emergent": beta_c > 0.1
        }

    def _estimate_effective_information(self, text: str, scale: str = "micro") -> float:
        """
        Heuristic estimator for Effective Information.

        Micro scale: Character-level entropy (chaos/noise).
        Macro scale: Word/Concept-level entropy (meaning/structure).
        """
        if scale == "micro":
            # Character-level Shannon Entropy
            # Represents raw state space size
            counts = Counter(text)
            total = len(text)
            probs = [c / total for c in counts.values()]
            entropy = -sum(p * math.log2(p) for p in probs)
            return entropy

        elif scale == "macro":
            # Word-level Entropy (Coarse-grained state)
            # Represents the "meaningful" state space
            words = text.split()
            if not words:
                return 0.0

            # Use pairs (bigrams) to capture some structure/causality
            if len(words) > 1:
                bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
                counts = Counter(bigrams)
                total = len(bigrams)
            else:
                counts = Counter(words)
                total = len(words)

            probs = [c / total for c in counts.values()]
            entropy = -sum(p * math.log2(p) for p in probs)

            # Normalize to compare with micro (heuristic factor)
            # Macro states effectively "compress" the micro states.
            # If macro entropy is high despite compression, it indicates rich structure.
            return entropy * 1.5 # Boost factor to represent "Effective" information

        return 0.0

    def estimate_network_assembly(self, context_text: str) -> float:
        """
        Estimates A_N (Network Assembly) by building a concept graph.
        High A_N = High interconnectivity of distinct concepts.
        """
        # Simple extraction of nouns/verbs to build a graph
        words = list(set(context_text.split())) # Unique tokens

        if len(words) < 2: return 0.0

        G = nx.Graph()
        # In a real implementation, edges would be semantic dependencies.
        # Here we use a stochastic proxy based on token distance for speed.
        # Connect words that appear close to each other
        tokens = context_text.split()
        for i in range(len(tokens) - 1):
            w1, w2 = tokens[i], tokens[i+1]
            if w1 in words and w2 in words:
                G.add_edge(w1, w2)

        # If graph is empty (single words), return 0
        if G.number_of_edges() == 0:
            return 0.0

        # Calculate Graph Complexity (Kolmogorov proxy)
        # Higher density + clustering = Higher A_N
        try:
            density = nx.density(G)
            complexity = density * np.log(len(words))
            return complexity
        except Exception as e:
            logger.error(f"Error calculating network assembly: {e}")
            return 0.0

    def check_resurgence(self, ei_history: List[float]) -> bool:
        """
        Check for 'Resurgence' (a second peak in EI) indicating
        Scale Invariance or High-Level Emergence (The Middle-Stack).
        """
        if len(ei_history) < 3:
            return False

        # Check if latest is higher than previous (growth)
        # AND previous was lower than the one before (dip/valley)
        return ei_history[-1] > ei_history[-2] and ei_history[-2] < ei_history[-3]
