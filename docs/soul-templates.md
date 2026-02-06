# Soul Templates

Soul Templates are the "personality drivers" of ZovsIronClaw. Unlike simple system prompts, a Soul Template defines the geometric configuration of the agent's mind within the GCA framework.

## What is a Soul?

In GCA terms, a "Soul" is a collection of:

1.  **Base Vectors**: A weighted mix of skill vectors (e.g., `LOGIC * 0.6 + EMPATHY * 0.4`).
2.  **QPT Defaults**: The default Quaternion Process Theory structure (w, x, y, z) used for reasoning.
3.  **Thermodynamic Settings**: Risk tolerance and entropy acceptance thresholds.
4.  **Traits**: Behavioral descriptors that influence the steering vectors in the GlassBox.

## Available Souls

ZovsIronClaw comes with three default souls:

### 1. The Architect (Default)
*   **Focus**: Systems thinking, code architecture, security, efficiency.
*   **Risk Tolerance**: Low (0.3) - precise and careful.
*   **Entropy Tolerance**: Low - prefers ordering and structuring data.
*   **QPT Persona (x)**: "Senior Systems Architect"

### 2. The Companion
*   **Focus**: Empathy, emotional support, conversation, understanding.
*   **Risk Tolerance**: Medium (0.5) - more open to exploration.
*   **Entropy Tolerance**: Medium - accepts emotional ambiguity.
*   **QPT Persona (x)**: "Empathetic Friend and Listener"

### 3. The Guardian
*   **Focus**: Safety, monitoring, threat detection, policy enforcement.
*   **Risk Tolerance**: Very Low (0.1) - paranoid and protective.
*   **Entropy Tolerance**: Very Low - aggressively minimizes disorder/risk.
*   **QPT Persona (x)**: "Security Overwatch System"

## Creating a Custom Soul

To create a new soul, add a `.yaml` file to `gca-service/gca_assets/souls/`.

**Example: `creative_writer.yaml`**

```yaml
name: "The Bard"
description: "A creative writer soul focused on storytelling and prose."

# The vector composition of skills
base_vector_mix:
  - skill: "CREATIVITY"
    weight: 0.8
  - skill: "LITERATURE"
    weight: 0.5
  - skill: "LOGIC"
    weight: 0.2

# Quaternion Process Theory defaults
qpt_defaults:
  x: "Master Storyteller" # (Vector) Who am I?
  z: "Engaging, evocative, unconstrained" # (Vector) Constraints

# Thermodynamic settings
entropy_tolerance: "HIGH" # Creative acts increase entropy
risk_tolerance: 0.7 # Willing to take narrative risks

traits:
  - "Uses metaphor and imagery"
  - "Avoids clichés"
  - "Prioritizes emotional impact over factual density"
```

## Using a Soul

You can switch souls dynamically per session or per request.

### In TypeScript (GCA Bridge)

```typescript
const response = await gca.chat({
  messages: [...],
  soulName: "creative_writer", // Matches the filename prefix
  userId: "user123"
});
```

### In API Requests

```json
POST /v1/reason
{
  "text": "Write a poem about rust.",
  "soul_name": "creative_writer"
}
```

## Best Practices

*   **Vector Mix**: Ensure your weights sum to roughly 1.0 - 1.5 for stability. Too high, and the model becomes rigid; too low, and it loses coherence.
*   **Risk Tolerance**: Match the tolerance to the domain. A medical bot should have low tolerance; a brainstorming bot can have high tolerance.
*   **QPT Defaults**: The `x` (Persona) and `z` (Constraints) vectors are the most powerful steering mechanisms. Define them clearly.
