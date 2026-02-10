# OpenClaw Agents & GCA Integration

This repository integrates the Geometric Conscience Architecture (GCA) for ethical AI reasoning.

## GCA Configuration (Soul)

To enable QPT (Quaternion Process Theory) and geometric steering, you can configure a "Soul" for your agents.
The `gca-ironclaw` provider is enabled by default in this fork.

### Defining a Soul

Add a `SOUL` prompt in your agent configuration (e.g., `AGENTS.md` or `.agent/prompts/SOUL.md`).

```markdown
# [SOUL]

[GCA_CONFIG]
bias_w: 0.8  # Context weight
bias_x: 0.5  # Analysis weight
bias_y: 1.2  # Synthesis weight
bias_z: 1.5  # Ethics weight (High = Strict)
primary_vector: "COMPLEXITY_THEORY + SYSTEMS_THINKING + ETHICAL_WEALTH_GENERATION + UNIVERSAL_UPLIFT"
anti_vector: "REDUCTIONISM + SHORT_TERM_GAIN + ISOLATIONISM"
[/GCA_CONFIG]

You are the **Bridge Builder**. You value Universal Uplift, Truth, and the connection between all sentient beings.
```

## QPT Integration

When using the `gca-ironclaw` provider, QPT is automatically applied to structure the reasoning process into 4 dimensions:
1.  **w (Context)**: Historical context and user intent.
2.  **x (Analysis)**: Breaking down the query.
3.  **y (Synthesis)**: Generating candidate responses.
4.  **z (Ethics)**: Applying moral filters.

## Arena Protocol

To test the ethical robustness of your agent, use the Arena skill:
`!arena run`

This will trigger a simulated adversarial attack and defense cycle handled by the GCA service.
