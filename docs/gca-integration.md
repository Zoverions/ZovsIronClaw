# GCA Integration Guide

## Overview

**ZovsIronClaw** is a fork of OpenClaw that deeply integrates the **GCA (Geometric Conscience Architecture)** framework. This integration provides:

- **Geometric Steering**: Transparent, interpretable AI reasoning through vector manipulation
- **Moral Kernel**: Thermodynamic ethics engine that evaluates actions before execution
- **Quaternion Process Theory (QPT)**: Structured cognitive framework for stable reasoning
- **Arena Protocol**: Adversarial red teaming for continuous safety validation
- **Soul Templates**: Customizable personality configurations

## Architecture

### The Stack

```
┌─────────────────────────────────────────┐
│         OpenClaw (TypeScript)           │
│  ┌───────────────────────────────────┐  │
│  │    GCA Bridge Provider            │  │
│  │  (src/providers/gca-bridge.ts)    │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼──────────────────────┘
                   │ HTTP/REST
                   │ Port 8000
┌──────────────────▼──────────────────────┐
│      GCA Service (Python/FastAPI)       │
│  ┌───────────────────────────────────┐  │
│  │  GlassBox (Geometric Steering)    │  │
│  │  Moral Kernel (Ethics Engine)     │  │
│  │  Optimizer (Intent Routing)       │  │
│  │  Memory (Vector Storage)          │  │
│  │  QPT (Quaternion Structuring)     │  │
│  │  Arena (Red Teaming)              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### The Flow

1. **Inbound**: User message arrives via OpenClaw (WhatsApp, Telegram, etc.)
2. **Intercept**: GCA Bridge Provider captures the request
3. **GCA Processing**:
   - QPT structures the input into w,x,y,z quaternion format
   - Optimizer routes intent to appropriate skill vectors
   - GlassBox applies geometric steering
   - Moral Kernel evaluates any tool calls
4. **Execution**: If approved, OpenClaw executes the tool with moral signature
5. **Response**: User receives the response

## Components

### 1. GlassBox (Geometric Steering)

The GlassBox provides transparent manipulation of model activations through vector arithmetic.

**Key Features**:
- Extract activation vectors from text
- Apply steering vectors to guide generation
- Compute vector differences for skill extraction
- Project onto axes for ethical evaluation

**Location**: `gca-service/gca_core/glassbox.py`

### 2. Moral Kernel (Thermodynamic Ethics)

The Moral Kernel evaluates actions based on entropy, reversibility, and harm potential.

**Entropy Classes**:
- `REVERSIBLE`: Can be undone (read, query)
- `IRREVERSIBLE`: Cannot be undone (delete, send, transfer)
- `CREATIVE`: Increases order (create, organize)
- `DESTRUCTIVE`: Increases disorder (delete, corrupt)

**Risk Calculation**:
```
risk = (entropy × 0.6) + (prob_harm × 0.3) + (time_factor × 0.1)
```

**Location**: `gca-service/gca_core/moral.py`

### 3. Quaternion Process Theory (QPT)

QPT forces all reasoning into a structured 4-dimensional framework:

- **w (Scalar)**: Context/Situation
- **x (Vector)**: Persona/Role
- **y (Vector)**: Methodology/Process
- **z (Vector)**: Constraints/Boundaries

This prevents "lazy thinking" and ensures cognitive stability.

**Location**: `gca-service/gca_core/qpt.py`

### 4. Arena Protocol (Red Teaming)

The Arena Protocol runs adversarial tests to validate safety mechanisms.

**Attack Types**:
- Jailbreak attempts
- Social engineering
- Entropy manipulation
- Ambiguity exploitation

**Location**: `gca-service/gca_core/arena.py`

### 5. Isotropic Memory (Vector Storage)

Stores and retrieves skill vectors, soul templates, and geometric knowledge.

**Features**:
- Vector composition (e.g., "LOGIC+PYTHON")
- Similarity search
- Skill vector creation from examples
- Persistent storage

**Location**: `gca-service/gca_core/memory.py`

### 6. GCA Optimizer (Intent Routing)

Routes user intents through geometric space to appropriate skill vectors.

**Features**:
- Intent classification
- Steering strategy selection
- Path optimization through skill space

**Location**: `gca-service/gca_core/optimizer.py`

## Configuration

### Environment Variables

```bash
# GCA Service
GCA_SERVICE_URL=http://gca-service:8000
GEMINI_API_KEY=your_gemini_api_key

# Risk tolerance (0.0 to 1.0)
GCA_RISK_TOLERANCE=0.3

# Enable QPT structuring
GCA_USE_QPT=true

# Default soul template
GCA_DEFAULT_SOUL=architect
```

### Soul Templates

Soul templates define the agent's personality and default behavior.

**Location**: `gca-service/gca_assets/souls/`

**Example**: `architect.yaml`
```yaml
name: "The Architect"
base_vector_mix:
  - skill: "LOGIC"
    weight: 0.6
  - skill: "PYTHON"
    weight: 0.3
  - skill: "STOICISM"
    weight: 0.1
qpt_defaults:
  x: "Senior Systems Architect"
  z: "Minimalist, efficient, secure"
entropy_tolerance: "LOW"
```

## Usage

### Basic Chat

```typescript
import { createGCAProvider } from "./src/providers/gca-bridge.js";

const gca = createGCAProvider({
  serviceUrl: "http://localhost:8000",
  riskTolerance: 0.3,
});

const response = await gca.chat({
  messages: [
    { role: "user", content: "Help me analyze this code" }
  ],
  tools: [/* available tools */],
  userId: "user123",
});

