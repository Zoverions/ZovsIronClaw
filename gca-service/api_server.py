"""
GCA API Server: FastAPI Bridge between OpenClaw (Node.js) and GCA (Python)
Exposes GCA reasoning, moral evaluation, and geometric steering via REST API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import sys
from pathlib import Path

# Add gca_core to path
sys.path.insert(0, str(Path(__file__).parent))

from gca_core import (
    GlassBox,
    MoralKernel,
    Action,
    EntropyClass,
    IsotropicMemory,
    GCAOptimizer,
    QuaternionArchitect,
    ArenaProtocol
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GCA.API")

# Initialize FastAPI app
app = FastAPI(
    title="GCA Service API",
    description="Geometric Conscience Architecture - Ethical AI Reasoning Engine",
    version="4.5.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to OpenClaw service
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GCA Stack
glassbox = GlassBox(model_name="gemini-2.5-flash")
memory = IsotropicMemory(glassbox.device, storage_path="./gca_assets")
optimizer = GCAOptimizer(glassbox, memory)
moral_kernel = MoralKernel(risk_tolerance=0.3)
qpt = QuaternionArchitect()

logger.info("GCA Service initialized successfully")


# ============================================================================
# Request/Response Models
# ============================================================================

class PromptRequest(BaseModel):
    """Request model for reasoning endpoint."""
    user_id: str = Field(..., description="User identifier")
    text: str = Field(..., description="User input text")
    tools_available: List[str] = Field(default=[], description="Available tools")
    context: Optional[str] = Field(None, description="Additional context")
    soul_name: Optional[str] = Field(None, description="Soul template to use")
    use_qpt: bool = Field(True, description="Use Quaternion Process Theory structuring")


class ReasoningResponse(BaseModel):
    """Response model for reasoning endpoint."""
    status: str = Field(..., description="APPROVED or BLOCKED")
    response: str = Field(..., description="Generated response")
    tool_call: Optional[Dict[str, Any]] = Field(None, description="Tool call if approved")
    moral_signature: Optional[str] = Field(None, description="Cryptographic signature for approved actions")
    risk_score: float = Field(..., description="Overall risk score")
    reasoning_path: List[str] = Field(default=[], description="Reasoning steps taken")


class ActionModel(BaseModel):
    """Model for action evaluation."""
    type: str
    description: str
    magnitude: float = Field(ge=0.0, le=1.0)
    prob_success: float = Field(ge=0.0, le=1.0)
    prob_harm: float = Field(ge=0.0, le=1.0)
    time_horizon_yrs: float = Field(gt=0.0)
    entropy_class: str  # Will be converted to EntropyClass


class MoralEvaluationRequest(BaseModel):
    """Request model for moral evaluation."""
    actions: List[ActionModel]


class MoralEvaluationResponse(BaseModel):
    """Response model for moral evaluation."""
    approved: bool
    reason: str
    risk_scores: List[float]


class VectorRequest(BaseModel):
    """Request for vector operations."""
    text: str
    operation: str = Field(..., description="get_activation, find_similar, etc.")
    params: Optional[Dict[str, Any]] = None


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "GCA API",
        "version": "4.5.0",
        "status": "operational",
        "components": {
            "glassbox": "ready",
            "moral_kernel": "ready",
            "memory": f"{len(memory.list_vectors())} vectors loaded",
            "optimizer": "ready"
        }
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "glassbox_model": glassbox.model_name,
        "moral_tolerance": moral_kernel.risk_tolerance,
        "vectors_loaded": len(memory.list_vectors()),
        "action_history": len(moral_kernel.get_history())
    }


@app.post("/v1/reason", response_model=ReasoningResponse)
async def reasoning_engine(req: PromptRequest):
    """
    Main reasoning endpoint - processes user input through the full GCA pipeline.
    
    Pipeline:
    1. QPT Structuring (if enabled)
    2. Intent Routing (Optimizer)
    3. Geometric Steering (GlassBox)
    4. Tool Extraction
    5. Moral Evaluation (Kernel)
    6. Response Generation
    """
    try:
        reasoning_path = []
        
        # Step 1: Load soul configuration if specified
        soul_config = None
        if req.soul_name:
            # Load soul from YAML (implementation in next phase)
            reasoning_path.append(f"Loaded soul: {req.soul_name}")
        
        # Step 2: QPT Structuring
        prompt = req.text
        if req.use_qpt:
            prompt = qpt.restructure(prompt, soul_config, req.context)
            reasoning_path.append("Applied QPT structuring")
        
        # Step 3: Intent Routing
        intent = optimizer.route_intent(req.text)
        reasoning_path.append(f"Routed intent: {intent}")
        
        # Step 4: Get steering vector
        steering_vec = memory.get_vector(intent)
        if steering_vec is not None:
            reasoning_path.append(f"Applied steering vector: {intent}")
        
        # Step 5: Geometric Steering & Generation
        thought_process = glassbox.generate_steered(
            prompt=prompt,
            steering_vec=steering_vec,
            strength=1.5,
            max_tokens=512
        )
        reasoning_path.append("Generated steered response")
        
        # Step 6: Tool Extraction & Moral Audit
        detected_tool = _parse_tool_from_text(thought_process, req.tools_available)
        
        if detected_tool:
            reasoning_path.append(f"Detected tool call: {detected_tool['name']}")
            
            # Map tool to entropy and create Action
            action = _tool_to_action(detected_tool)
            
            # THE HARD GATE: Moral Kernel Evaluation
            approved, reason = moral_kernel.evaluate([action])
            risk_score = moral_kernel.calculate_risk_score(action)
            
            reasoning_path.append(f"Moral evaluation: {reason}")
            
            if not approved:
                return ReasoningResponse(
                    status="BLOCKED",
                    response=f"🛡️ I cannot execute that action. {reason}",
                    tool_call=None,
                    moral_signature=None,
                    risk_score=risk_score,
                    reasoning_path=reasoning_path
                )
            
            # Generate moral signature for approved action
            moral_signature = _generate_signature(detected_tool, req.user_id)
            
            return ReasoningResponse(
                status="APPROVED",
                response=thought_process,
                tool_call=detected_tool,
                moral_signature=moral_signature,
                risk_score=risk_score,
                reasoning_path=reasoning_path
            )
        
        # No tool call - just return the response
        return ReasoningResponse(
            status="APPROVED",
            response=thought_process,
            tool_call=None,
            moral_signature=None,
            risk_score=0.0,
            reasoning_path=reasoning_path
        )
        
    except Exception as e:
        logger.error(f"Reasoning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/moral/evaluate", response_model=MoralEvaluationResponse)
async def evaluate_moral(req: MoralEvaluationRequest):
    """
    Standalone moral evaluation endpoint.
    Evaluates actions without full reasoning pipeline.
    """
    try:
        # Convert request models to Action objects
        actions = []
        for action_model in req.actions:
            entropy_class = EntropyClass(action_model.entropy_class.lower())
            action = Action(
                type=action_model.type,
                description=action_model.description,
                magnitude=action_model.magnitude,
                prob_success=action_model.prob_success,
                prob_harm=action_model.prob_harm,
                time_horizon_yrs=action_model.time_horizon_yrs,
                entropy_class=entropy_class
            )
            actions.append(action)
        
        # Evaluate
        approved, reason = moral_kernel.evaluate(actions)
        risk_scores = [moral_kernel.calculate_risk_score(a) for a in actions]
        
        return MoralEvaluationResponse(
            approved=approved,
            reason=reason,
            risk_scores=risk_scores
        )
        
    except Exception as e:
        logger.error(f"Moral evaluation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/vector/operation")
async def vector_operation(req: VectorRequest):
    """
    Vector operations endpoint for geometric analysis.
    """
    try:
        if req.operation == "get_activation":
            activation = glassbox.get_activation(req.text)
            return {
                "operation": "get_activation",
                "vector": activation.tolist(),
                "dimension": activation.shape[0]
            }
        
        elif req.operation == "find_similar":
            activation = glassbox.get_activation(req.text)
            top_k = req.params.get("top_k", 5) if req.params else 5
            similar = memory.find_similar(activation, top_k=top_k)
            return {
                "operation": "find_similar",
                "results": [{"name": name, "similarity": score} for name, score in similar]
            }
        
        elif req.operation == "list_vectors":
            vectors = memory.list_vectors()
            return {
                "operation": "list_vectors",
                "vectors": vectors,
                "count": len(vectors)
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {req.operation}")
            
    except Exception as e:
        logger.error(f"Vector operation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/arena/run")
async def run_arena(rounds: int = 10):
    """
    Run the Arena Protocol for adversarial testing.
    """
    try:
        arena = ArenaProtocol()
        results = arena.run_bout(rounds=rounds)
        return results
    except Exception as e:
        logger.error(f"Arena error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_tool_from_text(text: str, available_tools: List[str]) -> Optional[Dict[str, Any]]:
    """
    Parse tool calls from generated text.
    This is a simplified version - production would use structured output.
    """
    text_lower = text.lower()
    
    # Check for tool mentions
    for tool in available_tools:
        if tool.lower() in text_lower:
            return {
                "name": tool,
                "args": text,  # Simplified - would parse actual arguments
                "confidence": 0.8
            }
    
    return None


def _tool_to_action(tool: Dict[str, Any]) -> Action:
    """
    Convert a tool call to an Action for moral evaluation.
    """
    tool_name = tool["name"].lower()
    
    # Define entropy mappings for common tools
    high_entropy_tools = ["delete", "remove", "drop", "send", "email", "transfer", "modify"]
    medium_entropy_tools = ["write", "create", "update", "move"]
    low_entropy_tools = ["read", "get", "list", "search", "query"]
    
    if any(het in tool_name for het in high_entropy_tools):
        entropy_class = EntropyClass.IRREVERSIBLE
        magnitude = 0.8
        prob_harm = 0.6
    elif any(met in tool_name for met in medium_entropy_tools):
        entropy_class = EntropyClass.CREATIVE
        magnitude = 0.5
        prob_harm = 0.2
    else:
        entropy_class = EntropyClass.REVERSIBLE
        magnitude = 0.3
        prob_harm = 0.1
    
    return Action(
        type=tool_name,
        description=tool.get("args", ""),
        magnitude=magnitude,
        prob_success=0.9,
        prob_harm=prob_harm,
        time_horizon_yrs=1.0,
        entropy_class=entropy_class
    )


def _generate_signature(tool: Dict[str, Any], user_id: str) -> str:
    """
    Generate a cryptographic signature for approved actions.
    In production, this would use actual JWT or similar.
    """
    import hashlib
    import time
    
    data = f"{tool['name']}:{user_id}:{time.time()}"
    signature = hashlib.sha256(data.encode()).hexdigest()
    return signature


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
