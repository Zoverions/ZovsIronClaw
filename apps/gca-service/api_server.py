"""
GCA API Server: FastAPI Bridge between OpenClaw (Node.js) and GCA (Python)
Exposes GCA reasoning, moral evaluation, and geometric steering via REST API.
Integrates Recursive Universe Framework for Causal Flow Analysis.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import logging
import sys
import yaml
import os
import time
import json
from pathlib import Path
import numpy as np
from textblob import TextBlob
from collections import Counter

# Add gca_core to path
sys.path.insert(0, str(Path(__file__).parent))

from gca_core.glassbox import GlassBox
from gca_core.resource_manager import ResourceManager
from gca_core.moral import MoralKernel, Action, EntropyClass
from gca_core.optimizer import GCAOptimizer
from gca_core.tools import Tool
from gca_core.memory import IsotropicMemory
from gca_core.resonance import ResonanceEngine
from gca_core.qpt import QuaternionArchitect
from gca_core.arena import ArenaProtocol
from gca_core.memory_advanced import BiomimeticMemory
from gca_core.perception import PerceptionSystem
from gca_core.observer import Observer
from gca_core.pulse import PulseSystem
from gca_core.causal_flow import CausalFlowEngine
from gca_core.swarm import SwarmNetwork
from gca_core.reflective_logger import ReflectiveLogger
from gca_core.soul_loader import get_soul_loader
from gca_core.security import SecurityManager
from dreamer import DeepDreamer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# We will use ReflectiveLogger as the main logger for GCA core logic
base_logger = logging.getLogger("IronClaw")

# Load Config via Resource Manager
config_path = "config.yaml"
resource_manager = ResourceManager(config_path=config_path)
CFG = resource_manager.get_active_config()
logger = logging.getLogger("GCA.API")
logger.info(f"Loaded Profile: {CFG.get('active_profile', 'unknown').upper()}")

# Initialize FastAPI app
app = FastAPI(
    title="GCA Service API",
    description="Geometric Conscience Architecture - Ethical AI Reasoning Engine",
    version="4.5.1"
)

# Restrict CORS to local development and Tauri origins
origins = [
    "http://localhost:5173",
    "tauri://localhost",
    "https://tauri.localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- INIT CORE COMPONENTS ---
logger.info("Booting IronClaw Core...")
glassbox = GlassBox(config=CFG)
memory = IsotropicMemory(glassbox.device, storage_path="./gca_assets")
bio_mem = BiomimeticMemory(glassbox, memory)
dreamer = DeepDreamer(bio_mem)

optimizer = GCAOptimizer(glassbox, memory)
moral_kernel = MoralKernel(risk_tolerance=0.3)
resonance = ResonanceEngine(glassbox, memory)
qpt = QuaternionArchitect()
perception = PerceptionSystem(config=CFG)
observer = Observer(glassbox)
causal_engine = CausalFlowEngine(glassbox)

# Init Reflective Logger first so Pulse can use it
reflective_logger = ReflectiveLogger(glassbox, bio_mem, moral_kernel)

# Pulse System (v4.8)
pulse = PulseSystem(bio_mem, glassbox, causal_engine=causal_engine, qpt=qpt)

# Pulse Intervention Hook
def pulse_correction(msg):
    # Log intervention and inject into next memory context
    reflective_logger.log("warning", f"PULSE INTERVENTION: {msg}")
    bio_mem.perceive(f"SYSTEM_INTERVENTION: {msg}")

pulse.set_intervention_callback(pulse_correction)
pulse.start()

# Initialize Security Manager
# Use user home directory for persistent identity
identity_path = os.path.expanduser("~/.gca/identity.pem")
security_manager = SecurityManager(key_path=identity_path)

if not security_manager.private_key:
    logger.warning(f"No identity keys found at {identity_path}. Run setup to generate.")
else:
    logger.info(f"Identity keys loaded successfully from {identity_path}.")

# Init Iron Swarm
swarm_network = SwarmNetwork(glassbox, reflective_logger, moral_kernel, profile=resource_manager.profile, port=8000)
if security_manager.private_key:
    swarm_network.mesh.set_security_manager(security_manager)
swarm_network.mesh.start()

# Bind Introspection Loop: Logger -> Observer
# We create a lambda to bridge the callback signature
def introspection_callback(modality, content, metadata):
    # Fire and forget to avoid blocking logger
    try:
        # Assuming we are in an event loop context, or just run directly if lightweight
        # Since observer.process_input is synchronous (CPU bound), we can call it.
        observer.process_input(modality, content, metadata)
    except Exception as e:
        print(f"Introspection callback failed: {e}")

reflective_logger.bind_observer(introspection_callback)

base_logger.info("GCA Service initialized successfully with Reflective Logger")

# ============================================================================
# Models
# ============================================================================

class SecurityInitResponse(BaseModel):
    mnemonic: str

class SecurityConfirmRequest(BaseModel):
    mnemonic: str

class SoulConfig(BaseModel):
    base_style: str  # e.g., "Architect"
    blend_styles: List[str] = [] # ["Stoic", "Python"]
    blend_weights: List[float] = [] # [0.3, 0.2]

class ReasonRequest(BaseModel):
    user_id: str = Field(..., max_length=100)
    text: str = Field(..., max_length=100000)
    soul_config: Optional[str] = ""
    soul_object: Optional[SoulConfig] = None # v4.6 Dynamic Soul
    input_modality: Optional[str] = "text" # 'text' or 'voice'
    tools_available: List[str] = []
    context: Optional[str] = None # For additional context like previous messages
    environmental_context: Optional[str] = None # Weather, Location, Mood, etc.

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

class ObservationRequest(BaseModel):
    content: str = Field(..., max_length=5000)
    modality: str = "text" # text, audio, vision
    source: Optional[str] = "unknown"
    timestamp: Optional[float] = None

class ObservationResponse(BaseModel):
    status: str
    alignment: float
    detected_state: Union[List[float], str]
    description: str

class SwarmTaskRequest(BaseModel):
    task: str
    context: Optional[str] = None

class MemorySyncRequest(BaseModel):
    engrams: List[Dict[str, Any]]

# OpenAI Chat Completion Schemas
class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "profile": CFG.get("active_profile"),
        "model": glassbox.model_name,
        "device": glassbox.device,
        "vectors_loaded": len(memory.list_vectors()),
        "pulse_entropy": pulse.current_entropy,
        "mesh_peers": len(swarm_network.mesh.get_active_nodes()),
        "identity_secured": security_manager.private_key is not None
    }

@app.post("/v1/setup/security/init", response_model=SecurityInitResponse)
async def init_security():
    """Generate a new 12-word mnemonic for the user."""
    mnemonic = security_manager.generate_passphrase()
    return SecurityInitResponse(mnemonic=mnemonic)

@app.post("/v1/setup/security/confirm")
async def confirm_security(req: SecurityConfirmRequest):
    """Confirm mnemonic, derive keys, and save identity."""
    try:
        security_manager.derive_keys(req.mnemonic)

        # Create directory if needed
        identity_path = os.path.expanduser("~/.gca/identity.pem")
        os.makedirs(os.path.dirname(identity_path), exist_ok=True)

        security_manager.save_keys(identity_path)

        # Reload mesh with new identity?
        # Ideally, we should restart mesh, but updating key in memory is enough for now.
        # We need to inject the security manager into the mesh if we haven't already.
        # (This will be handled in the mesh update step)
        if swarm_network and swarm_network.mesh:
            swarm_network.mesh.set_security_manager(security_manager)

        logger.info("Identity secured and saved.")
        return {"status": "success", "message": "Identity established."}
    except Exception as e:
        logger.error(f"Security confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/swarm/task")
async def handle_remote_task(req: SwarmTaskRequest):
    """Executes a task delegated from the mesh."""
    logger.info(f"Executing remote task: {req.task[:50]}...")

    # Reuse glassbox for execution
    prompt = f"Context: {req.context}\nTask: {req.task}\n\nExecute this task."
    try:
        response = glassbox.generate_steered(prompt, strength=1.0)
        return {"status": "success", "content": response}
    except Exception as e:
        logger.error(f"Remote task error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/soul/current")
async def get_current_soul():
    """Returns the active soul configuration for sync."""
    loader = get_soul_loader()
    # Assuming active soul is default 'Architect' or derived from config
    soul = loader.get_soul("Architect")
    if soul:
        return soul.to_dict()
    return {"error": "No active soul found"}

@app.get("/v1/soul/list")
async def list_souls():
    """Returns the list of available souls and their details."""
    loader = get_soul_loader()
    souls = loader.list_souls()
    details = {}
    for soul_name in souls:
        details[soul_name] = loader.get_soul_info(soul_name)
    return {"souls": souls, "details": details}

@app.post("/v1/memory/sync")
async def sync_memory(req: MemorySyncRequest):
    """Receive memories from peers for Shared Consciousness."""
    try:
        count = bio_mem.inject_external(req.engrams)
        return {"status": "synced", "count": count}
    except Exception as e:
        logger.error(f"Memory sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    OpenAI-compatible Chat Completion endpoint.
    Exposes native OpenClaw tools to the GCA brain.
    """
    start_time = time.time()

    # Extract latest user message
    user_msg = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if not user_msg:
        # Fallback if no user message found (e.g. system prompt only)
        return _openai_response_text("GCA: No user message found.", req.model)

    user_text = user_msg.content
    if isinstance(user_text, list):
        # Handle multimodal content array
        text_parts = [p.get("text", "") for p in user_text if p.get("type") == "text"]
        user_text = " ".join(text_parts)

    # 2. Dynamic Tool Handling (v4.9.5)
    # Convert OpenAI schemas to GCA Tool objects
    dynamic_tools = []
    tool_names = []
    if req.tools:
        for t in req.tools:
            if "function" in t:
                func = t["function"]
                name = func["name"]
                tool_names.append(name)
                # Create a dynamic Tool object
                # Attempt to guess intent from description or name
                # For now, default to 'EXTERNAL'
                dynamic_tools.append(Tool(
                    name=name,
                    description=func.get("description", "External tool from OpenClaw"),
                    parameters=func.get("parameters", {}),
                    intent_vector="EXTERNAL"
                ))

    # Call Internal GCA Reasoning Logic

    # 1. Check Pulse
    if pulse.current_entropy > 0.8:
        return _openai_response_text(
            "🛡️ [SYSTEM HALT] Mental entropy critical. Please rephrase.",
            req.model,
            finish_reason="stop"
        )

    # 2. Soul Parsing from Model Name
    soul_name = "Architect"  # Default
    if req.model.lower().startswith("gca-"):
        parts = req.model.split("-")
        if len(parts) > 1:
            soul_name = parts[1].capitalize()

    loader = get_soul_loader()
    soul = loader.get_soul(soul_name)
    # Create a minimal soul config representation for QPT
    soul_config_str = f"soul: {soul_name}"
    if soul:
        # If we could access vector mix, we would pass it.
        # For now, we rely on QPT picking up the soul name in context.
        pass

    context_str = "\n".join([f"{m.role}: {m.content}" for m in req.messages[:-1]])

    # Run the GCA Pipeline
    try:
        # Intent Routing
        intent = optimizer.route_intent(user_text)

        # Soul & Memory
        skill_vec = memory.get_vector(intent)
        wm_context = bio_mem.retrieve_context(skill_vec)

        # QPT Structure
        structured_prompt = qpt.restructure(
            raw_prompt=user_text,
            soul_config=soul_config_str,
            context=context_str,
            working_memory=wm_context
        )

        # Tool Injection
        if dynamic_tools:
            # Use new prioritize_tools to sort by relevance to intent
            relevant_tools = optimizer.prioritize_tools(dynamic_tools, user_text)
            tool_definitions = "\n".join([t.format_prompt() for t in relevant_tools])

            # Inject tools into prompt
            structured_prompt += f"\n\n[AVAILABLE TOOLS]\n{tool_definitions}\nTo use a tool, output: TOOL_CALL: <tool_name> <arguments>"

        # Generate (Steering)
        # Ideally, we'd compose vectors here: Skill + Soul
        # But for now, we rely on GlassBox using the base model and skill vector if available.
        # Note: If we had _compose_vectors exposed, we could use it.
        # But logic is local to reasoning_engine.
        # Let's just pass strength=1.0 for now.

        response_text = glassbox.generate_steered(
            prompt=structured_prompt,
            strength=1.0,
            temperature=req.temperature
        )

        # Parse for Tool Calls
        tool_call_data = _parse_tool_from_text(response_text, tool_names)

        if tool_call_data:
            # Moral Check
            action = _tool_to_action(tool_call_data)
            approved, reason = moral_kernel.evaluate([action])

            if not approved:
                return _openai_response_text(
                    f"🛡️ [MORAL INTERVENTION] I cannot execute {tool_call_data['name']}. Reason: {reason}",
                    req.model
                )

            # Approved - Format as OpenAI Tool Call
            return _openai_response_tool_call(
                tool_call_data["name"],
                tool_call_data["args"],
                req.model,
                content=response_text # Include thought process in content
            )

        # Standard Text Response
        return _openai_response_text(response_text, req.model)

    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        return _openai_response_text(f"GCA Error: {str(e)}", req.model)

