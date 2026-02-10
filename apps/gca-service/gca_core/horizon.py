"""
Horizon Scanner: Detecting the Emergent Horizon.
Operationalizes the Zoverions philosophy:
- Layer 0: Thermodynamics (Variance Alarm)
- Layer 1: Biology (Outlier Integration)
- Layer 2: Game Theory (Geodesic Extrapolation)
"""

import numpy as np
import logging
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Deque

logger = logging.getLogger("GCA.Horizon")

@dataclass
class HorizonState:
    variance: float
    is_critical_variance: bool
    outliers_count: int
    prediction: Optional[str] = None

class HorizonScanner:
    def __init__(self, glassbox, window_size: int = 50, variance_threshold: float = 0.15):
        """
        Args:
            glassbox: The LLM engine for prediction.
            window_size: Number of past free energy states to track for variance.
            variance_threshold: The variance level that triggers a 'Horizon Event'.
        """
        self.glassbox = glassbox
        self.window_size = window_size
        self.variance_threshold = variance_threshold

        # Layer 0: Variance Tracking
        self.history: Deque[float] = deque(maxlen=window_size)

        # Layer 1: Outlier Storage
        # Store tuples of (free_energy, context_snippet)
        self.outliers: Deque[str] = deque(maxlen=20)

        # Layer 2: Prediction Cache
        self.last_prediction: Optional[str] = None

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
                outlier_entry = f"FE={free_energy:.2f} (Z={z_score:.1f}): {snippet}..."

                # Check for duplicates before adding
                if not any(snippet in o for o in self.outliers):
                    self.outliers.append(outlier_entry)
                    logger.info(f"[HORIZON] Outlier Detected (Z={z_score:.2f}): {snippet}")

        # 4. Check Variance Alarm
        # "Look for Variance Spikes, not Average Shifts."
        is_critical = variance > self.variance_threshold
        if is_critical:
             # Log sparingly to avoid spam
             if np.random.rand() < 0.1:
                logger.warning(f"[HORIZON] Critical Variance: {variance:.4f} (Threshold: {self.variance_threshold})")

        return HorizonState(variance, is_critical, len(self.outliers))

    def predict_geodesic(self) -> str:
        """
        Layer 3: The Geodesic Extrapolation.
        "Plot the Path of Least Resistance."
        """
        if len(self.outliers) < 3:
             return "Insufficient anomalies to predict horizon."

        # Construct Prompt for the GlassBox
        prompt = (
            "SYSTEM: Horizon Scanning Protocol Initiated.\n"
            "TASK: Analyze the following rejected data points (anomalies) to detect the emergent future.\n"
            "METHOD: Ignore rhetoric. Focus on incentives and energy minimization. Find the 'Strange Attractor'.\n\n"
            "ANOMALIES:\n" +
            "\n".join([f"- {o}" for o in list(self.outliers)[-5:]]) +
            "\n\nPREDICTION (The Geodesic Path):"
        )

        try:
            # Use generate_steered (standard generation without steering vector)
            response = self.glassbox.generate_steered(prompt, max_tokens=300)
            self.last_prediction = response
            return response
        except Exception as e:
            logger.error(f"Horizon prediction failed: {e}")
            return f"Prediction Error: {e}"
