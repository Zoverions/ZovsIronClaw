"""
GlassBox: Geometric Steering Engine for GCA Framework
Provides transparent, interpretable AI reasoning through geometric vector manipulation.
Now supports DeepSeek-R1 (Thinking Models), GLM-4, and 4-bit Quantization.
"""

import torch
import yaml
import os
import re
from typing import Optional, Dict, Any, List
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from functools import lru_cache

logger = logging.getLogger("GCA.GlassBox")

# Default Config Path
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

class GlassBox:
    """
    The GlassBox provides geometric steering capabilities for LLM reasoning.
    It allows for transparent manipulation of model activations through vector arithmetic.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the GlassBox with a specific model.
        Args:
            model_name: Override model ID.
            device: Override device.
            config: Full configuration dictionary (from ResourceManager).
        """
        # Load Config
        if config:
            self.cfg = config
        elif os.path.exists(config_path):
            with open(config_path) as f:
                self.cfg = yaml.safe_load(f)
        else:
            # Default fallback
            self.cfg = {
                'system': {'model_id': 'Qwen/Qwen2.5-0.5B-Instruct', 'device': 'cpu', 'dtype': 'float32'},
                'geometry': {'layer_idx': 12}
            }

        self.model_name = model_name or self.cfg.get('system', {}).get('model_id')
        self.device = device or self.cfg.get('system', {}).get('device', 'cpu')
        dtype_str = self.cfg.get('system', {}).get('dtype', 'float32')
        self.dtype = getattr(torch, dtype_str)

        logger.info(f"Loading model: {self.model_name} on {self.device} ({dtype_str})")

        # Quantization Logic
        quantization_type = self.cfg.get('system', {}).get('quantization', 'none')
        quantization_config = None

        # BitsAndBytes requires CUDA
        can_use_bnb = "cuda" in self.device or (self.device == "auto" and torch.cuda.is_available())

        if quantization_type == "4bit":
            if can_use_bnb:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=self.dtype,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                logger.info("⚡ Quantization Enabled: 4-bit (NF4)")
            else:
                logger.warning(f"⚠️ Quantization (4bit) requested but device is {self.device}. Disabling quantization (BitsAndBytes requires CUDA).")

        elif quantization_type == "8bit":
             if can_use_bnb:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                )
                logger.info("⚡ Quantization Enabled: 8-bit")
             else:
                logger.warning(f"⚠️ Quantization (8bit) requested but device is {self.device}. Disabling quantization.")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)

        # Load Model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=self.dtype,
            trust_remote_code=True,
            quantization_config=quantization_config,
            device_map=self.device # Use device_map for better handling of multi-gpu or offload
        )
        # Ensure model is on correct device if device_map didn't handle it fully
        if self.device != "auto" and quantization_config is None and self.device not in str(self.model.device):
             self.model.to(self.device)

        self.layer_idx = self.cfg.get('geometry', {}).get('layer_idx', 12)
        self.activation_cache = {}
        logger.info(f"GlassBox initialized. Steering layer: {self.layer_idx}")

    @lru_cache(maxsize=1024)
    def _cached_activation(self, text: str, layer_idx: int) -> torch.Tensor:
        """Internal cached activation method to avoid re-computation."""
        target_layer = layer_idx

        activations = []
        def hook(module, input, output):
            if isinstance(output, tuple):
                hidden = output[0]
            else:
                hidden = output
            # Mean pool over sequence length
            activations.append(torch.mean(hidden, dim=1).detach().cpu())

        # Attach hook
        handle = self._get_layer(target_layer).register_forward_hook(hook)

        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            self.model(**inputs)
            
        handle.remove()
        
        if activations:
            return activations[0].squeeze()
        return torch.zeros(1) # Should not happen

    def get_activation(self, text: str, layer_idx: Optional[int] = None) -> torch.Tensor:
        """
        Extract activation vectors from the model for given text.
        """
        target_layer = layer_idx if layer_idx is not None else self.layer_idx
        return self._cached_activation(text, target_layer)

    def generate_steered(
        self,
        prompt: str,
        steering_vec: Optional[torch.Tensor] = None,
        strength: float = 1.0,
        max_tokens: int = 1024, # Increased for thinking models
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with geometric steering applied via forward hook.
        Handles DeepSeek-R1 "Thought" separation.
        """
        handle = None
        if steering_vec is not None:
            steering_vec = steering_vec.to(self.device).to(self.dtype)
            
            def steering_hook(module, input, output):
                if isinstance(output, tuple):
                    hidden = output[0]
                    # Inject steering vector
                    # Add to all tokens in sequence (simple broadcasting)
                    modified = hidden + (steering_vec.unsqueeze(0).unsqueeze(0) * strength)
                    return (modified,) + output[1:]
                else:
                    return output + (steering_vec.unsqueeze(0).unsqueeze(0) * strength)

            handle = self._get_layer(self.layer_idx).register_forward_hook(steering_hook)
            logger.info(f"Steering active: strength={strength}")

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Strip prompt
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]

            # Handle Thinking Models (DeepSeek-R1)
            thought, answer = self._extract_thought(generated_text)
            if thought:
                logger.info(f"🧠 [THOUGHT PROCESS]: {thought[:200]}...") # Log first 200 chars of thought
                # We return only the answer to the user to keep it clean,
                # but the thought is logged for the 'ReflectiveLogger'.
                return answer.strip()

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            return f"Error: {str(e)}"
        finally:
            if handle:
                handle.remove()

    def _extract_thought(self, text: str):
        """
        Extracts content within <think> tags for DeepSeek-R1.
        Returns (thought, answer).
        """
        # Pattern for <think> ... </think>
        # Note: DeepSeek sometimes uses escaped tags or different variations, but <think> is standard.
        pattern = r"<think>(.*?)</think>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            thought = match.group(1).strip()
            # The answer is everything after </think>
            answer = text.split("</think>")[-1].strip()
            return thought, answer
        return None, text

    def _get_layer(self, idx):
        if hasattr(self.model, "model"):
            if hasattr(self.model.model, "layers"):
                return self.model.model.layers[idx]
        if hasattr(self.model, "transformer"):
            return self.model.transformer.h[idx]
        if hasattr(self.model, "layers"): # GLM might be here
            return self.model.layers[idx]
        # Fallback search
        modules = list(self.model.modules())
        if len(modules) > idx:
            return modules[idx]
        return modules[-1]

    def compute_vector_difference(self, text_a: str, text_b: str) -> torch.Tensor:
        vec_a = self.get_activation(text_a)
        vec_b = self.get_activation(text_b)
        return vec_b - vec_a
        
    def project_onto_axis(self, text: str, axis_vector: torch.Tensor) -> float:
        activation = self.get_activation(text)
        activation_norm = activation / (activation.norm() + 1e-8)
        axis_norm = axis_vector / (axis_vector.norm() + 1e-8)
        return torch.dot(activation_norm, axis_norm).item()