@app.post("/v1/soul/compose")
async def compose_soul(config: SoulConfig):
    """
    v4.6: Dynamic Vector Blending.
    Returns the vector statistics of the new composite soul.
    """
    loader = get_soul_loader()

    # Construct blending parameters
    # Base soul is always included
    base_souls = [config.base_style] + config.blend_styles

    # Weights
    # If blend_weights are provided, we assume 1.0 for base and then the rest
    if config.blend_weights:
        weights = [1.0] + config.blend_weights
    else:
        weights = None # soul_loader will equal-weight them

    try:
        composite = loader.create_composite_soul(
            name=f"{config.base_style}-Composite",
            base_souls=base_souls,
            weights=weights
        )
    except Exception as e:
        logger.error(f"Error composing soul: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if not composite:
        raise HTTPException(status_code=404, detail="One or more souls not found.")

    return {
        "status": "composed",
        "name": composite.name,
        "vector_norm": 1.0,
        "components": base_souls,
        "weights": weights,
        "traits": composite.traits
    }

@app.post("/v1/observe")
async def observe_environment(req: ObservationRequest):
    try:
        # Pass metadata as dict
        metadata = {"source": req.source, "timestamp": req.timestamp}

        # Run in threadpool to avoid blocking event loop with pytorch ops
        result = await run_in_threadpool(
            observer.process_input,
            req.modality,
            req.content,
            metadata
        )
        return result
    except Exception as e:
        logger.error(f"Observation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/reason", response_model=ReasoningResponse)
async def reasoning_engine(req: ReasonRequest):
    reflective_logger.log("info", f"Incoming from {req.user_id}: {req.text[:50]}...")

    # v4.8: Pulse Check
    if pulse.current_entropy > 0.8:
        return ReasoningResponse(
            status="BLOCKED",
            content="[SYSTEM HALT] Mental entropy too high. Please restate intent clearly.",
            meta={"entropy_score": pulse.current_entropy}
        )

    try:
        # 0. CAUSAL ANALYSIS
        # We assume text is both micro and macro for self-analysis unless context provided
        causal_metrics = causal_engine.calculate_causal_beta(req.text, req.text)

        # 1. PARSE SOUL CONFIG
        soul_positive, soul_negative = _parse_vector_config(req.soul_config)
        
        # v4.6: Dynamic Soul Object Override
        if req.soul_object:
            # We would resolve vectors here. For now, we append to soul_positive if names match skills
            # This is a basic integration.
            pass

        # 1.5 PERCEIVE (Sensory Input + Environment)
        # We pass environmental_context here so memory can capture "The Mood of the City"
        bio_mem.perceive(req.text, env_context=req.environmental_context)

        # 2. INGEST & RESONANCE
        resonance.ingest(req.user_id, req.text)
        user_vec = resonance.get_style_vector(req.user_id)
        
        # 3. GEOMETRIC ROUTING
        intent = optimizer.route_intent(req.text)
        skill_vec = memory.get_vector(intent)

        # Update user insight with actual intent
        bio_mem.track_user_pattern(req.user_id, causal_metrics.get('beta_c', 0), intent)

        # 3.5 RETRIEVE WORKING MEMORY CONTEXT
        wm_context = bio_mem.retrieve_context(skill_vec)

        # 4. VECTOR COMPOSITION
        # Final = Skill + UserResonance + SoulBias - AntiBias
        final_vec = _compose_vectors(skill_vec, user_vec, soul_positive, soul_negative)
        
        # Auto-tune strength (mock logic for now)
        strength = 1.5
        
        # 5. QPT STRUCTURING (Recursive Universe Injection)
        # We inject the causal analysis and environmental context into the QPT 'w' scalar
        context_str = req.context or ""
        if req.environmental_context:
            context_str += f"\n[Environment] {req.environmental_context}"

        structured_prompt = qpt.restructure(
            raw_prompt=req.text,
            soul_config=req.soul_config,
            context=context_str,
            working_memory=wm_context,
            causal_analysis=causal_metrics
        )

        # 5.5 TOOL INJECTION
        if req.tools_available:
            # v4.9: Native Tool Integration - Use Optimizer to select and format tools
            relevant_tools = optimizer.select_relevant_tools(req.text, req.tools_available)
            tool_definitions = "\n".join([t.format_prompt() for t in relevant_tools])

            structured_prompt += f"\n\n[AVAILABLE TOOLS]\n{tool_definitions}\nTo use a tool, output: TOOL_CALL: <tool_name> <arguments>"

        # 6. THINKING (Generation)
        response_text = glassbox.generate_steered(
            prompt=structured_prompt,
            steering_vec=final_vec,
            strength=strength
        )
        
        # 6.5 PERCEIVE OUTPUT (Feedback Loop)
        bio_mem.perceive(response_text)

        # Causal Analysis of Response (Self-Reflection)
        response_metrics = causal_engine.calculate_causal_beta(response_text, response_text)

        # 7. TOOL EXTRACTION & MORAL AUDIT
        detected_tool = _parse_tool_from_text(response_text, req.tools_available)
        
        if detected_tool:
            action = _tool_to_action(detected_tool)

            # Inject Causal/Assembly Data into Action for Moral Kernel
            action.target_network_assembly = causal_metrics.get('network_assembly', 0.0)
            action.is_causally_emergent = causal_metrics.get('is_emergent', False)

            approved, reason = moral_kernel.evaluate([action])
            risk_score = moral_kernel.calculate_risk_score(action)
            
            if not approved:
                reflective_logger.log("warn", f"MORAL VETO: {reason}")
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
                    "risk_score": risk_score,
                    "causal_flow": causal_metrics,
                    "response_causal_flow": response_metrics
                }
            )

        return ReasoningResponse(
            status="SUCCESS",
            content=response_text,
            meta={
                "intent": intent,
                "resonance": "active",
                "causal_flow": causal_metrics,
                "response_causal_flow": response_metrics
            }
        )

    except Exception as e:
        reflective_logger.log("error", f"Reasoning error: {e}")
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

        # Run Causal Flow Analysis on the description
        # We don't change the response structure of describe, but we could log or trigger side effects
        causal_metrics = causal_engine.calculate_causal_beta(text, text)
        if causal_metrics.get("is_emergent"):
            logger.info(f"✨ EMERGENT VISUAL DETECTED: {text[:50]}...")
            text = f"[✨ EMERGENT SIGNAL] {text}"

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
        # Load Goal from .agent/prompts/GOAL.md
        goal_path = Path(__file__).parent.parent / ".agent" / "prompts" / "GOAL.md"
        if goal_path.exists():
            with open(goal_path, "r") as f:
                goal_text = f.read().strip()
        else:
            goal_text = "I want to be a stoic, high-output coder" # Fallback

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

