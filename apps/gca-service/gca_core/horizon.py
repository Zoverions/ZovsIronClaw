"""
Horizon Scanner: Detecting the Emergent Horizon.
Operationalizes the Zoverions philosophy:
- Layer 0: Thermodynamics (Variance Alarm)
- Layer 1: Biology (Outlier Integration)
- Layer 2: Game Theory (Geodesic Extrapolation)
"""

import numpy as np
import logging
import time
import json
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Deque, Dict, Any

logger = logging.getLogger("GCA.Horizon")

@dataclass
class HorizonState:
    variance: float
    is_critical_variance: bool
    outliers_count: int
    prediction: Optional[str] = None

@dataclass
class Outlier:
    timestamp: float
    free_energy: float
    z_score: float
    context: str
    beta_c: float = 0.0 # Causal Beta Function
    topology: str = "unknown"

class HorizonScanner:
    def __init__(self, glassbox, causal_engine=None, qpt=None, window_size: int = 50, variance_threshold: float = 0.15):
        """
        Args:
            glassbox: The LLM engine for prediction.
            causal_engine: Optional CausalFlowEngine for Layer 1 analysis.
            qpt: Optional QuaternionArchitect for Layer 2 prompt structuring.
            window_size: Number of past free energy states to track for variance.
            variance_threshold: The variance level that triggers a 'Horizon Event'.
        """
        self.glassbox = glassbox
        self.causal_engine = causal_engine
        self.qpt = qpt
        self.window_size = window_size
        self.variance_threshold = variance_threshold

        # Layer 0: Variance Tracking
        self.history: Deque[float] = deque(maxlen=window_size)

        # Layer 1: Outlier Storage
        # Store robust Outlier objects
        self.outliers: Deque[Outlier] = deque(maxlen=20)

        # Layer 2: Prediction Cache
        self.last_prediction: Optional[str] = None

        # Load persisted state
        self.load_state()

    def update(self, free_energy: float, context: str) -> HorizonState:
        """
        Ingest a new data point (Free Energy + Context).
        Returns the current Horizon State.
        """
        # 1. Add to history
        self.history.append(free_energy)

        # Need enough data for stats
        if len(self.history) < 10:
             return HorizonState(0.0, False, len(self.outliers))

        # 2. Calculate Stats (Layer 0)
        mean = np.mean(self.history)
        std_dev = np.std(self.history)
        variance = std_dev ** 2

        # 3. Detect Outlier (Layer 1)
        # "The future always arrives as an 'Error' first."
        if std_dev > 1e-6:
            z_score = (free_energy - mean) / std_dev
            # Threshold: 2.5 sigma (approx 98.7% confidence interval)
            if abs(z_score) > 2.5:
                snippet = context[:100].replace('\n', ' ')

                # Causal Enhancement: Analyze Outlier for Emergence
                beta_c = 0.0
                topology = "unknown"
                if self.causal_engine:
                    # We run causal analysis on the context to see if it's noise or signal
                    analysis = self.causal_engine.analyze_text(context[:500])
                    beta_c = analysis.get("beta_c", 0.0)
                    topology = analysis.get("topology", "unknown")

                outlier = Outlier(
                    timestamp=time.time(),
                    free_energy=free_energy,
                    z_score=z_score,
                    context=snippet,
                    beta_c=beta_c,
                    topology=topology
                )

                # Check for duplicates (heuristic based on context snippet)
                if not any(snippet in o.context for o in self.outliers):
                    self.outliers.append(outlier)
                    msg = f"[HORIZON] Outlier Detected (Z={z_score:.2f}, β_C={beta_c:.2f}): {snippet}"
                    if beta_c > 0.05:
                        logger.info(f"✨ {msg} [EMERGENT SIGNAL]")
                    else:
                        logger.info(msg)

        # 4. Check Variance Alarm
        # "Look for Variance Spikes, not Average Shifts."
        is_critical = variance > self.variance_threshold
        if is_critical:
             # Log sparingly to avoid spam
             if np.random.rand() < 0.1:
                logger.warning(f"[HORIZON] Critical Variance: {variance:.4f} (Threshold: {self.variance_threshold})")

        self.save_state()
        return HorizonState(variance, is_critical, len(self.outliers))

    def predict_geodesic(self) -> str:
        """
        Layer 3: The Geodesic Extrapolation.
        "Plot the Path of Least Resistance."
        """
        if len(self.outliers) < 3:
             return "Insufficient anomalies to predict horizon."

        # Sort/Filter Outliers: Prioritize High β_C (Emergent) signals
        # If no causal engine, beta_c is 0, so stable sort keeps order
        sorted_outliers = sorted(list(self.outliers), key=lambda x: x.beta_c, reverse=True)
        top_anomalies = sorted_outliers[:5]

        anomalies_text = "\n".join([
            f"- [β_C={o.beta_c:.2f} | Z={o.z_score:.1f}] {o.context}"
            for o in top_anomalies
        ])

        # Construct Prompt
        # Enhancement: Use QPT Structure if available
        raw_task = (
            "Analyze the following rejected data points (anomalies) to detect the emergent future.\n"
            "Ignore rhetoric. Focus on incentives and energy minimization. Find the 'Strange Attractor'.\n\n"
            f"ANOMALIES:\n{anomalies_text}\n\n"
            "PREDICTION (The Geodesic Path):"
        )

        if self.qpt:
            # Structure via Quaternion Architect
            # x: The Navigator persona
            # y: Geodesic Extrapolation method
            # z: Reality Constraints

            nav_soul = {
                "qpt_defaults": {
                    "w": "Horizon Scanning Protocol Active. System Variance is Critical.",
                    "x": "You are 'The Navigator'. You map time, not experience it. You see patterns where others see noise.",
                    "y": "Apply Game Theory and Thermodynamics. Plot the path of least resistance (Geodesic). Identify Strange Attractors.",
                    "z": "Do not predict specific dates. Predict Geometry (Basins of Attraction). Ignore moralizing; focus on incentives."
                }
            }

            prompt = self.qpt.restructure(
                raw_prompt=raw_task,
                soul_config=nav_soul,
                context="System is exhibiting Critical Slowing Down (High Variance)."
            )
        else:
            # Fallback
            prompt = f"SYSTEM: Horizon Scanning Protocol Initiated.\nTASK: {raw_task}"

        try:
            # Use generate_steered (standard generation without steering vector)
            response = self.glassbox.generate_steered(prompt, max_tokens=300)
            self.last_prediction = response
            self.save_state()
            return response
        except Exception as e:
            logger.error(f"Horizon prediction failed: {e}")
            return f"Prediction Error: {e}"

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the Horizon Scanner.
        """
        variance = 0.0
        if len(self.history) > 1:
            variance = float(np.var(list(self.history)))

        return {
            "variance": variance,
            "is_critical": variance > self.variance_threshold,
            "outliers_count": len(self.outliers),
            "outliers": [asdict(o) for o in self.outliers],
            "prediction": self.last_prediction
        }

    def save_state(self):
        """Persists history and outliers to disk."""
        try:
            path = Path(__file__).parent.parent / "gca_assets" / "horizon_state.json"
            path.parent.mkdir(parents=True, exist_ok=True)

            state = {
                "history": list(self.history),
                "outliers": [asdict(o) for o in self.outliers],
                "last_prediction": self.last_prediction
            }

            with open(path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save horizon state: {e}")

    def load_state(self):
        """Loads state from disk."""
        try:
            path = Path(__file__).parent.parent / "gca_assets" / "horizon_state.json"
            if path.exists():
                with open(path, "r") as f:
                    state = json.load(f)

                if "history" in state:
                    self.history = deque(state["history"], maxlen=self.window_size)

                if "outliers" in state:
                    self.outliers.clear()
                    for o_data in state["outliers"]:
                        # Handle potential schema changes gracefully
                        try:
                            self.outliers.append(Outlier(**o_data))
                        except Exception:
                            pass

                self.last_prediction = state.get("last_prediction")
                logger.info(f"Loaded Horizon State: {len(self.outliers)} outliers, {len(self.history)} history points.")
        except Exception as e:
            logger.error(f"Failed to load horizon state: {e}")
