"""
Iron Chain: Lightweight Blockchain for Decentralized Identity and Governance.
Implements a Proof-of-Authority / Proof-of-Logic consensus mechanism for the Iron Swarm.
"""

import hashlib
import json
import time
import logging
import base64
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger("GCA.Chain")

@dataclass
class Transaction:
    """
    Represents a state change in the distributed ledger.
    """
    id: str
    type: str # GENESIS, TRANSFER, PROPOSAL, VOTE, TASK_COMPLETION
    sender: str  # Public Key
    recipient: str # Public Key or Contract Address
    payload: Dict[str, Any]
    timestamp: float
    signature: str = ""

    def to_dict(self):
        return asdict(self)

    def calculate_hash(self) -> str:
        tx_copy = self.to_dict()
        tx_copy.pop('signature', None)
        tx_string = json.dumps(tx_copy, sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

@dataclass
class Block:
    """
    A container for transactions linked to the previous block.
    """
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    validator: str # Public Key of the node that created this block
    signature: str = ""
    hash: str = ""

    def to_dict(self):
        d = asdict(self)
        # Handle nested Transaction objects
        d['transactions'] = [
            tx.to_dict() if hasattr(tx, 'to_dict') else tx
            for tx in self.transactions
        ]
        return d

    def calculate_hash(self) -> str:
        block_copy = self.to_dict()
        block_copy.pop('hash', None)
        block_copy.pop('signature', None)
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.nodes = set()
        self.security_manager = None # Injected for signing

        # Governance State
        self.active_policies: Dict[str, Any] = {}
        self.proposals: Dict[str, Dict] = {} # proposal_id -> details
        self.votes: Dict[str, Dict[str, str]] = {} # proposal_id -> {voter_id: vote}

        # Create Genesis Block
        self.create_genesis_block()

    def set_security_manager(self, security_manager):
        self.security_manager = security_manager

    def create_genesis_block(self):
        genesis_tx = Transaction(
            id="0",
            type="GENESIS",
            sender="SYSTEM",
            recipient="ALL",
            payload={"message": "Iron Swarm Genesis"},
            timestamp=time.time(),
            signature="GENESIS_SIG"
        )

        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0",
            validator="SYSTEM",
            signature="GENESIS_SIG",
            hash=""
        )
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)
        logger.info("Iron Chain Genesis Block created.")

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Transaction) -> bool:
        # Verify signature
        if transaction.type != "GENESIS":
            try:
                tx_hash = transaction.calculate_hash()
                if not self._verify_signature(transaction.sender, tx_hash, transaction.signature):
                    logger.warning(f"Invalid signature for transaction {transaction.id}")
                    return False
            except Exception as e:
                logger.error(f"Error verifying transaction {transaction.id}: {e}")
                return False

        # Prevent duplicates
        for tx in self.pending_transactions:
            if tx.id == transaction.id:
                return False

        self.pending_transactions.append(transaction)
        logger.info(f"Transaction {transaction.id} added to pending.")
        return True

    def create_block(self) -> Optional[Block]:
        """
        Bundles pending transactions into a new block.
        Requires security_manager to be set to sign the block.
        """
        if not self.security_manager:
            logger.error("Cannot mine block: No security manager available for signing.")
            return None

        if not self.pending_transactions:
            # logger.debug("No transactions to mine.")
            return None

        last_block = self.get_last_block()

        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.hash,
            validator=self.security_manager.get_public_key_b64()
        )

        # Reset pending
        self.pending_transactions = []

        # Hash and Sign
        new_block.hash = new_block.calculate_hash()

        # Sign the hash (as proof of authority)
        # Note: We sign the block hash, not the whole block content directly,
        # though usually one signs the serialized block content.
        # Let's sign the serialized content (minus signature/hash) which is what calculate_hash uses.
        block_content_str = new_block.calculate_hash() # Wait, calculate_hash returns the hash of content. Signing the hash is standard.
        new_block.signature = self.security_manager.sign_message(block_content_str) # This signs the hash string

        # Add to local chain
        self.chain.append(new_block)

        # Process Block (update state)
        self.process_block(new_block)

        logger.info(f"Block {new_block.index} mined by {new_block.validator[:10]}...")
        return new_block

    def receive_block(self, block: Block) -> bool:
        """
        Receives a block from the network, validates it, and appends if valid.
        """
        last_block = self.get_last_block()

        # 1. Check Index
        if block.index != last_block.index + 1:
            if block.index > last_block.index + 1:
                 logger.warning(f"Received future block {block.index}. Need sync.")
                 # Sync logic would go here
            return False

        # 2. Check Previous Hash
        if block.previous_hash != last_block.hash:
            logger.warning(f"Block {block.index} previous hash mismatch.")
            return False

        # 3. Verify Hash Integrity
        calculated_hash = block.calculate_hash()
        if calculated_hash != block.hash:
             logger.warning(f"Block {block.index} hash invalid.")
             return False

        # 4. Verify Signature (Proof of Authority)
        # Ideally, we verify against a known validator list.
        # For now, we accept any signature that matches the validator public key provided in the block.
        # This is "open entry" Proof of Authority.
        if not self._verify_signature(block.validator, calculated_hash, block.signature):
             logger.warning(f"Block {block.index} signature invalid.")
             return False

        # Add and Process
        self.chain.append(block)
        self.process_block(block)

        # Remove mined transactions from pending
        tx_ids = set(tx.id for tx in block.transactions)
        self.pending_transactions = [t for t in self.pending_transactions if t.id not in tx_ids]

        logger.info(f"Block {block.index} added to chain.")
        return True

    def process_block(self, block: Block):
        """Update internal state based on block transactions."""
        for tx in block.transactions:
            if tx.type == "PROPOSAL":
                self._handle_proposal(tx)
            elif tx.type == "VOTE":
                self._handle_vote(tx)

    def _handle_proposal(self, tx: Transaction):
        prop_id = tx.payload.get("proposal_id") or tx.id
        choices = tx.payload.get("choices", ["yes", "no"])

        self.proposals[prop_id] = {
            "creator": tx.sender,
            "title": tx.payload.get("title"),
            "description": tx.payload.get("description"),
            "choices": choices,
            "status": "active",
            "vote_counts": {c: 0 for c in choices},
            "deadline": tx.timestamp + 86400 # 24 hours default
        }
        self.votes[prop_id] = {}
        logger.info(f"Governance Proposal created: {prop_id}")

    def _handle_vote(self, tx: Transaction):
        prop_id = tx.payload.get("proposal_id")
        choice = tx.payload.get("choice")

        if prop_id in self.proposals and self.proposals[prop_id]["status"] == "active":
            prop = self.proposals[prop_id]
            if choice not in prop["vote_counts"]:
                return # Invalid choice

            # Check double vote
            if tx.sender in self.votes[prop_id]:
                return

            self.votes[prop_id][tx.sender] = choice
            prop["vote_counts"][choice] += 1

            logger.info(f"Vote cast on {prop_id}: {choice}")

    def get_active_policies(self) -> Dict[str, Any]:
        """Return currently active governance policies."""
        return self.active_policies

    def get_governance_state(self) -> Dict[str, Any]:
        """Return full governance state including active proposals."""
        # Update deadlines before returning
        self.check_proposal_deadlines()
        return {
            "active_policies": self.active_policies,
            "proposals": self.proposals
        }

    def check_proposal_deadlines(self):
        """Check if any proposals have expired and should be enacted/rejected."""
        now = time.time()
        for pid, prop in self.proposals.items():
            if prop["status"] == "active" and now >= prop["deadline"]:
                # Finalize
                counts = prop["vote_counts"]
                total_votes = sum(counts.values())

                # Determine winner
                if total_votes > 0:
                    winner = max(counts, key=counts.get)
                    # Simple majority check for "yes" vs "no" or just highest vote
                    # If binary yes/no, require > 50% yes
                    if "yes" in counts and "no" in counts and len(counts) == 2:
                        if counts["yes"] > total_votes / 2:
                            prop["status"] = "passed"
                            logger.info(f"Proposal {pid} PASSED.")
                        else:
                            prop["status"] = "rejected"
                            logger.info(f"Proposal {pid} REJECTED.")
                    else:
                        prop["status"] = f"passed_winner_{winner}"
                        logger.info(f"Proposal {pid} RESOLVED: Winner {winner}")
                else:
                    prop["status"] = "expired_no_votes"
                    logger.info(f"Proposal {pid} EXPIRED (No votes).")

    def _verify_signature(self, pub_key_b64: str, message: str, signature_b64: str) -> bool:
        # We need a utility to verify external signatures.
        # SecurityManager has verify_signature but relies on its instance.
        # We can construct a public key from b64 string.
        # Since we don't want to duplicate logic, let's assume SecurityManager is available OR import verify logic.
        # We'll use the one from security module directly or via our instance if available.
        # Actually, SecurityManager.verify_signature accepts public_key_bytes.

        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            import base64

            pub_bytes = base64.b64decode(pub_key_b64)
            key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            sig_bytes = base64.b64decode(signature_b64)

            key.verify(sig_bytes, message.encode('utf-8'))
            return True
        except Exception as e:
            logger.debug(f"Signature verification error: {e}")
            return False
