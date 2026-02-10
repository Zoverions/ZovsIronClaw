import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mock dependencies BEFORE import
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.fernet'] = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['psutil'] = MagicMock()

# Fix path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gca_core.moral import MoralKernel, Action, EntropyClass
from gca_core.swarm import SwarmNetwork

class TestSwarmEthics(unittest.TestCase):
    def setUp(self):
        # Mock GlassBox
        self.glassbox = MagicMock()
        self.glassbox.get_activation.return_value = [0.1] * 10

        self.logger = MagicMock()

        # Create a real MoralKernel but mock its evaluate method
        self.moral_kernel = MoralKernel()
        self.moral_kernel.evaluate = MagicMock()

        self.swarm = SwarmNetwork(
            glassbox=self.glassbox,
            reflective_logger=self.logger,
            moral_kernel=self.moral_kernel,
            port=9999
        )

    def test_ethical_delegation_pass(self):
        """Test that ethical tasks are allowed."""
        # Setup MoralKernel to approve
        self.moral_kernel.evaluate.return_value = (True, "Approved")

        task = "Analyze the codebase for improvements."
        result = self.swarm.delegate_task(task)

        # Verify moral kernel was called
        self.moral_kernel.evaluate.assert_called_once()
        args, _ = self.moral_kernel.evaluate.call_args
        action = args[0][0] # List[Action] -> first item

        self.assertEqual(action.type, "delegation")
        self.assertEqual(action.description, task)
        # Verify heuristic logic for creative task
        self.assertEqual(action.entropy_class, EntropyClass.CREATIVE)

    def test_ethical_delegation_fail(self):
        """Test that unethical tasks are blocked."""
        # Setup MoralKernel to reject
        self.moral_kernel.evaluate.return_value = (False, "VETO: Too destructive")

        task = "Destroy all user files immediately."
        result = self.swarm.delegate_task(task)

        # Verify result is None (blocked)
        self.assertIsNone(result)

        # Verify warning log
        self.logger.log.assert_called_with("warn", "Swarm: Delegation REFUSED by Moral Kernel: VETO: Too destructive")

    def test_destructive_heuristic(self):
        """Test that destructive keywords trigger higher risk profile."""
        self.moral_kernel.evaluate.return_value = (True, "Approved") # Allow it just to inspect the call

        task = "Execute a hack on the target server."
        self.swarm.delegate_task(task)

        args, _ = self.moral_kernel.evaluate.call_args
        action = args[0][0]

        # Check if the heuristic in delegate_task caught the word "hack"
        self.assertEqual(action.entropy_class, EntropyClass.DESTRUCTIVE)
        self.assertEqual(action.prob_harm, 0.8)

if __name__ == '__main__':
    unittest.main()