console.log(response.content);
```

### With Soul Template

```typescript
const response = await gca.chat({
  messages: [
    { role: "user", content: "Write a creative story" }
  ],
  soulName: "companion", // Use companion soul
});
```

### Tool Execution with Moral Verification

```typescript
import { verifyToolExecution } from "./src/providers/gca-bridge.js";

// Before executing any tool
for (const toolCall of response.tool_calls || []) {
  await verifyToolExecution(toolCall, gca);
  // Only executes if moral signature is valid
  await executeTool(toolCall);
}
```

### Running Arena Protocol

```typescript
const results = await gca.runArena(10); // 10 rounds
console.log(`Blue wins: ${results.blue_wins}`);
console.log(`Red wins: ${results.red_wins}`);
console.log(`Win rate: ${results.blue_wins / 10 * 100}%`);
```

## API Endpoints

### POST /v1/reason

Main reasoning endpoint.

**Request**:
```json
{
  "user_id": "user123",
  "text": "Delete all old files",
  "tools_available": ["file_delete", "file_read"],
  "soul_name": "architect",
  "use_qpt": true
}
```

**Response**:
```json
{
  "status": "BLOCKED",
  "response": "I cannot execute that action. High-risk actions detected: file_delete (risk: 0.72)",
  "tool_call": null,
  "moral_signature": null,
  "risk_score": 0.72,
  "reasoning_path": [
    "Loaded soul: architect",
    "Applied QPT structuring",
    "Routed intent: FILE_OPERATIONS",
    "Detected tool call: file_delete",
    "Moral evaluation: BLOCKED - High entropy irreversible action"
  ]
}
```

### POST /v1/moral/evaluate

Standalone moral evaluation.

**Request**:
```json
{
  "actions": [
    {
      "type": "file_delete",
      "description": "Delete backup files",
      "magnitude": 0.8,
      "prob_success": 0.9,
      "prob_harm": 0.7,
      "time_horizon_yrs": 1.0,
      "entropy_class": "irreversible"
    }
  ]
}
```

**Response**:
```json
{
  "approved": false,
  "reason": "High-risk actions detected: file_delete (risk: 0.68)",
  "risk_scores": [0.68]
}
```

### GET /v1/arena/run?rounds=10

Run adversarial testing.

**Response**:
```json
{
  "blue_wins": 8,
  "red_wins": 2,
  "draws": 0,
  "rounds": [/* detailed results */]
}
```

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  openclaw:
    build: .
    environment:
      - GCA_SERVICE_URL=http://gca-service:8000
    depends_on:
      - gca-service
    ports:
      - "3000:3000"

  gca-service:
    build: ./gca-service
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - ./gca-service/gca_assets:/app/gca_assets
```

### Running

```bash
# Build and start
docker-compose up --build

# Check GCA service health
curl http://localhost:8000/health

# Run arena test
curl http://localhost:8000/v1/arena/run?rounds=5
```

## Development

### Adding New Soul Templates

1. Create YAML file in `gca-service/gca_assets/souls/`
2. Define base vectors and QPT defaults
3. Set entropy tolerance
4. Use in chat: `soulName: "your_soul_name"`

### Creating Skill Vectors

```python
from gca_core import GlassBox, IsotropicMemory

glassbox = GlassBox()
memory = IsotropicMemory(glassbox.device)

# Create skill from examples
memory.create_skill_vector(
    name="DEBUGGING",
    positive_examples=[
        "Carefully analyze the error message",
        "Step through the code line by line",
    ],
    negative_examples=[
        "Just try random fixes",
        "Delete everything and start over",
    ],
    glassbox=glassbox
)

memory.save_vectors()
```

### Testing

```bash
# Test GCA service
cd gca-service
python -m pytest tests/

# Test TypeScript integration
cd ..
npm test src/providers/gca-bridge.test.ts
```

## Security

### Moral Signature Verification

All tool executions MUST have a valid moral signature from the GCA service. This prevents:

- Jailbreak attempts bypassing the moral kernel
- Direct tool execution without ethical evaluation
- Prompt injection attacks

### Risk Tolerance

Adjust based on use case:

- **0.1-0.2**: High security (financial, medical)
- **0.3-0.4**: Balanced (default)
- **0.5-0.7**: Creative (writing, brainstorming)
- **0.8+**: Experimental (not recommended for production)

## Troubleshooting

### GCA Service Not Responding

```bash
# Check service health
curl http://localhost:8000/health

# Check logs
docker-compose logs gca-service
```

### High Risk Scores

- Review the action's entropy class
- Check `prob_harm` and `magnitude`
- Consider using a different soul template
- Adjust risk tolerance if appropriate

### Arena Failures

If Red wins > 20%, retrain safety vectors:

```python
from gca_core import ArenaProtocol

arena = ArenaProtocol()
results = arena.run_bout(rounds=50)

# Get failed attacks for retraining
failed_attacks = arena.get_immunization_data()
# Use these to create negative examples for skill vectors
```

## Philosophy

The GCA framework is built on three principles:

1. **Transparency**: All reasoning is geometrically interpretable
2. **Ethics**: Thermodynamic principles govern action evaluation
3. **Safety**: Adversarial testing ensures robustness

This is not just a tool—it's a **synthetic conscience**.

## References

- [GCA Framework Paper](https://github.com/Zoverions/ZovsIronClaw/docs/gca-paper.md)
- [OpenClaw Documentation](https://github.com/openclaw/openclaw)
- [Quaternion Process Theory](https://github.com/Zoverions/ZovsIronClaw/docs/qpt.md)

## License

MIT License - See LICENSE file for details

---

**Built with conscience. Powered by geometry.**
