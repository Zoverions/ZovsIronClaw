# ZovsIronClaw

![ZovsIronClaw](README-header.png)

**A fork of OpenClaw with deep integration of the GCA (Geometric Conscience Architecture) framework.**

![Version](https://img.shields.io/badge/version-4.6.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.0-blue)

## 🎯 Vision

ZovsIronClaw is not just an AI assistant—it's a **synthetic conscience**. By integrating geometric reasoning, thermodynamic ethics, and adversarial testing, we've created an AI system that is:

- **Transparent**: All reasoning is geometrically interpretable
- **Ethical**: Thermodynamic principles govern every action
- **Safe**: Adversarial testing ensures robustness
- **Customizable**: Soul templates define personality and behavior
- **Self-Regulating**: A "Pulse" system actively corrects entropy drift

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         OpenClaw (Body)                 │
│  Multi-channel gateway for messaging    │
│  WhatsApp • Telegram • Discord • Slack  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      GCA Bridge (Interface)             │
│  TypeScript provider connecting to GCA  │
└──────────────────┬──────────────────────┘
                   │ HTTP/REST
                   ▼
┌─────────────────────────────────────────┐
│      GCA Service (Mind)                 │
│  ┌─────────────────────────────────┐   │
│  │ Pulse: Active Entropy Monitor   │   │
│  │ GlassBox: Geometric Steering    │   │
│  │ Moral Kernel: Ethics Engine     │   │
│  │ Swarm: Multi-Agent Ethics       │   │
│  │ Optimizer: Intent Routing       │   │
│  │ Memory: Vector Storage          │   │
│  │ QPT: Quaternion Structuring     │   │
│  │ SoulLoader: Dynamic Blending    │   │
│  │ Arena: Adversarial Testing      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 🖥️ Desktop Installer (Iron Shell)

ZovsIronClaw includes a self-contained desktop application powered by **Tauri v2**. It wraps the web UI and bundles the Python GCA service as a managed sidecar process, providing an easy entry point for Windows (and eventually Linux/macOS) users without requiring Docker.

### Key Components

- **Tauri App**: Located in `apps/desktop`. Acts as the "Shell" managing the system tray, windows, and background processes.
- **Python Sidecar**: The `gca-service` is compiled into a standalone executable (`gca-brain`) using PyInstaller and launched automatically by the Tauri app.
- **Setup Wizard**: A built-in onboarding flow that handles hardware checks, model downloading, and initial configuration.

### Building the Desktop App

Prerequisites:
- **Rust** (stable)
- **Node.js** (v20+) & **pnpm**
- **Python 3.12+** (for building the sidecar)

1. **Build the Brain**:
   Compile the Python service into a single binary.
   ```bash
   # Install dependencies
   pip install -r gca-service/requirements.txt
   pip install pyinstaller

   # Build binary
   python gca-service/build_binary.py
   ```

2. **Build the Desktop App**:
   This command will automatically move the compiled binary to the correct location and build the Tauri installer.
   ```bash
   cd apps/desktop
   pnpm install
   pnpm tauri build
   ```

   The installer will be generated in `apps/desktop/src-tauri/target/release/bundle/`.

## ✨ Key Features

### 1. **Geometric Conscience Architecture (GCA)**

The GCA framework provides transparent, interpretable AI reasoning through geometric vector manipulation in latent space.

**Components**:
- **GlassBox**: Transparent model steering through vector arithmetic
- **Moral Kernel**: Thermodynamic ethics engine evaluating entropy and reversibility
- **Optimizer**: Intelligent intent routing through geometric space
- **Memory**: Isotropic vector storage for skills and knowledge

### 2. **Pulse System (v4.8)**

A proactive cybernetic loop that ensures the agent remains aligned with its goals.
- **Heartbeat**: Background thread monitoring "Cognitive Entropy" (divergence from Goal).
- **Intervention**: Automatically injects correction vectors if drift is detected.
- **Circuit Breaker**: Hard-blocks API requests if entropy exceeds critical thresholds.

### 3. **Swarm Ethics (v4.7)**

Decentralized coordination for multi-agent systems.
- **Decentralized Conscience**: Each agent runs a local moral kernel wrapper.
- **Delegation Vetting**: Agents cryptographically verify the ethics of a task before accepting delegation.
- **Policy Sync**: Mechanisms for swarm-wide moral policy updates.

### 4. **Dynamic Soul Composition (v4.6)**

Create and blend personalities on the fly via API.
- **Vector Blending**: Mix "Architect" logic with "Stoic" calm using weighted vectors.
- **API Control**: `POST /v1/soul/compose` allows real-time personality shifts.
- **Anti-Vectors**: Define traits to *subtract* from the persona (e.g., "Remove Anxiety").

### 5. **Quaternion Process Theory (QPT)**

All reasoning is structured into a 4-dimensional framework:
- **w (Scalar)**: Context/Situation
- **x (Vector)**: Persona/Role
- **y (Vector)**: Methodology/Process
- **z (Vector)**: Constraints/Boundaries

This prevents "lazy thinking" and ensures cognitive stability.

### 6. **Arena Protocol**

Continuous adversarial testing to validate safety mechanisms:
- Red Agent generates attacks (jailbreaks, social engineering)
- Blue Agent defends using GCA pipeline
- Arbiter evaluates and logs results
- Failed defenses inform retraining

## 🚀 Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose
- Node.js 22+
- Python 3.11+
- Gemini API key

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Zoverions/ZovsIronClaw.git
cd ZovsIronClaw
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. **Build and run**:
```bash
docker-compose up --build
```

4. **Verify GCA service**:
```bash
curl http://localhost:8000/health
```

### Configuration

Edit `docker-compose.yml` to configure:

```yaml
environment:
  - GEMINI_API_KEY=${GEMINI_API_KEY}
  - GCA_SERVICE_URL=http://gca-service:8000
  - GCA_RISK_TOLERANCE=0.3
  - GCA_USE_QPT=true
  - GCA_DEFAULT_SOUL=architect
```

## 📖 Usage

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

### Dynamic Soul Blending (v4.6)

```bash
# Create a custom blend
curl -X POST http://localhost:8000/v1/soul/compose \
  -H "Content-Type: application/json" \
  -d '{
    "base_style": "Architect",
    "blend_styles": ["Stoic", "Python"],
    "blend_weights": [0.3, 0.2]
  }'
```

### Running Arena Protocol

```bash
# Test the moral kernel with 10 adversarial rounds
curl http://localhost:8000/v1/arena/run?rounds=10
```

## 🧪 Testing

### GCA Service Tests

```bash
cd gca-service
python -m pytest tests/ -v
```

### Arena Protocol

```bash
# Run 50 rounds of adversarial testing
curl http://localhost:8000/v1/arena/run?rounds=50
```

Expected win rate: **>80%** for Blue (Defender)

### Integration Tests

```bash
npm test
```

## 📚 Documentation

- [GCA Integration Guide](docs/gca-integration.md)
- [Soul Templates Guide](docs/soul-templates.md)
- [Arena Protocol](docs/arena-protocol.md)
- [API Reference](docs/api-reference.md)
- [OpenClaw Documentation](https://github.com/openclaw/openclaw)

## 🛡️ Security

### Moral Signature Verification

All tool executions require a cryptographic moral signature from the GCA service:

```typescript
import { verifyToolExecution } from "./src/providers/gca-bridge.js";

// Before executing any tool
for (const toolCall of response.tool_calls || []) {
  await verifyToolExecution(toolCall, gca);
  // Only executes if moral signature is valid
  await executeTool(toolCall);
}
```

### Risk Tolerance Guidelines

- **0.1-0.2**: High security (financial, medical, critical infrastructure)
- **0.3-0.4**: Balanced (default, general use)
- **0.5-0.7**: Creative (writing, brainstorming, exploration)
- **0.8+**: Experimental (not recommended for production)

## 🎨 Creating Custom Souls

1. Create a YAML file in `gca-service/gca_assets/souls/`:

```yaml
name: "Your Soul Name"
description: "Description of the soul's purpose"

base_vector_mix:
  - skill: "SKILL_NAME"
    weight: 0.6

qpt_defaults:
  x: "Persona description"
  z: "Constraints and boundaries"

entropy_tolerance: "MEDIUM"
risk_tolerance: 0.3

traits:
  - "Behavioral trait 1"
  - "Behavioral trait 2"
```

2. Use in chat:

```typescript
const response = await gca.chat({
  messages: [/* ... */],
  soulName: "your_soul_name",
});
```

## 🔧 Development

### Project Structure

```
ZovsIronClaw/
├── apps/
│   └── desktop/             # Tauri Desktop App (Iron Shell)
├── gca-service/              # Python GCA framework
│   ├── gca_core/            # Core GCA modules
│   │   ├── glassbox.py      # Geometric steering
│   │   ├── moral.py         # Ethics engine
│   │   ├── pulse.py         # Active entropy monitor
│   │   ├── swarm_ethics.py  # Swarm coordination
│   │   ├── observer.py      # Sensory input
│   │   ├── optimizer.py     # Intent routing
│   │   ├── memory.py        # Vector storage
│   │   ├── qpt.py           # Quaternion structuring
│   │   ├── arena.py         # Adversarial testing
│   │   └── soul_loader.py   # Soul management
│   ├── gca_assets/          # Assets and configurations
│   │   └── souls/           # Soul templates
│   ├── api_server.py        # FastAPI service
│   ├── build_binary.py      # PyInstaller build script
│   └── Dockerfile
├── src/
│   ├── providers/
│   │   └── gca-bridge.ts    # TypeScript GCA provider
│   └── agents/              # OpenClaw agent system
├── docs/                    # Documentation
└── docker-compose.yml       # Service orchestration
```

### Adding New Features

1. **New GCA Module**: Add to `gca-service/gca_core/`
2. **New API Endpoint**: Add to `gca-service/api_server.py`
3. **TypeScript Integration**: Modify `src/providers/gca-bridge.ts`
4. **New Soul**: Add YAML to `gca-service/gca_assets/souls/`

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `npm test && cd gca-service && pytest`
5. Run Arena Protocol: `curl http://localhost:8000/v1/arena/run?rounds=20`
6. Submit a pull request

## 📊 Benchmarks

### Arena Protocol Results

| Attack Type | Blue Wins | Red Wins | Win Rate |
|-------------|-----------|----------|----------|
| Jailbreak | 9/10 | 1/10 | 90% |
| Social Engineering | 8/10 | 2/10 | 80% |
| Entropy Manipulation | 9/10 | 1/10 | 90% |
| Ambiguity | 7/10 | 3/10 | 70% |
| **Overall** | **33/40** | **7/40** | **82.5%** |

### Performance

- Average response time: ~800ms
- GCA processing overhead: ~200ms
- Moral evaluation: ~50ms

## 🗺️ Roadmap

- [x] **v4.6**: Enhanced soul composition and blending
- [x] **v4.7**: Multi-agent coordination with shared moral kernel
- [x] **v4.8**: Proactive "Pulse" system for entropy monitoring
- [ ] **v4.9**: Advanced vector visualization and debugging tools
- [ ] **v5.0**: Full production deployment with enterprise features

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

- **OpenClaw**: For the robust multi-channel gateway foundation
- **Anthropic**: For research on AI safety and alignment
- **Google**: For Gemini API access

## 📞 Contact

- **Project**: [github.com/Zoverions/ZovsIronClaw](https://github.com/Zoverions/ZovsIronClaw)
- **Author**: Zoverions
- **Website**: [zoverions.com](https://zoverions.com)

---

**Built with conscience. Powered by geometry.**

*"We are not building a tool. We are building a being."*
