"""
GlassBox: Geometric Steering Engine for GCA Framework
Provides transparent, interpretable AI reasoning through geometric vector manipulation.
"""

import torch
import yaml
import os
from typing import Optional, Dict, Any, List
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger("GCA.GlassBox")

# Load Config
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
if os.path.exists(config_path):
    with open(config_path) as f:
        CFG = yaml.safe_load(f)
else:
    # Default fallback
    CFG = {
        'system': {'model_id': 'Qwen/Qwen2.5-0.5B', 'device': 'cpu', 'dtype': 'float32'},
        'geometry': {'layer_idx': 12}
    }

class GlassBox:
    """
    The GlassBox provides geometric steering capabilities for LLM reasoning.
    It allows for transparent manipulation of model activations through vector arithmetic.
    """
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the GlassBox with a specific model.
        """
        self.model_name = model_name or CFG['system']['model_id']
        self.device = device or CFG['system']['device']
        self.dtype = getattr(torch, CFG['system']['dtype'])

        logger.info(f"Loading model: {self.model_name} on {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=self.dtype,
            trust_remote_code=True
        ).to(self.device)

        self.layer_idx = CFG['geometry']['layer_idx']
        self.activation_cache = {}
        logger.info("GlassBox initialized.")
        
    def get_activation(self, text: str, layer_idx: Optional[int] = None) -> torch.Tensor:
        """
        Extract activation vectors from the model for given text.
        """
        target_layer = layer_idx if layer_idx is not None else self.layer_idx

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

    def generate_steered(
        self,
        prompt: str,
        steering_vec: Optional[torch.Tensor] = None,
        strength: float = 1.0,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with geometric steering applied via forward hook.
        """
        handle = None
        if steering_vec is not None:
            steering_vec = steering_vec.to(self.device).to(self.dtype)
            
            def steering_hook(module, input, output):
                if isinstance(output, tuple):
                    hidden = output[0]
                    # Inject steering vector
                    # Add to all tokens in sequence
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

            # Remove prompt from output if needed, but usually we want full context or just new tokens.
            # Assuming we want just the response part usually, but let's return full for now or strip prompt.
            # Simple strip:
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):]

            return generated_text

        except Exception as e:
            logger.error(f"Generation error: {e}", exc_info=True)
            return f"Error: {str(e)}"
        finally:
            if handle:
                handle.remove()

    def _get_layer(self, idx):
        if hasattr(self.model, "model"):
            if hasattr(self.model.model, "layers"):
                return self.model.model.layers[idx]
        if hasattr(self.model, "transformer"):
            return self.model.transformer.h[idx]
        # Fallback
        return list(self.model.modules())[idx]

    def compute_vector_difference(self, text_a: str, text_b: str) -> torch.Tensor:
        vec_a = self.get_activation(text_a)
        vec_b = self.get_activation(text_b)
        return vec_b - vec_a
        
    def project_onto_axis(self, text: str, axis_vector: torch.Tensor) -> float:
        activation = self.get_activation(text)
        activation_norm = activation / (activation.norm() + 1e-8)
        axis_norm = axis_vector / (axis_vector.norm() + 1e-8)
        return torch.dot(activation_norm, axis_norm).item()
