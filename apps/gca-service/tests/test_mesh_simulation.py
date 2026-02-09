import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
import time

# Mock torch and psutil before importing gca_core
sys.modules['torch'] = MagicMock()
sys.modules['psutil'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['einops'] = MagicMock()
sys.modules['moviepy'] = MagicMock()
sys.modules['qwen_vl_utils'] = MagicMock()

# Add path: apps/gca-service/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from gca_core.mesh import MeshNetwork, MeshNode
from gca_core.resource_manager import SystemProfile

class TestMeshSimulation(unittest.TestCase):
    @patch('socket.socket')
    def test_discovery_logic(self, mock_socket_ctor):
        """Test that MeshNetwork correctly parses discovery packets."""
        mock_sock = MagicMock()
        mock_socket_ctor.return_value = mock_sock

        # Initialize MeshNetwork
        # Note: __init__ creates socket, so we mock it above
        net = MeshNetwork("agent_1", 8000, SystemProfile.TITAN)

        # Simulate incoming packet from another node
        payload = {
            "agent_id": "agent_2",
            "port": 8001,
            "role": "spark",
            "capabilities": ["test"],
            "timestamp": time.time()
        }
        data = json.dumps(payload).encode('utf-8')
        addr = ('192.168.1.100', 5555) # Source IP and port

        # Manually trigger packet handling
        net._handle_packet(data, addr)

        # Verify peers list
        peers = net.get_active_nodes()
        self.assertEqual(len(peers), 1)
        node = peers[0]
        self.assertEqual(node.agent_id, "agent_2")
        self.assertEqual(node.role, "spark")
        self.assertEqual(node.host, "192.168.1.100")
        self.assertEqual(node.port, 8001)

if __name__ == '__main__':
    unittest.main()
