"""
GCA Resource Manager: Smart Offloading & Hardware Detection
"""
import os
import psutil
import torch
import logging
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger("IronClaw.Resource")

class SystemProfile(str, Enum):
    HIGH_PERFORMANCE = "high_performance" # Local Models (GPU)
    BALANCED = "balanced"                 # Quantized/Mixed
    LOW_RESOURCE = "low_resource"         # API-Only / Cloud Offload

class ResourceManager:
    def __init__(self, override_profile: str = None):
        self.profile = self._detect_hardware()
        if override_profile and override_profile in SystemProfile.__members__.values():
            self.profile = SystemProfile(override_profile)

        logger.info(f"System Profile Detected: {self.profile.value.upper()}")
        self.capabilities = self._get_capabilities()

    def _detect_hardware(self) -> SystemProfile:
        # 1. Check GPU
        has_cuda = torch.cuda.is_available()
        vram_gb = 0
        if has_cuda:
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

        # 2. Check RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)

        logger.info(f"Hardware Audit: RAM={ram_gb:.1f}GB, GPU={'CUDA' if has_cuda else 'CPU'}, VRAM={vram_gb:.1f}GB")

        # Decision Logic
        if has_cuda and vram_gb >= 8 and ram_gb >= 16:
            return SystemProfile.HIGH_PERFORMANCE
        elif (has_cuda and vram_gb >= 4) or ram_gb >= 12:
            return SystemProfile.BALANCED
        else:
            return SystemProfile.LOW_RESOURCE

    def _get_capabilities(self) -> Dict[str, Any]:
        """Returns what features should run locally vs offloaded"""
        p = self.profile
        return {
            "local_llm": p == SystemProfile.HIGH_PERFORMANCE,
            "local_embeddings": p != SystemProfile.LOW_RESOURCE, # Can run cpu-only on balanced
            "local_transcription": p == SystemProfile.HIGH_PERFORMANCE, # Whisper large needs VRAM
            "local_vision": p == SystemProfile.HIGH_PERFORMANCE,
            "quantization": "4bit" if p == SystemProfile.BALANCED else "none" if p == SystemProfile.HIGH_PERFORMANCE else "api"
        }

    def should_offload(self, task: str) -> bool:
        """
        Check if a specific task (reasoning, vision, audio) should be offloaded to API.
        task: 'llm', 'vision', 'audio', 'embedding'
        """
        caps = self.capabilities
        if task == 'llm':
            return not caps['local_llm']
        if task == 'vision':
            return not caps['local_vision']
        if task == 'audio':
            return not caps['local_transcription']
        if task == 'embedding':
            return not caps['local_embeddings']
        return True # Default to offload for unknown tasks safety
