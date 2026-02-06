"""
Perception Engine: Multimodal capabilities for GCA (Vision, Audio, Embeddings)
"""

import torch
import logging
import yaml
import os
import io
import tempfile
from typing import List, Optional, Union
import numpy as np
from pathlib import Path

# Lazy imports to save startup time/memory if not used
# from sentence_transformers import SentenceTransformer
# from faster_whisper import WhisperModel
# from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

logger = logging.getLogger("GCA.Perception")

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
if os.path.exists(config_path):
    with open(config_path) as f:
        CFG = yaml.safe_load(f)
else:
    CFG = {}

class PerceptionSystem:
    def __init__(self):
        self.cfg = CFG.get('perception', {})
        self.device = CFG.get('system', {}).get('device', 'cpu')

        # Sub-engines
        self.embedding_engine = None
        self.vision_engine = None
        self.audio_engine = None
        self.vision_processor = None

        logger.info("Perception System Initialized (Lazy Loading)")

    def _ensure_embeddings(self):
        if self.embedding_engine is None:
            from sentence_transformers import SentenceTransformer
            model_id = self.cfg.get('embeddings', {}).get('model_id', 'sentence-transformers/all-MiniLM-L6-v2')
            device = self.cfg.get('embeddings', {}).get('device', self.device)
            logger.info(f"Loading Embedding Model: {model_id} on {device}")
            self.embedding_engine = SentenceTransformer(model_id, device=device)

    def _ensure_vision(self):
        if self.vision_engine is None:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            model_id = self.cfg.get('vision', {}).get('model_id', 'Qwen/Qwen2-VL-2B-Instruct')
            device = self.cfg.get('vision', {}).get('device', self.device)
            logger.info(f"Loading Vision Model: {model_id} on {device}")

            # Use float32 for CPU to avoid bfloat16 issues on some hardware
            dtype = torch.float32 if device == 'cpu' else torch.float16

            self.vision_engine = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=dtype,
                device_map=device
            )
            self.vision_processor = AutoProcessor.from_pretrained(model_id)

    def _ensure_audio(self):
        if self.audio_engine is None:
            from faster_whisper import WhisperModel
            model_size = self.cfg.get('audio', {}).get('model_size', 'tiny')
            device = self.cfg.get('audio', {}).get('device', self.device)
            logger.info(f"Loading Audio Model: {model_size} on {device}")

            compute_type = "int8" if device == 'cpu' else "float16"
            self.audio_engine = WhisperModel(model_size, device=device, compute_type=compute_type)

    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text.
        """
        self._ensure_embeddings()
        embeddings = self.embedding_engine.encode(text)
        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return embeddings

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text.
        """
        self._ensure_audio()

        # Write to temp file because faster-whisper likes files
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()

            segments, info = self.audio_engine.transcribe(tmp.name, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()

    def describe_media(self, media_path: str, prompt: str = "Describe this image.") -> str:
        """
        Describe image or video frames using VLM.
        """
        self._ensure_vision()
        from qwen_vl_utils import process_vision_info

        # Check if video or image based on extension
        ext = Path(media_path).suffix.lower()
        is_video = ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video" if is_video else "image",
                        "video" if is_video else "image": media_path,
                        # Optional: limit frames/fps if video
                        # "max_pixels": 360 * 420,
                        # "fps": 1.0,
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text = self.vision_processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.vision_processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.vision_engine.device)

        generated_ids = self.vision_engine.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        output_text = self.vision_processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        return output_text[0]

    def describe_image_bytes(self, image_bytes: bytes, prompt: str = "Describe this image.") -> str:
        """
        Describe image from bytes.
        """
        # Save to temp file to reuse the file-based pipeline which is robust
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(image_bytes)
            tmp.flush()
            return self.describe_media(tmp.name, prompt)

    def describe_video_bytes(self, video_bytes: bytes, prompt: str = "Describe this video.") -> str:
        """
        Describe video from bytes.
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
            tmp.write(video_bytes)
            tmp.flush()
            return self.describe_media(tmp.name, prompt)
