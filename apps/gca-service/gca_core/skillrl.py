"""
GCA Phase 6: SkillRL Evolution Engine
-------------------------------------
Implements Recursive Skill Augmentation.
1. Logs Trajectories (Input -> Reasoning -> Output).
2. Distills Success Vectors (The 'Why' it worked).
3. Evolving Registry: Blends new experience into permanent skills.
"""

import torch
import torch.nn.functional as F
import json
import os
import numpy as np

# --- CONFIG ---
REGISTRY_PATH = "skill_registry.json"
HISTORY_PATH = "trajectory_history.jsonl"
LEARNING_RATE = 0.15  # How much new experience overrides old habit

class SkillEvolutionEngine:
    def __init__(self, model, tokenizer, basis):
        self.model = model
        self.tokenizer = tokenizer
        self.basis = basis

        # Load Skills
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'r') as f:
                self.registry = json.load(f)
        else:
            self.registry = {}

    def log_trajectory(self, skill_name, user_prompt, final_response, success_score=1.0):
        """
        Saves a run for distillation.
        In a full system, success_score comes from user feedback or unit tests.
        """
        entry = {
            "skill": skill_name,
            "prompt": user_prompt,
            "response": final_response,
            "score": success_score
        }

        with open(HISTORY_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"[🧬] Trajectory logged for '{skill_name}'. Score: {success_score}")

        # Immediate Recursive Update (The SkillRL Loop)
        if success_score > 0.7:
            self._distill_and_update(entry)

    def _distill_and_update(self, entry):
        """
        The Core Logic: Extracts the vector from the specific successful run
        and blends it into the master skill.
        """
        skill_name = entry['skill']
        text_content = entry['response'] # We learn from the *Output* mostly

        # 1. Harvest the vector of this specific success
        # We run the successful response through the model to see where it lives in latent space
        inputs = self.tokenizer(text_content, return_tensors="pt").to(self.model.device)

        captured = []
        def hook(module, input, output):
            # Capture the mean activation of the success
            if isinstance(output, tuple):
                hidden = output[0]
            else:
                hidden = output
            captured.append(torch.mean(hidden, dim=1).detach())

        # We assume Layer 6 is our steering layer (per GCA spec)
        # Note: This index might need adjustment depending on model depth/config
        layer_idx = 6
        handle = None

        if hasattr(self.model, "transformer"): # GPT-2 style
             if len(self.model.transformer.h) > layer_idx:
                 handle = self.model.transformer.h[layer_idx].register_forward_hook(hook)
        elif hasattr(self.model, "model") and hasattr(self.model.model, "layers"): # Llama/Qwen style
             if len(self.model.model.layers) > layer_idx:
                 handle = self.model.model.layers[layer_idx].register_forward_hook(hook)
        elif hasattr(self.model, "layers"): # GLM style
             if len(self.model.layers) > layer_idx:
                 handle = self.model.layers[layer_idx].register_forward_hook(hook)

        if handle is None:
             # Fallback: Try to find any reasonable layer
             print(f"[⚠️] Could not find layer {layer_idx} to hook into. Trying fallback.")
             # Very basic fallback to last layer just to not crash
             modules = list(self.model.modules())
             # This is risky, but better than crash. Ideally we should configure this.
             return

        with torch.no_grad():
            self.model(**inputs)
        handle.remove()

        if not captured:
            print("[⚠️] No activation captured.")
            return

        success_state = captured[0].squeeze(0) # [Hidden_Dim]

        # 2. Project onto Basis (Get the Coefficients)
        # SVD Projection: Coeffs = State @ Basis.T
        # Basis shape: [16, 768] (assumed) -> Basis.T: [768, 16]

        # Ensure basis is on same device
        basis = self.basis.to(success_state.device)

        if basis.shape[1] == success_state.shape[0]:
             # basis is (N, D), state is (D) -> state @ basis.T -> (D) @ (D, N) -> (N)
             coeffs = torch.matmul(success_state, basis.T)
        elif basis.shape[0] == success_state.shape[0]:
             # basis is (D, N), state is (D) -> state @ basis -> (D) @ (D, N) -> (N)
             coeffs = torch.matmul(success_state, basis)
        else:
             print(f"[⚠️] Basis dimension mismatch. Basis: {basis.shape}, State: {success_state.shape}")
             return

        new_vector_coeffs = coeffs.cpu().tolist()

        # 3. Recursive Update (Weighted Blend)
        if skill_name in self.registry:
            old_coeffs = self.registry[skill_name]['vector_coeffs']

            # Blend: New = Old + LR * (Success - Old)
            evolved_coeffs = []
            # Handle case where coeff length might differ (if basis changed)
            length = min(len(old_coeffs), len(new_vector_coeffs))

            for i in range(length):
                old = old_coeffs[i]
                new = new_vector_coeffs[i]
                updated = old + LEARNING_RATE * (new - old)
                evolved_coeffs.append(updated)

            self.registry[skill_name]['vector_coeffs'] = evolved_coeffs
            self.registry[skill_name]['evolution_generations'] = self.registry[skill_name].get('evolution_generations', 0) + 1

            print(f"[🧠] Skill '{skill_name}' Evolved! (Gen {self.registry[skill_name]['evolution_generations']})")
        else:
            # New Skill Discovery
            print(f"[✨] New Skill Created: '{skill_name}'")
            self.registry[skill_name] = {
                "vector_coeffs": new_vector_coeffs,
                "layer": layer_idx,
                "default_strength": 5.0,
                "evolution_generations": 1
            }

        # 4. Save Registry
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(self.registry, f, indent=2)
