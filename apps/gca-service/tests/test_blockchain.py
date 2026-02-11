import pytest
import time
import os
import shutil
import sys
from pathlib import Path

# Add gca_core directory directly to path to bypass __init__.py which loads torch
sys.path.insert(0, str(Path(__file__).parent.parent / "gca_core"))

import blockchain
from blockchain import Blockchain, Transaction, Block
import security
from security import SecurityManager

# Cleanup test artifacts
@pytest.fixture(scope="module")
def security_manager():
    key_path = "/tmp/test_identity.pem"
    if os.path.exists(key_path):
        os.remove(key_path)

    sm = SecurityManager()
    mnemonic = sm.generate_passphrase()
    sm.derive_keys(mnemonic)
    sm.save_keys(key_path)
    yield sm
    if os.path.exists(key_path):
        os.remove(key_path)

def test_blockchain_init():
    chain = Blockchain()
    assert len(chain.chain) == 1
    assert chain.chain[0].transactions[0].type == "GENESIS"

def test_transaction_creation_and_signing(security_manager):
    chain = Blockchain()
    chain.set_security_manager(security_manager)

    sender = security_manager.get_wallet_address()

    tx = Transaction(
        id="tx1",
        type="TRANSFER",
        sender=sender,
        recipient="recipient_key",
        payload={"amount": 10},
        timestamp=time.time()
    )

    # Sign
    tx_hash = tx.calculate_hash()
    tx.signature = security_manager.sign_message(tx_hash)

    assert chain.add_transaction(tx) == True
    assert len(chain.pending_transactions) == 1

def test_block_mining(security_manager):
    chain = Blockchain()
    chain.set_security_manager(security_manager)

    sender = security_manager.get_wallet_address()
    tx = Transaction(
        id="tx_mine",
        type="TRANSFER",
        sender=sender,
        recipient="recipient_key",
        payload={"amount": 50},
        timestamp=time.time()
    )
    tx.signature = security_manager.sign_message(tx.calculate_hash())
    chain.add_transaction(tx)

    block = chain.create_block()

    assert block is not None
    assert block.index == 1
    assert len(block.transactions) == 1
    assert block.validator == sender
    assert len(chain.chain) == 2
    assert len(chain.pending_transactions) == 0

def test_governance_lifecycle(security_manager):
    chain = Blockchain()
    chain.set_security_manager(security_manager)
    sender = security_manager.get_wallet_address()

    # 1. Create Proposal
    prop_tx = Transaction(
        id="prop1",
        type="PROPOSAL",
        sender=sender,
        recipient="GOV",
        payload={
            "proposal_id": "prop1",
            "title": "Test Prop",
            "description": "Test"
        },
        timestamp=time.time()
    )
    prop_tx.signature = security_manager.sign_message(prop_tx.calculate_hash())
    chain.add_transaction(prop_tx)

    # Mine Block 1 (Proposal Active)
    chain.create_block()
    state = chain.get_governance_state()
    assert "prop1" in state["proposals"]
    assert state["proposals"]["prop1"]["status"] == "active"

    # 2. Vote
    vote_tx = Transaction(
        id="vote1",
        type="VOTE",
        sender=sender,
        recipient="GOV",
        payload={"proposal_id": "prop1", "choice": "yes"},
        timestamp=time.time()
    )
    vote_tx.signature = security_manager.sign_message(vote_tx.calculate_hash())
    chain.add_transaction(vote_tx)

    # Mine Block 2 (Vote Counted)
    chain.create_block()
    state = chain.get_governance_state()
    assert state["proposals"]["prop1"]["vote_counts"]["yes"] == 1

    # 3. Simulate Deadline Passing
    chain.proposals["prop1"]["deadline"] = time.time() - 1
    chain.check_proposal_deadlines()

    assert chain.proposals["prop1"]["status"] == "passed"

