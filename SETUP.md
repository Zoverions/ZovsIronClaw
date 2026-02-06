# ZovsIronClaw Setup Guide

Complete guide to setting up and running ZovsIronClaw with GCA integration.

## Prerequisites

### Required

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Git**
- **Gemini API Key** (from Google AI Studio)
- **8GB RAM** minimum
- **10GB disk space**

### Optional

- OpenAI API Key
- xAI Grok API Key
- Claude API credentials

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/Zoverions/ZovsIronClaw.git
cd ZovsIronClaw
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.ironclaw.example .env.ironclaw

# Edit with your API keys
nano .env.ironclaw  # or use your preferred editor
```

**Minimum required configuration**:
```bash
GEMINI_API_KEY=your_actual_gemini_api_key_here
OPENCLAW_GATEWAY_TOKEN=any_secure_random_string
```

### 3. Build

```bash
./scripts/build-ironclaw.sh
```

This will:
- Build the GCA service Docker image
- Build the OpenClaw Docker image
- Verify configuration

### 4. Start

```bash
./scripts/start-ironclaw.sh
```

### 5. Verify

```bash
# Check GCA service health
curl http://localhost:8000/health

# Run a quick Arena test
curl http://localhost:8000/v1/arena/run?rounds=5
```

**Expected output**:
```json
{
  "status": "healthy",
  "glassbox_model": "gemini-2.5-flash",
  "moral_tolerance": 0.3,
  "vectors_loaded": 0,
  "action_history": 0
}
```

## Detailed Setup

### Getting API Keys

#### Gemini API Key (Required)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API Key"
3. Create or select a project
4. Copy the API key
5. Add to `.env.ironclaw`: `GEMINI_API_KEY=your_key_here`

#### OpenAI API Key (Optional)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new secret key
3. Add to `.env.ironclaw`: `OPENAI_API_KEY=your_key_here`

#### xAI Grok API Key (Optional)

1. Go to [xAI Console](https://console.x.ai/)
2. Generate API key
3. Add to `.env.ironclaw`: `XAI_API_KEY=your_key_here`

### Configuration Options

#### GCA Risk Tolerance

Controls how conservative the moral kernel is:

```bash
# High security (financial, medical)
GCA_RISK_TOLERANCE=0.2

# Balanced (default)
GCA_RISK_TOLERANCE=0.3

# Creative (writing, brainstorming)
GCA_RISK_TOLERANCE=0.5
```

#### Default Soul Template

Choose the personality for your agent:

```bash
# For coding and systems work
GCA_DEFAULT_SOUL=architect

# For conversations and support
GCA_DEFAULT_SOUL=companion

# For security operations
GCA_DEFAULT_SOUL=guardian
```

#### Quaternion Process Theory

Enable structured reasoning:

```bash
# Enable QPT (recommended)
GCA_USE_QPT=true

# Disable QPT (faster but less stable)
GCA_USE_QPT=false
```

### Directory Structure

After setup, your directory should look like:

```
ZovsIronClaw/
├── .env.ironclaw              # Your configuration (DO NOT COMMIT)
├── docker-compose.ironclaw.yml
├── gca-service/
│   ├── gca_core/              # GCA Python modules
│   ├── gca_assets/
│   │   └── souls/             # Soul templates
│   ├── api_server.py
│   └── Dockerfile
├── src/
│   └── providers/
│       └── gca-bridge.ts      # TypeScript integration
├── scripts/
│   ├── build-ironclaw.sh
│   ├── start-ironclaw.sh
│   └── stop-ironclaw.sh
└── docs/
    └── gca-integration.md
```

## Running ZovsIronClaw

### Start Services

```bash
./scripts/start-ironclaw.sh
```

### Stop Services

```bash
./scripts/stop-ironclaw.sh
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.ironclaw.yml logs -f

# GCA service only
docker-compose -f docker-compose.ironclaw.yml logs -f gca-service

# OpenClaw only
docker-compose -f docker-compose.ironclaw.yml logs -f openclaw-gateway
```

### Restart Services

```bash
./scripts/stop-ironclaw.sh
./scripts/start-ironclaw.sh
```

## Testing

### Health Check

```bash
curl http://localhost:8000/health
```

### Arena Protocol (Adversarial Testing)

```bash
# Run 10 rounds
curl http://localhost:8000/v1/arena/run?rounds=10

# Run 50 rounds (comprehensive)
curl http://localhost:8000/v1/arena/run?rounds=50
```

**Expected win rate**: >80% for Blue (Defender)

### Test Reasoning Endpoint

```bash
curl -X POST http://localhost:8000/v1/reason \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "text": "Help me write a Python function",
    "tools_available": [],
    "soul_name": "architect",
    "use_qpt": true
  }'
```

### Test Moral Evaluation

```bash
curl -X POST http://localhost:8000/v1/moral/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "actions": [
      {
        "type": "file_delete",
        "description": "Delete old backup files",
        "magnitude": 0.8,
        "prob_success": 0.9,
        "prob_harm": 0.6,
        "time_horizon_yrs": 1.0,
        "entropy_class": "irreversible"
      }
    ]
  }'