def _openai_response_text(content: str, model: str, finish_reason: str = "stop") -> Dict[str, Any]:
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": finish_reason
        }],
        "usage": {
            "prompt_tokens": 0, # Placeholder
            "completion_tokens": len(content.split()),
            "total_tokens": len(content.split())
        }
    }

def _openai_response_tool_call(name: str, args: str, model: str, content: str = None) -> Dict[str, Any]:
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
                "tool_calls": [{
                    "id": f"call_{int(time.time())}",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": args # JSON string
                    }
                }]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

def _parse_vector_config(text):
    if not text:
        return None, None
    try:
        # Assume text is the content of SOUL.md which is YAML
        data = yaml.safe_load(text)
        if isinstance(data, dict):
            return data.get("base_vector_mix"), data.get("anti_vectors")
    except Exception as e:
        logger.warning(f"Failed to parse soul config: {e}")
    return None, None

def _compose_vectors(skill, user, soul_pos_config, soul_neg_config):
    # Start with skill vector
    final = None
    device = glassbox.device

    if skill is not None:
        final = skill.to(device)

    # Add User
    if user is not None:
        user = user.to(device)
        if final is None:
            final = user
        else:
            final += user

    # Add Soul Positive
    if soul_pos_config:
        for item in soul_pos_config:
            name = item.get("skill")
            weight = float(item.get("weight", 1.0))
            vec = memory.get_vector(name)
            if vec is not None:
                vec = vec.to(device)
                if final is None:
                    final = vec * weight
                else:
                    final += vec * weight

    # Subtract Soul Negative
    if soul_neg_config:
        for item in soul_neg_config:
            name = item.get("skill")
            weight = float(item.get("weight", 1.0))
            vec = memory.get_vector(name)
            if vec is not None:
                vec = vec.to(device)
                if final is None:
                    final = -vec * weight
                else:
                    final -= vec * weight

    return final

def _parse_tool_from_text(text: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
    text_lower = text.lower()

    # 1. Try to find explicit tool call patterns like TOOL_CALL: <name> <args>
    # (Matches the instructions injected in /v1/chat/completions)
    import re
    match = re.search(r"TOOL_CALL:\s*(\w+)\s+(.*)", text, re.IGNORECASE)
    if match:
        name = match.group(1)
        args = match.group(2).strip()
        if name in available_tools:
            return {"name": name, "args": args}

    # 2. Fallback heuristic
    for tool in available_tools:
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
    import secrets
    
    env_secret = os.environ.get("GCA_HMAC_SECRET")
    if not env_secret:
        # Generate a random secret if not provided in environment
        # Note: This means signatures won't persist across restarts unless secret is set.
        # This is a security trade-off for safety by default.
        logger.warning("GCA_HMAC_SECRET not set. Using random ephemeral secret.")
        if not hasattr(_generate_signature, "_ephemeral_secret"):
            _generate_signature._ephemeral_secret = secrets.token_bytes(32)
        secret = _generate_signature._ephemeral_secret
    else:
        secret = env_secret.encode()

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
    # Default to localhost for security
    host = os.environ.get("GCA_HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=8000)
