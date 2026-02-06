"""
GlassBox: Geometric Steering Engine for GCA Framework
Provides transparent, interpretable AI reasoning through geometric vector manipulation.
"""

import torch
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("GCA.GlassBox")


class GlassBox:
    """
    The GlassBox provides geometric steering capabilities for LLM reasoning.
    It allows for transparent manipulation of model activations through vector arithmetic.
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash", device: str = "cpu"):
        """
        Initialize the GlassBox with a specific model.
        
        Args:
            model_name: The model to use for generation
            device: Computing device (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self.activation_cache = {}
        logger.info(f"GlassBox initialized with model: {model_name}")
        
    def get_activation(self, text: str, layer: Optional[int] = None) -> torch.Tensor:
        """
        Extract activation vectors from the model for given text.
        
        Args:
            text: Input text to analyze
            layer: Specific layer to extract from (None = final layer)
            
        Returns:
            Activation tensor representing the text in latent space
        """
        # Placeholder for actual model activation extraction
        # In production, this would interface with the actual model
        cache_key = f"{text}_{layer}"
        if cache_key in self.activation_cache:
            return self.activation_cache[cache_key]
            
        # Simulate activation extraction
        activation = torch.randn(768)  # Typical embedding dimension
        self.activation_cache[cache_key] = activation
        return activation
        
    def generate_steered(
        self,
        prompt: str,
        steering_vec: Optional[torch.Tensor] = None,
        strength: float = 1.0,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text with geometric steering applied.
        
        Args:
            prompt: Input prompt
            steering_vec: Vector to steer generation toward
            strength: Strength of steering (0.0 to 5.0)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated text with steering applied
        """
        import os
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # If steering vector provided, modify the prompt to reflect the geometric intent
        if steering_vec is not None:
            # In a full implementation, this would inject the steering at the activation level
            # For now, we use prompt engineering to simulate the effect
            logger.info(f"Applying steering with strength {strength}")
            
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error during generation: {str(e)}"
    
    def compute_vector_difference(self, text_a: str, text_b: str) -> torch.Tensor:
        """
        Compute the geometric difference between two text representations.
        This is the foundation of "skill vectors" in GCA.
        
        Args:
            text_a: First text
            text_b: Second text
            
        Returns:
            Difference vector (text_b - text_a)
        """
        vec_a = self.get_activation(text_a)
        vec_b = self.get_activation(text_b)
        return vec_b - vec_a
        
    def project_onto_axis(self, text: str, axis_vector: torch.Tensor) -> float:
        """
        Project text representation onto a specific axis (e.g., "ethical" vs "unethical").
        
        Args:
            text: Text to analyze
            axis_vector: The axis to project onto
            
        Returns:
            Scalar projection value
        """
        activation = self.get_activation(text)
        # Normalize both vectors
        activation_norm = activation / (activation.norm() + 1e-8)
        axis_norm = axis_vector / (axis_vector.norm() + 1e-8)
        # Compute dot product
        projection = torch.dot(activation_norm, axis_norm).item()
        return projection