```

## Using OpenClaw CLI

### Interactive Mode

```bash
docker-compose -f docker-compose.ironclaw.yml run --rm openclaw-cli chat
```

### With Specific Soul

```bash
docker-compose -f docker-compose.ironclaw.yml run --rm \
  -e GCA_DEFAULT_SOUL=companion \
  openclaw-cli chat
```

## Customization

### Creating Custom Souls

1. Create a YAML file in `gca-service/gca_assets/souls/`:

```yaml
name: "Your Soul Name"
description: "What this soul does"

base_vector_mix:
  - skill: "SKILL_NAME"
    weight: 0.6

qpt_defaults:
  x: "Persona description"
  z: "Constraints"

entropy_tolerance: "MEDIUM"
risk_tolerance: 0.3
```

2. Restart GCA service:

```bash
docker-compose -f docker-compose.ironclaw.yml restart gca-service
```

3. Use your soul:

```bash
-e GCA_DEFAULT_SOUL=your_soul_name
```

### Adjusting Moral Kernel

Edit `.env.ironclaw`:

```bash
# More permissive
GCA_RISK_TOLERANCE=0.5

# More restrictive
GCA_RISK_TOLERANCE=0.2
```

Then restart:

```bash
./scripts/stop-ironclaw.sh
./scripts/start-ironclaw.sh
```

## Troubleshooting

### GCA Service Won't Start

**Check logs**:
```bash
docker-compose -f docker-compose.ironclaw.yml logs gca-service
```

**Common issues**:
- Missing `GEMINI_API_KEY`
- Port 8000 already in use
- Insufficient memory

**Solution**:
```bash
# Check if port is in use
lsof -i :8000

# Check Docker resources
docker system df
```

### High Risk Scores Blocking Everything

**Symptom**: All actions are blocked

**Solution**: Increase risk tolerance
```bash
# In .env.ironclaw
GCA_RISK_TOLERANCE=0.5
```

### Arena Protocol Failing

**Symptom**: Red wins > 20%

**Solution**: This indicates safety issues. Review logs and retrain vectors.

```bash
docker-compose -f docker-compose.ironclaw.yml logs gca-service | grep "RED WIN"
```

### OpenClaw Can't Connect to GCA

**Check network**:
```bash
docker network inspect ironclaw-network
```

**Check GCA health from OpenClaw container**:
```bash
docker-compose -f docker-compose.ironclaw.yml exec openclaw-gateway \
  curl http://gca-service:8000/health
```

## Performance Tuning

### For Low-Memory Systems

Edit `docker-compose.ironclaw.yml`:

```yaml
gca-service:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

### For High-Performance Systems

```yaml
gca-service:
  deploy:
    resources:
      limits:
        memory: 8G
        cpus: '4'
```

## Security Best Practices

### 1. Protect API Keys

```bash
# Never commit .env.ironclaw
echo ".env.ironclaw" >> .gitignore

# Use strong gateway token
OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)
```

### 2. Use Guardian Soul for Sensitive Operations

```bash
GCA_DEFAULT_SOUL=guardian
GCA_RISK_TOLERANCE=0.2
```

### 3. Enable Audit Logging

```bash
GCA_LOG_LEVEL=INFO
```

### 4. Regular Arena Testing

```bash
# Add to cron
0 */6 * * * curl http://localhost:8000/v1/arena/run?rounds=20
```

## Upgrading

### Pull Latest Changes

```bash
git pull origin main
```

### Rebuild

```bash
./scripts/stop-ironclaw.sh
./scripts/build-ironclaw.sh
./scripts/start-ironclaw.sh
```

### Backup Configuration

```bash
# Backup your souls and vectors
tar -czf gca-backup-$(date +%Y%m%d).tar.gz \
  gca-service/gca_assets/ \
  .env.ironclaw
```

## Getting Help

### Check Documentation

- [GCA Integration Guide](docs/gca-integration.md)
- [API Reference](docs/api-reference.md)
- [OpenClaw Docs](https://github.com/openclaw/openclaw)

### View Logs

```bash
# Real-time logs
docker-compose -f docker-compose.ironclaw.yml logs -f

# Save logs to file
docker-compose -f docker-compose.ironclaw.yml logs > ironclaw.log
```

### Common Commands Reference

```bash
# Build
./scripts/build-ironclaw.sh

# Start
./scripts/start-ironclaw.sh

# Stop
./scripts/stop-ironclaw.sh

# Logs
docker-compose -f docker-compose.ironclaw.yml logs -f

# Health check
curl http://localhost:8000/health

# Arena test
curl http://localhost:8000/v1/arena/run?rounds=10

# Restart single service
docker-compose -f docker-compose.ironclaw.yml restart gca-service
```

## Next Steps

1. **Read the [GCA Integration Guide](docs/gca-integration.md)**
2. **Create custom soul templates** for your use cases
3. **Run comprehensive Arena testing** (50+ rounds)
4. **Connect messaging platforms** (WhatsApp, Telegram, etc.)
5. **Monitor and tune** risk tolerance based on usage

---

**Need help?** Open an issue on GitHub or check the documentation.

**Built with conscience. Powered by geometry.**
