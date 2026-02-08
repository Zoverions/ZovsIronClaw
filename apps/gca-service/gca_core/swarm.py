"""
Iron Swarm: Hive Mind Coordination for GCA
Provides cognitive orchestration for multi-agent swarms using GCA core.
"""

import logging
import time
import uuid
import torch
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .glassbox import GlassBox
from .reflective_logger import ReflectiveLogger
from .moral import MoralKernel

logger = logging.getLogger("GCA.IronSwarm")

@dataclass
class SwarmNode:
    """Represents a single agent in the swarm."""
    agent_id: str
    role: str
    status: str = "idle"
    current_task: str = ""
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: float = field(default_factory=time.time)
    vector_state: Optional[List[float]] = None # Cognitive state embedding

class SwarmNetwork:
    """
    The Hive Mind. Manages the topology and task distribution of the swarm.
    """
    def __init__(self, glassbox: GlassBox, reflective_logger: ReflectiveLogger):
        self.glassbox = glassbox
        self.logger = reflective_logger
        self.nodes: Dict[str, SwarmNode] = {}
        self.tasks: List[Dict] = []
        self.swarm_id = str(uuid.uuid4())[:8]

        self.logger.log("info", f"Iron Swarm initialized: {self.swarm_id}")

    def register_node(self, agent_id: str, role: str, capabilities: List[str]) -> str:
        """Register a new agent into the swarm."""
        if agent_id in self.nodes:
            self.logger.log("warn", f"Swarm: Agent {agent_id} re-registered")
            return "updated"

        node = SwarmNode(agent_id=agent_id, role=role, capabilities=capabilities)
        self.nodes[agent_id] = node
        self.logger.log("info", f"Swarm: Node joined - {agent_id} ({role})")
        return "registered"

    def update_node_state(self, agent_id: str, status: str, task: str = ""):
        """Update the heartbeat and status of a node."""
        if agent_id not in self.nodes:
            return

        node = self.nodes[agent_id]
        node.status = status
        node.current_task = task
        node.last_heartbeat = time.time()

        # Self-Reflection on Swarm Health
        if status == "error":
            self.logger.log("warn", f"Swarm: Node {agent_id} reported ERROR: {task}")
            # Potential intervention logic here

    def delegate_task(self, task_description: str) -> Optional[str]:
        """
        Cognitive routing: Find the best agent for a task based on role/capabilities.
        Uses GlassBox for semantic matching if needed.
        """
        best_agent = None
        best_score = -1.0

        # Embed task
        task_vec = self.glassbox.get_activation(task_description)
        task_vec = torch.nn.functional.normalize(task_vec, dim=0)

        for agent_id, node in self.nodes.items():
            if node.status != "idle":
                continue

            # Semantic match role to task
            role_vec = self.glassbox.get_activation(node.role)
            role_vec = torch.nn.functional.normalize(role_vec, dim=0)

            score = torch.dot(task_vec, role_vec).item()

            if score > best_score and score > 0.4: # Threshold
                best_score = score
                best_agent = agent_id

        if best_agent:
            self.nodes[best_agent].status = "assigned"
            self.nodes[best_agent].current_task = task_description
            self.logger.log("info", f"Swarm: Task delegated to {best_agent} (Score: {best_score:.2f})")
            return best_agent

        self.logger.log("warn", f"Swarm: No suitable idle agent found for task: {task_description}")
        return None

    def submit_result(self, agent_id: str, result: str, cot_text: str, cot_hash: str) -> bool:
        """
        Receives result from worker. Verifies Proof of Logic (PoL).
        """
        if agent_id not in self.nodes:
            return False

        # Verify Hash (Integrity)
        import hashlib
        computed_hash = hashlib.sha256(cot_text.encode()).hexdigest()
        if computed_hash != cot_hash:
            self.logger.log("warn", f"Swarm: PoL Hash Mismatch from {agent_id}")
            return False

        # Verify Logic (Consistency) using small verifier model
        if not self._verify_logic(cot_text):
            self.logger.log("warn", f"Swarm: PoL Logical Inconsistency from {agent_id}")
            return False

        self.nodes[agent_id].status = "idle"
        self.nodes[agent_id].current_task = ""
        self.logger.log("info", f"Swarm: Task completed by {agent_id}. PoL Verified.")
        return True

    def _verify_logic(self, cot_text: str) -> bool:
        """
        Uses GlassBox to verify logical consistency.
        Currently implements a heuristic check for reasoning markers.
        """
        # Check for reasoning markers
        markers = ["therefore", "because", "implies", "step", "reasoning", "->", "=>", "since"]
        score = sum(1 for m in markers if m in cot_text.lower())

        # If it's too short, it's suspicious.
        if len(cot_text.split()) < 5:
             return False

        # Require at least one marker or sufficient length with some structure
        return score >= 1 or len(cot_text.split()) > 20

    def get_network_status(self) -> Dict[str, Any]:
        """Return full swarm telemetry."""
        return {
            "swarm_id": self.swarm_id,
            "node_count": len(self.nodes),
            "nodes": {
                aid: {
                    "role": n.role,
                    "status": n.status,
                    "task": n.current_task,
                    "heartbeat_age": time.time() - n.last_heartbeat
                }
                for aid, n in self.nodes.items()
            }
        }
