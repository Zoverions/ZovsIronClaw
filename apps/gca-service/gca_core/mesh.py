"""
GCA Mesh Network: Decentralized Discovery & Soul Sync
Implements UDP broadcasting for local peer discovery and establishing the "AA Mesh".
"""

import socket
import threading
import time
import json
import logging
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from .resource_manager import SystemProfile

logger = logging.getLogger("GCA.Mesh")

BROADCAST_PORT = 5999
BROADCAST_INTERVAL = 5.0
PEER_TIMEOUT = 15.0

@dataclass
class MeshNode:
    agent_id: str
    host: str
    port: int
    role: str # TITAN, FORGE, SPARK
    capabilities: List[str]
    last_seen: float = 0.0

    def to_dict(self):
        d = asdict(self)
        d.pop('last_seen', None)
        return d

class MeshNetwork:
    def __init__(self, agent_id: str, port: int, profile: SystemProfile):
        self.agent_id = agent_id
        self.port = port # API Port
        self.profile = profile
        self.running = False
        self.nodes: Dict[str, MeshNode] = {}
        self.lock = threading.Lock()

        # UDP Socket for Broadcasting
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
             try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
             except Exception:
                pass # Not supported on all platforms

        # Bind to 0.0.0.0 to listen on all interfaces
        try:
            self.sock.bind(('', BROADCAST_PORT))
        except Exception as e:
            logger.warning(f"Failed to bind UDP port {BROADCAST_PORT}: {e}. Mesh discovery disabled.")
            self.sock = None

    def start(self):
        if not self.sock:
            return

        self.running = True

        # Start Broadcaster
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()

        # Start Listener
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

        logger.info(f"Mesh Network started. Agent ID: {self.agent_id}")

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

    def get_active_nodes(self) -> List[MeshNode]:
        """Return nodes seen within PEER_TIMEOUT."""
        now = time.time()
        active = []
        with self.lock:
            # Filter out stale nodes
            to_remove = []
            for nid, node in self.nodes.items():
                if now - node.last_seen < PEER_TIMEOUT:
                    active.append(node)
                else:
                    to_remove.append(nid)

            for nid in to_remove:
                del self.nodes[nid]

        return active

    def _broadcast_loop(self):
        while self.running:
            try:
                payload = {
                    "agent_id": self.agent_id,
                    "port": self.port,
                    "role": self.profile.value,
                    "capabilities": ["reasoning", "memory_sync"], # Basic set
                    "timestamp": time.time()
                }
                msg = json.dumps(payload).encode('utf-8')
                self.sock.sendto(msg, ('<broadcast>', BROADCAST_PORT))
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")

            time.sleep(BROADCAST_INTERVAL)

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                self._handle_packet(data, addr)
            except Exception as e:
                if self.running:
                    logger.debug(f"Listen error: {e}")

    def _handle_packet(self, data: bytes, addr):
        try:
            payload = json.loads(data.decode('utf-8'))
            remote_id = payload.get("agent_id")

            if remote_id == self.agent_id:
                return # Ignore self

            with self.lock:
                is_new = remote_id not in self.nodes

                node = MeshNode(
                    agent_id=remote_id,
                    host=addr[0], # IP from UDP packet
                    port=payload.get("port", 8000),
                    role=payload.get("role", "spark"),
                    capabilities=payload.get("capabilities", []),
                    last_seen=time.time()
                )
                self.nodes[remote_id] = node

                if is_new:
                    logger.info(f"Mesh: Discovered peer {remote_id} ({node.role}) at {node.host}:{node.port}")

        except Exception as e:
            logger.debug(f"Packet parse error: {e}")
