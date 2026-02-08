# Security Recommendations & Novel Insights for ZovsIronClaw

## 1. Implemented Fixes (v4.9.0)

- **API Hardening**: `gca-service` now binds to `127.0.0.1` by default and enforces strict CORS policies.
- **Input Validation**: Added max length constraints to API endpoints to prevent DoS.
- **Tauri Hardening**: Enabled strict Content Security Policy (CSP) and restricted model download URLs to trusted domains.
- **Secret Management**: Implemented ephemeral secret generation for HMAC if no environment variable is provided.

## 2. Novel Security Insights

### 2.1 Model Serialization Attacks (The "Pickle" Problem)
**Risk:** Loading PyTorch models via `torch.load` can execute arbitrary code if the model file is malicious.
**Solution:**
- **Enforce `.safetensors`**: Migrate all model loading to use the `safetensors` library, which is a safe, zero-copy alternative to Pickle.
- **Paper:** ["Safetensors: Fast and Safe Tensor Serialization"](https://github.com/huggingface/safetensors)

### 2.2 Prompt Injection & Jailbreaking
**Risk:** LLMs are susceptible to "jailbreaks" where users bypass safety filters.
**Solution:**
- **Constitutional AI / RLAIF**: Integrate a "Constitution" directly into the decoding process (partially implemented via `MoralKernel`).
- **Instruction Hierarchy**: Explicitly separate "System Instructions" from "User Data" in the prompt structure (already used in `GlassBox` but can be reinforced).
- **Canary Tokens**: Inject hidden tokens into the system prompt and check for their presence in the output to detect leakage.

### 2.3 Adversarial attacks on Geometric Steering
**Risk:** Attackers might find vectors that, when subtracted, disable safety mechanisms (Inverse Steering).
**Solution:**
- **Vector Normalization**: Ensure all steering vectors are normalized to prevent "over-steering" attacks.
- **Dynamic Re-centering**: Periodically re-calculate the "center of mass" of the agent's personality to detect drift.

## 3. Future Roadmap Recommendations

- **Swarm Consensus (Proof of Logic)**: Implement a mechanism where sensitive actions require approval from multiple "sub-agents" (e.g., a "Critic" and a "Safety Officer").
- **Homomorphic Encryption**: Explore using Fully Homomorphic Encryption (FHE) for processing sensitive user data in memory without decrypting it (Long-term research).
- **Secure Enclaves**: If running on supported hardware, move the `SecureStorage` keys into a TEE (Trusted Execution Environment).
