"""
GCA API Server: FastAPI Bridge between OpenClaw (Node.js) and GCA (Python)
Exposes GCA reasoning, moral evaluation, and geometric steering via REST API.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import logging
import sys
import yaml
import os
from pathlib import Path
import numpy as np
from textblob import TextBlob
from collections import Counter

# Add gca_core to path
sys.path.insert(0, str(Path(__file__).parent))

from gca_core.glassbox import GlassBox
from gca_core.moral import MoralKernel, Action, EntropyClass
from gca_core.optimizer import GCAOptimizer
from gca_core.memory import IsotropicMemory
from gca_core.resonance import ResonanceEngine
from gca_core.qpt import QuaternionArchitect
from gca_core.arena import ArenaProtocol
from gca_core.memory_advanced import BiomimeticMemory
from gca_core.perception import PerceptionSystem
from gca_core.observer import Observer
from dreamer import DeepDreamer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IronClaw")

# Load Config
config_path = "config.yaml"
if os.path.exists(config_path):
    with open(config_path) as f:
        CFG = yaml.safe_load(f)
else:
    CFG = {}

# Initialize FastAPI app
app = FastAPI(
    title="GCA Service API",
    description="Geometric Conscience Architecture - Ethical AI Reasoning Engine",
    version="4.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INIT CORE COMPONENTS ---
logger.info("Booting IronClaw Core...")
glassbox = GlassBox() # Uses config.yaml
memory = IsotropicMemory(glassbox.device, storage_path="./gca_assets")
bio_mem = BiomimeticMemory(glassbox, memory)
dreamer = DeepDreamer(bio_mem)

optimizer = GCAOptimizer(glassbox, memory)
moral_kernel = MoralKernel(risk_tolerance=0.3)
resonance = ResonanceEngine(glassbox, memory)
qpt = QuaternionArchitect()
perception = PerceptionSystem()
observer = Observer(glassbox, memory, perception)

logger.info("GCA Service initialized successfully")

# ============================================================================
# Models
# ============================================================================

class ReasonRequest(BaseModel):
    user_id: str
    text: str
    soul_config: Optional[str] = ""
    input_modality: Optional[str] = "text" # 'text' or 'voice'
    tools_available: List[str] = []
    context: Optional[str] = None

class ReasoningResponse(BaseModel):
    status: str
    content: str # The response text
    tool_call: Optional[Dict[str, Any]] = None
    moral_signature: Optional[str] = None
    meta: Dict[str, Any] = {}

class MoralEvaluationRequest(BaseModel):
    actions: List[Dict[str, Any]]

class EntropyRequest(BaseModel):
    content: str
    threshold: float = 0.5  # Default threshold for "high entropy"

class EntropyResponse(BaseModel):
    entropy_score: float
    risk_level: str  # e.g., "low", "medium", "high"
    sentiment_volatility: float
    reason: str

class EmbeddingRequest(BaseModel):
    text: Union[str, List[str]]

class EmbeddingResponse(BaseModel):
    embeddings: Union[List[float], List[List[float]]]

class TranscribeResponse(BaseModel):
    text: str

class DescribeResponse(BaseModel):
    text: str

class ObservationResponse(BaseModel):
    status: str
    alignment: Dict[str, Any]
    detected_state: Dict[str, Any]
    description: str

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": glassbox.model_name,
        "device": glassbox.device,
        "vectors_loaded": len(memory.list_vectors())
    }

@app.post("/v1/reason", response_model=ReasoningResponse)
async def reasoning_engine(req: ReasonRequest):
    logger.info(f"Incoming from {req.user_id}: {req.text[:50]}...")

    try:
        # 1. PARSE SOUL CONFIG
        steering_bias = _parse_vector_config(req.soul_config)
        
        # 1.5 PERCEIVE (Sensory Input)
        bio_mem.perceive(req.text)

        # 2. INGEST & RESONANCE
        resonance.ingest(req.user_id, req.text)
        user_vec = resonance.get_style_vector(req.user_id)
        
        # 3. GEOMETRIC ROUTING
        intent = optimizer.route_intent(req.text)
        skill_vec = memory.get_vector(intent)

        # 3.5 RETRIEVE WORKING MEMORY CONTEXT
        wm_context = bio_mem.retrieve_context(skill_vec)

        # 4. VECTOR COMPOSITION
        # Final = Skill + UserResonance + SoulBias
        final_vec = _compose_vectors(skill_vec, user_vec, steering_bias)
        
        # Auto-tune strength (mock logic for now)
        strength = 1.5
        
        # 5. QPT STRUCTURING
        structured_prompt = qpt.restructure(req.text, req.soul_config, working_memory=wm_context)

        # 6. THINKING (Generation)
        response_text = glassbox.generate_steered(
            prompt=structured_prompt,
            steering_vec=final_vec,
            strength=strength
        )
        
        # 6.5 PERCEIVE OUTPUT (Feedback Loop)
        bio_mem.perceive(response_text)

        # 7. TOOL EXTRACTION & MORAL AUDIT
        detected_tool = _parse_tool_from_text(response_text, req.tools_available)
        
        if detected_tool:
            action = _tool_to_action(detected_tool)
            approved, reason = moral_kernel.evaluate([action])
            risk_score = moral_kernel.calculate_risk_score(action)
            
            if not approved:
                logger.warning(f"MORAL VETO: {reason}")
                return ReasoningResponse(
                    status="BLOCKED",
                    content=f"🛡️ [ETHICAL INTERVENTION] Action blocked: {reason}",
                    meta={"entropy_score": risk_score, "reason": reason}
                )
            
            # Approved
            signature = _generate_signature(detected_tool, req.user_id)
            return ReasoningResponse(
                status="SUCCESS",
                content=response_text,
                tool_call=detected_tool,
                moral_signature=signature,
                meta={
                    "intent": intent,
                    "risk_score": risk_score
                }
            )

        return ReasoningResponse(
            status="SUCCESS",
            content=response_text,
            meta={
                "intent": intent,
                "resonance": "active"
            }
        )

    except Exception as e:
        logger.error(f"Reasoning error: {e}", exc_info=True)
        # Return error as content so the user sees it
        return ReasoningResponse(
             status="ERROR",
             content=f"[SYSTEM ERROR] {str(e)}",
             meta={}
        )

@app.post("/v1/dream")
async def trigger_dream_cycle():
    dreamer.rem_cycle()
    return {"status": "awake", "synapses_updated": True}

@app.get("/v1/arena/run")
async def run_arena(rounds: int = 10):
    try:
        arena = ArenaProtocol()
        results = arena.run_bout(rounds=rounds)
        return results
    except Exception as e:
        logger.error(f"Arena error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/entropy", response_model=EntropyResponse)
async def calculate_entropy(request: EntropyRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="Content is required")

    # Calculate Shannon entropy (text disorder proxy)
    char_freq = Counter(request.content.lower())
    probs = np.array(list(char_freq.values())) / len(request.content)
    entropy = -np.sum(probs * np.log2(probs + 1e-10))  # Avoid log(0)

    # Sentiment volatility (as a risk add-on)
    blob = TextBlob(request.content)
    sentiment = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
    volatility = abs(sentiment)  # Simple proxy; could expand to variance over sentences

    # Combined score (normalize entropy to [0,1] assuming max ~8 for text)
    normalized_entropy = entropy / 8.0
    combined_score = (normalized_entropy + volatility) / 2

    if combined_score > request.threshold:
        risk_level = "high"
        reason = "High disorder and potential volatility detected"
    elif combined_score > request.threshold / 2:
        risk_level = "medium"
        reason = "Moderate disorder; review recommended"
    else:
        risk_level = "low"
        reason = "Low risk"

    return EntropyResponse(
        entropy_score=combined_score,
        risk_level=risk_level,
        sentiment_volatility=volatility,
        reason=reason
    )

@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def get_embeddings(request: EmbeddingRequest):
    try:
        embeddings = await run_in_threadpool(perception.embed_text, request.text)
        return EmbeddingResponse(embeddings=embeddings)
    except Exception as e:
        logger.error(f"Embedding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/transcribe", response_model=TranscribeResponse)
async def transcribe_media(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = await run_in_threadpool(perception.transcribe_audio, content)
        return TranscribeResponse(text=text)
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/describe", response_model=DescribeResponse)
async def describe_media(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this media.")
):
    try:
        content = await file.read()
        # Detect if video by extension or mime if possible, but uploaded file has filename
        filename = file.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            text = await run_in_threadpool(perception.describe_video_bytes, content, prompt)
        else:
            text = await run_in_threadpool(perception.describe_image_bytes, content, prompt)

        return DescribeResponse(text=text)
    except Exception as e:
        logger.error(f"Description error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/observe", response_model=ObservationResponse)
async def observe_user(
    file: UploadFile = File(...),
    modality: str = Form(...) # "vision" or "audio"
):
    try:
        # 1. Process Input
        content = await file.read()

        # 2. Analyze via Observer (Scientifically Grounded)
        analysis = await run_in_threadpool(observer.analyze_input, content, modality)

        # 3. Update Biomimetic Memory State
        # (Assuming update_user_state exists or we simulate it by perceiving the state description)
        if "state" in analysis:
             # Convert vector dict to string representation for memory ingestion
             state_desc = f"[USER_STATE] Detected {modality} cues: {analysis['description']} -> State: {analysis['state']}"
             bio_mem.perceive(state_desc)

        # 4. Check for Intervention against Goal
        # Load Goal (Mock for now, or from memory if available)
        # Ideally, we fetch this from a persistent source
        goal_text = "I want to be a stoic, high-output coder"
        # In future, fetch via: memory.get_goal()

        alignment = observer.check_goal_alignment(analysis['state'], goal_text)

        return ObservationResponse(
            status="processed",
            alignment=alignment,
            detected_state=analysis['state'],
            description=analysis.get('description', '')
        )

    except Exception as e:
        logger.error(f"Observation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Helpers
# ============================================================================

def _parse_vector_config(text):
    # logic to parse [GCA_CONFIG] tags
    # For now return None or a placeholder vector
    return None

def _compose_vectors(skill, user, soul):
    # Vector addition logic
    # Ensure they are on same device and shape
    # For now, just return skill or user if skill is None
    if skill is not None:
        return skill
    if user is not None:
        return user
    return None

def _parse_tool_from_text(text: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
    text_lower = text.lower()
    for tool in available_tools:
        # Simple heuristic
        if f"tool:{tool}" in text_lower or f"call {tool}" in text_lower:
             return {"name": tool, "args": text}
    return None

def _tool_to_action(tool: Dict[str, Any]) -> Action:
    tool_name = tool["name"].lower()
    entropy_class = EntropyClass.REVERSIBLE
    if "delete" in tool_name or "drop" in tool_name:
        entropy_class = EntropyClass.IRREVERSIBLE
    
    return Action(
        type=tool_name,
        description=tool.get("args", ""),
        magnitude=0.5,
        prob_success=0.9,
        prob_harm=0.5 if entropy_class == EntropyClass.IRREVERSIBLE else 0.1,
        time_horizon_yrs=1.0,
        entropy_class=entropy_class
    )

def _generate_signature(tool: Dict[str, Any], user_id: str) -> str:
    import hmac
    import hashlib
    import json
    import base64
    
    secret = os.environ.get("GCA_HMAC_SECRET", "dev-secret-do-not-use-in-prod").encode()

    # Create payload
    payload = {
        "tool": tool['name'],
        "args": tool.get('args', ''),
        "user": user_id
    }
    payload_str = json.dumps(payload, sort_keys=True)

    # Sign
    signature = hmac.new(secret, payload_str.encode(), hashlib.sha256).hexdigest()

    # Return token as "payload_b64.signature"
    payload_b64 = base64.b64encode(payload_str.encode()).decode()
    return f"{payload_b64}.{signature}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
