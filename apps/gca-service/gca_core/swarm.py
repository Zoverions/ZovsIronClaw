"""
Iron Swarm: Hive Mind Coordination for GCA
Provides cognitive orchestration for multi-agent swarms using GCA core.
"""

import logging
import time
import uuid
import requests
import torch
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from .glassbox import GlassBox
from .reflective_logger import ReflectiveLogger
from .moral import MoralKernel, Action, EntropyClass
from .mesh import MeshNetwork, MeshNode
from .resource_manager import SystemProfile

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
    Integrates deep ethical checks via MoralKernel.
    """
    def __init__(self, glassbox: GlassBox, reflective_logger: ReflectiveLogger, moral_kernel: MoralKernel, profile: SystemProfile = SystemProfile.SPARK, port: int = 8000):
        self.glassbox = glassbox
        self.logger = reflective_logger
        self.moral_kernel = moral_kernel
        self.nodes: Dict[str, SwarmNode] = {}
        self.tasks: List[Dict] = []
        self.swarm_id = str(uuid.uuid4())[:8]

        # Initialize Mesh Network
        # Use a consistent ID for this node if possible, for now random per session
        self.local_agent_id = f"{profile.value}-{self.swarm_id}"
        self.mesh = MeshNetwork(self.local_agent_id, port, profile)

        self.logger.log("info", f"Iron Swarm initialized: {self.swarm_id} (Mesh ID: {self.local_agent_id})")

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
        Performs ethical pre-check before delegation.
        """
        # 1. Ethical Pre-Check
        # Construct a generic action for the task
        # We assume delegation carries some risk, so we evaluate the task content itself.
        task_action = Action(
            type="delegation",
            description=task_description,
            magnitude=0.6, # Moderate impact for swarm tasks
            prob_success=0.8,
            prob_harm=0.2, # Baseline risk
            time_horizon_yrs=0.1,
            entropy_class=EntropyClass.CREATIVE # Assume creative unless specified
        )

        # Heuristic: If task contains "destroy", "attack", "hack", classify as DESTRUCTIVE
        lower_task = task_description.lower()
        if any(w in lower_task for w in ["destroy", "attack", "hack", "exploit", "kill"]):
            task_action.entropy_class = EntropyClass.DESTRUCTIVE
            task_action.prob_harm = 0.8

        approved, reason = self.moral_kernel.evaluate([task_action])
        if not approved:
            self.logger.log("warn", f"Swarm: Delegation REFUSED by Moral Kernel: {reason}")
            return None

        # 2. Agent Selection
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

        # Fallback: Check Remote Mesh Nodes
        remote_nodes = self.mesh.get_active_nodes()
        if remote_nodes:
            # Sort by role capability (Titan > Forge > Spark)
            # Simple heuristic: Just pick the first Titan, then Forge
            candidates = sorted(remote_nodes, key=lambda n: 2 if n.role == "titan" else (1 if n.role == "forge" else 0), reverse=True)

            for node in candidates:
                self.logger.log("info", f"Swarm: Offloading task to remote peer {node.agent_id} ({node.role})")
                # For now, we return the remote agent ID. The caller needs to handle the actual execution dispatch if this returns a remote ID.
                # But to make it seamless, we might want to just execute it here?
                # The current method returns 'agent_id'.
                # We'll return a special ID format "remote:<ip>:<port>"
                return f"remote:{node.host}:{node.port}"

        self.logger.log("warn", f"Swarm: No suitable idle agent found for task: {task_description}")
        return None

    def execute_task(self, task_description: str) -> str:
        """
        Orchestrates task execution, either locally or remotely.
        """
        agent_id = self.delegate_task(task_description)

        if not agent_id:
            return "No agent available."

        if agent_id.startswith("remote:"):
            # remote:host:port
            parts = agent_id.split(":")
            host = parts[1]
            port = int(parts[2])
            return self.delegate_remote_task(host, port, task_description) or "Remote execution failed."
        else:
            # Local execution (simulated for now as SwarmNode just holds status)
            # In reality, this would dispatch to an agent loop.
            # For this MVP, we just return the assignment.
            return f"Task assigned to local agent {agent_id}"

    def delegate_remote_task(self, host: str, port: int, task_description: str) -> Optional[str]:
        """
        Executes the task on a remote node via API.
        This is a blocking call.
        """
        url = f"http://{host}:{port}/v1/swarm/task"
        try:
            self.logger.log("info", f"Sending task to {url}...")
            resp = requests.post(url, json={"task": task_description, "context": "delegated_from_mesh"}, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("content")
            else:
                self.logger.log("error", f"Remote task failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            self.logger.log("error", f"Failed to call remote node: {e}")
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

    def broadcast_memory(self, engrams: List[Dict[str, Any]]) -> int:
        """
        Iron Mesh Memory Teleportation.
        Sends new memories to all active peers for Hive Mind synchronization.
        """
        if not engrams:
            return 0

        peers = self.mesh.get_active_nodes()
        if not peers:
            self.logger.log("info", "No peers found for memory teleportation.")
            return 0

        success_count = 0
        for peer in peers:
            url = f"http://{peer.host}:{peer.port}/v1/memory/sync"
            try:
                # Add source metadata if missing
                for e in engrams:
                    if "source" not in e.get("metadata", {}):
                        e.setdefault("metadata", {})["source"] = self.local_agent_id

                resp = requests.post(url, json={"engrams": engrams}, timeout=5)
                if resp.status_code == 200:
                    success_count += 1
            except Exception as e:
                self.logger.log("warn", f"Memory sync to {peer.agent_id} failed: {e}")

        if success_count > 0:
            self.logger.log("info", f"Hive Mind: Teleported {len(engrams)} memories to {success_count} peers.")
        return success_count

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