def test_chain_validation(security_manager):
    chain = Blockchain()
    chain.set_security_manager(security_manager)

    # Create a valid block
    tx = Transaction(id="tx_valid", type="test", sender=security_manager.get_wallet_address(), recipient="you", payload={}, timestamp=time.time())
    tx.signature = security_manager.sign_message(tx.calculate_hash())
    chain.add_transaction(tx)
    block = chain.create_block()

    # Verify via receive_block logic (simulating another node)
    # Note: receive_block checks signatures, so we need a chain instance that trusts or verifies
    # Since we use the same security manager, verification should pass.

    chain2 = Blockchain() # Receiver
    # chain2 doesn't need security_manager to receive, but needs crypto libs which are imported

    # Reset chain2 to genesis match (create_genesis_block is deterministic mostly, except timestamp?)
    # Wait, Genesis timestamp is time.time(). It won't match.
    # We must sync genesis first for test validity.
    chain2.chain = [chain.chain[0]]

    assert chain2.receive_block(block) == True
    assert len(chain2.chain) == 2

    # Tamper with block
    block.hash = "fakehash"
    assert chain2.receive_block(block) == False # Should fail hash check (actually index check first since we already added it)

    # Create a new block on chain 1
    tx2 = Transaction(id="tx_valid2", type="test", sender=security_manager.get_wallet_address(), recipient="you", payload={}, timestamp=time.time())
    tx2.signature = security_manager.sign_message(tx2.calculate_hash())
    chain.add_transaction(tx2)
    block2 = chain.create_block()

    # Tamper content
    block2.transactions[0].payload = {"hacked": True}
    # This invalidates the hash check
    assert chain2.receive_block(block2) == False

def test_registry_and_transfer(security_manager):
    chain = Blockchain()
    chain.set_security_manager(security_manager)
    sender = security_manager.get_wallet_address()
    agent_id = "test-agent-01"

    # 1. Register Device
    reg_tx = Transaction(
        id="reg1",
        type="REGISTER_DEVICE",
        sender=sender,
        recipient="REGISTRY",
        payload={"agent_id": agent_id},
        timestamp=time.time()
    )
    reg_tx.signature = security_manager.sign_message(reg_tx.calculate_hash())
    chain.add_transaction(reg_tx)

    # Mine
    chain.create_block()
    assert chain.verify_identity(agent_id, sender) == True
    assert chain.verify_identity(agent_id, "wrongkey") == False

    # 2. Transfer (should fail with 0 balance)
    tx_fail = Transaction(
        id="tx_fail",
        type="TRANSFER",
        sender=sender,
        recipient="receiver",
        payload={"amount": 10},
        timestamp=time.time()
    )
    tx_fail.signature = security_manager.sign_message(tx_fail.calculate_hash())
    chain.add_transaction(tx_fail)
    chain.create_block()

    assert chain.get_balance(sender) == 0
    # Transfer logic logs warning but updates balance? Wait, let's check implementation.
    # Implementation checks: if sender_bal < amount and tx.type != "GENESIS": return
    # So balance should remain 0
    assert chain.get_balance("receiver") == 0

    # 3. Genesis Transfer (Minting)
    mint_tx = Transaction(
        id="mint1",
        type="GENESIS", # Allows creating money out of thin air
        sender="SYSTEM",
        recipient=sender,
        payload={"amount": 100},
        timestamp=time.time()
    )
    # We need to sign this? The code checks signature if type != GENESIS.
    # So we can just add it.
    chain.add_transaction(mint_tx)
    chain.create_block()

    assert chain.get_balance(sender) == 100

    # 4. Valid Transfer
    tx_ok = Transaction(
        id="tx_ok",
        type="TRANSFER",
        sender=sender,
        recipient="receiver",
        payload={"amount": 50},
        timestamp=time.time()
    )
    tx_ok.signature = security_manager.sign_message(tx_ok.calculate_hash())
    chain.add_transaction(tx_ok)
    chain.create_block()

    assert chain.get_balance(sender) == 50
    assert chain.get_balance("receiver") == 50
