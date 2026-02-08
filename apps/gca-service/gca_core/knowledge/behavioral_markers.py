"""
Behavioral Markers Knowledge Base
Grounded in behavioral science research (e.g., Ekman's FACS, Russell's Circumplex Model).

Maps observable cues (text descriptions from VLM/Audio models) to GCA State Vectors.
State Vector Components: [Entropy, Focus, Valence, Arousal]
- Entropy: Disorder/Stress (0=Order, 1=Chaos)
- Focus: Attention/Cognitive Load (0=Distracted, 1=Flow)
- Valence: Emotional Positivity (0=Negative, 1=Positive)
- Arousal: Energy Level (0=Low, 1=High)
"""

MARKERS = {
    "vision": {
        # Facial Action Coding System (FACS) proxies
        "furrowed_brow": {"entropy": 0.7, "focus": 0.8, "valence": 0.3, "arousal": 0.6}, # AU 4: Concentration or Anger
        "wide_eyes": {"entropy": 0.6, "focus": 0.5, "valence": 0.5, "arousal": 0.9}, # AU 5: Surprise/Fear
        "slumped_posture": {"entropy": 0.4, "focus": 0.2, "valence": 0.3, "arousal": 0.2}, # Low energy
        "smiling": {"entropy": 0.2, "focus": 0.5, "valence": 0.9, "arousal": 0.6}, # AU 12
        "looking_away": {"entropy": 0.5, "focus": 0.1, "valence": 0.5, "arousal": 0.4}, # Distraction
        "rubbing_face": {"entropy": 0.8, "focus": 0.4, "valence": 0.3, "arousal": 0.5}, # Stress/Fatigue
        "neutral_expression": {"entropy": 0.3, "focus": 0.6, "valence": 0.5, "arousal": 0.4},
        "leaning_forward": {"entropy": 0.3, "focus": 0.9, "valence": 0.6, "arousal": 0.7}, # Engagement
    },
    "audio": {
        # Prosodic features
        "rapid_speech": {"entropy": 0.7, "focus": 0.6, "valence": 0.5, "arousal": 0.9},
        "slow_speech": {"entropy": 0.3, "focus": 0.4, "valence": 0.4, "arousal": 0.2},
        "high_pitch": {"entropy": 0.6, "focus": 0.5, "valence": 0.6, "arousal": 0.8}, # Excitement or Stress
        "monotone": {"entropy": 0.2, "focus": 0.3, "valence": 0.4, "arousal": 0.1}, # Boredom
        "long_pauses": {"entropy": 0.5, "focus": 0.2, "valence": 0.4, "arousal": 0.3}, # Cognitive load or hesitation
        "loud_volume": {"entropy": 0.6, "focus": 0.7, "valence": 0.6, "arousal": 0.9},
        "sighing": {"entropy": 0.4, "focus": 0.3, "valence": 0.2, "arousal": 0.3}, # Relief or Frustration
    }
}

def get_state_from_description(text: str, modality: str = "vision") -> dict:
    """
    Scans the description text for known markers and averages their vectors.
    """
    text = text.lower()
    markers = MARKERS.get(modality, {})

    found_vectors = []

    for cue, vector in markers.items():
        if cue.replace("_", " ") in text or cue in text:
            found_vectors.append(vector)

    if not found_vectors:
        # Default neutral state if no markers found
        return {"entropy": 0.5, "focus": 0.5, "valence": 0.5, "arousal": 0.5}

    # Average the vectors
    avg_vector = {k: 0.0 for k in found_vectors[0].keys()}
    for vec in found_vectors:
        for k, v in vec.items():
            avg_vector[k] += v

    count = len(found_vectors)
    for k in avg_vector:
        avg_vector[k] /= count

    return avg_vector
