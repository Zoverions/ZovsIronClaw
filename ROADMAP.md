# ZovsIronClaw Deep Hill Plan

This roadmap tracks the transition from "Placeholder" to "Production" for the ZovsIronClaw system. It follows the Hill Chart methodology: Figure it Out (Uphill) -> Get it Done (Downhill).

## Hill 1: The Sensorium (Critical Path)
*Goal: Give the system eyes and ears.*

### Swabble (The Body) - Swift Daemon
- [x] **Logging & Visibility**: Ensure all placeholder functions emit structured logs (WARN/ERROR) instead of silent failures.
- [x] **Neural Link (HookExecutor)**: Implement HTTP POST loop to send captured audio/screen frames to `http://localhost:8000/v1/observe`.
- [x] **Health Check (StatusCommand)**: Ping the GCA health endpoint (`/health`) to verify "brain" connectivity.

### GCA Service (The Senses) - Python
- [x] **Observer Module**: Create `gca-service/gca_core/observer.py`.
    - [x] Input: Accept raw Audio/Image bytes.
    - [x] Process: Project into Latent Space using `GlassBox.get_activation`.
    - [x] Output: Generate "User State Vector" (e.g., `[0.1, 0.4, -0.2]` for "Stressed/Busy").

---

## Hill 2: The Proactive Mind (Planned Features)
*Goal: Make the system act without prompting.*

### The Pulse System
- [x] **Background Loop**: Implement `gca-service/gca_core/pulse.py` loop (every 5m).
- [x] **Logic**: Compare **User State Vector** (from Observer/WorkingMemory) vs. **Goal Vector** (from `GOAL.md`).
- [x] **Trigger**: `if distance(User, Goal) > Threshold: Trigger_Intervention()`.

### Soul Composition
- [x] **Anti-Vectors**: Update `SOUL.md` parsing in `gca-service/gca_core/soul_loader.py`.
- [x] **Implementation**: Allow definition of traits to avoid, subtracting them from the steering tensor.

---

## Execution Log

- **Phase 1: Analysis & Logging**: Identified key files and missing components.
- **Phase 2: The Hill Climb**: Completed Swabble hooks, Observer logic, Pulse system, and Soul composition updates.
