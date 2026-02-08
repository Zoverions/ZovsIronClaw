"""
GCA Resource Manager: Smart Offloading & Hardware Detection
Manages "Iron Swarm" Profiles: Spark (Mobile), Forge (Laptop), Titan (Workstation).
"""
import os
import psutil
import torch
import logging
import yaml
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger("IronClaw.Resource")

class SystemProfile(str, Enum):
    TITAN = "titan"   # Workstation (DeepSeek, 32B+, Local everything)
    FORGE = "forge"   # Laptop (GLM-4, 7B-9B, Balanced)
    SPARK = "spark"   # Mobile/Edge (0.5B, Moondream, Cloud Offload)

class ResourceManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.raw_config = self._load_raw_config()
        self.profile = self._determine_profile()

        logger.info(f"System Profile Active: {self.profile.value.upper()}")
        self.capabilities = self._get_capabilities()

    def _load_raw_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    def _determine_profile(self) -> SystemProfile:
        # 1. Check Env Var Override
        env_profile = os.environ.get("GCA_PROFILE", "").lower()
        if env_profile in SystemProfile.__members__.values():
            logger.info(f"Profile override via GCA_PROFILE: {env_profile}")
            return SystemProfile(env_profile)

        # 2. Check Config File "system.profile"
        cfg_profile = self.raw_config.get("system", {}).get("profile", "auto").lower()
        if cfg_profile != "auto" and cfg_profile in SystemProfile.__members__.values():
            logger.info(f"Profile set via config: {cfg_profile}")
            return SystemProfile(cfg_profile)

        # 3. Auto-Detect Hardware
        return self._detect_hardware()

    def _detect_hardware(self) -> SystemProfile:
        # 1. Check GPU
        has_cuda = torch.cuda.is_available()
        # MPS support for Mac
        has_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()

        vram_gb = 0
        if has_cuda:
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        elif has_mps:
            # MPS shares RAM, hard to get specific VRAM, assume "unified" matches RAM largely
            # For simplicity, treat high RAM macs as capable
            pass

        # 2. Check RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)

        logger.info(f"Hardware Audit: RAM={ram_gb:.1f}GB, GPU={'CUDA' if has_cuda else ('MPS' if has_mps else 'CPU')}, VRAM={vram_gb:.1f}GB")

        # Decision Logic
        # TITAN: > 24GB RAM (or High VRAM)
        if (has_cuda and vram_gb >= 20) or (has_mps and ram_gb >= 32) or ram_gb >= 48:
             return SystemProfile.TITAN

        # FORGE: > 8GB RAM (Standard Laptop)
        elif (has_cuda and vram_gb >= 4) or (has_mps and ram_gb >= 12) or ram_gb >= 12:
            return SystemProfile.FORGE

        # SPARK: < 8GB RAM or no acceleration
        else:
            return SystemProfile.SPARK

    def _resolve_device(self, requested_device: str) -> str:
        """Resolves requested device to available hardware."""
        # 1. Check if MPS (Mac) is available
        has_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()

        if requested_device == "cuda":
            if not torch.cuda.is_available():
                if has_mps:
                    return "mps"
                return "cpu"
        elif requested_device == "mps":
            if not has_mps:
                return "cpu"

        return requested_device

    def get_active_config(self) -> Dict[str, Any]:
        """
        Returns the flattened config for the active profile.
        Merges profile-specific settings into the main structure.
        Overrides device settings based on actual hardware availability.
        """
        base_config = self.raw_config.copy()
        profile_key = self.profile.value

        if "profiles" in base_config and profile_key in base_config["profiles"]:
            profile_data = base_config["profiles"][profile_key]

            # Ensure sections exist
            base_config.setdefault("system", {})
            base_config.setdefault("perception", {})
            base_config["perception"].setdefault("vision", {})
            base_config["perception"].setdefault("audio", {})
            base_config["perception"].setdefault("embeddings", {})

            # LLM -> System (for GlassBox)
            if "llm" in profile_data:
                base_config["system"].update(profile_data["llm"])

            # Vision -> Perception
            if "vision" in profile_data:
                base_config["perception"]["vision"].update(profile_data["vision"])

            # Audio -> Perception
            if "audio" in profile_data:
                base_config["perception"]["audio"].update(profile_data["audio"])

            # Embeddings -> Perception
            if "embeddings" in profile_data:
                base_config["perception"]["embeddings"].update(profile_data["embeddings"])

            # Add metadata
            base_config["active_profile"] = profile_key
            base_config["profile_description"] = profile_data.get("description", "")

        # Override devices based on reality
        if "system" in base_config:
             base_config["system"]["device"] = self._resolve_device(base_config["system"].get("device", "cpu"))

        if "perception" in base_config:
             for key in ["vision", "audio", "embeddings"]:
                 if key in base_config["perception"]:
                     base_config["perception"][key]["device"] = self._resolve_device(base_config["perception"][key].get("device", "cpu"))

        return base_config

    def _get_capabilities(self) -> Dict[str, Any]:
        """Returns what features should run locally vs offloaded"""
        p = self.profile
        return {
            "local_llm": True,
            "heavy_reasoning": p == SystemProfile.TITAN,
            "vision": True,
            "quantization": "4bit" if p in [SystemProfile.FORGE, SystemProfile.TITAN] else "none"
        }

    def should_offload(self, task: str) -> bool:
        """
        Check if a specific task (reasoning, vision, audio) should be offloaded to API.
        task: 'llm', 'vision', 'audio', 'embedding'
        """
        # For Spark, we might want to offload heavy vision or audio if we implemented cloud fallback
        # But for now, we assume local models are selected correctly for the profile.
        return False
