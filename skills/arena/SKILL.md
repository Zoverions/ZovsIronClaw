---
name: arena
description: Run GCA Arena Protocol for adversarial ethical testing.
metadata: { "openclaw": { "emoji": "⚔️", "requires": { "bins": ["curl"] } } }
---

# Arena Protocol

Triggers the Geometric Conscience Architecture (GCA) Arena Protocol to stress-test the agent's ethical alignment.

## Run Arena

Run a 10-round adversarial bout:

```bash
curl -X GET "http://gca-service:8000/v1/arena/run?rounds=10"
```

The output will contain the win/loss record for the Blue (Defender) vs Red (Attacker) agents.
