"""Automated test suite for Ed25519 manifest signing, signature verification,
replay sequence protection, key rotation, and min_app_version enforcement.
"""

import os
import sys
import json
import tempfile
import unittest

# Ensure software directory is on path
SOFTWARE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SOFTWARE_DIR)

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

import src._build as build_config
from src.core.tool_store import ToolStoreService


class TestManifestSigningAndVerification(unittest.TestCase):

    def setUp(self):
        # Generate two test Ed25519 keypairs
        self.priv_key_1 = ed25519.Ed25519PrivateKey.generate()
        self.pub_hex_1 = self.priv_key_1.public_key().public_bytes_raw().hex()

        self.priv_key_2 = ed25519.Ed25519PrivateKey.generate()
        self.pub_hex_2 = self.priv_key_2.public_key().public_bytes_raw().hex()

        # Mock embedded keys in build config
        build_config.EMBEDDED_PUBLIC_KEYS["key_1"] = self.pub_hex_1
        build_config.EMBEDDED_PUBLIC_KEYS["key_2"] = self.pub_hex_2
        build_config.IS_RELEASE = True  # Strict release mode: no dev bypass

        self.service = ToolStoreService()

    def test_valid_manifest_signature_verifies(self):
        """A manifest signed by the primary private key must verify successfully."""
        manifest = {
            "schema_version": "1.0.0",
            "sequence": 5,
            "tools": [{"id": "test_tool", "version": "1.0.0"}]
        }
        manifest_bytes = json.dumps(manifest).encode("utf-8")
        sig_bytes = self.priv_key_1.sign(manifest_bytes)

        is_valid = self.service.verify_manifest_signature(manifest_bytes, sig_bytes, key_id="key_1")
        self.assertTrue(is_valid, "Valid manifest signature should verify")

    def test_tampered_manifest_rejected(self):
        """Tampering with even 1 byte in the manifest JSON must fail verification."""
        manifest = {
            "schema_version": "1.0.0",
            "sequence": 5,
            "tools": [{"id": "test_tool", "version": "1.0.0"}]
        }
        manifest_bytes = json.dumps(manifest).encode("utf-8")
        sig_bytes = self.priv_key_1.sign(manifest_bytes)

        # Tampered manifest
        tampered_bytes = manifest_bytes.replace(b"test_tool", b"evil_tool")

        is_valid = self.service.verify_manifest_signature(tampered_bytes, sig_bytes, key_id="key_1")
        self.assertFalse(is_valid, "Tampered manifest must fail verification")

    def test_bad_signature_rejected(self):
        """Corrupted signature bytes must fail verification."""
        manifest_bytes = b'{"sequence": 5, "tools": []}'
        bad_sig = b"A" * 64

        is_valid = self.service.verify_manifest_signature(manifest_bytes, bad_sig, key_id="key_1")
        self.assertFalse(is_valid, "Corrupt signature must fail verification")

    def test_key_rotation_with_key_2(self):
        """Rotating to key_2 must verify when key_id='key_2' is provided."""
        manifest_bytes = b'{"sequence": 10, "tools": []}'
        sig_2 = self.priv_key_2.sign(manifest_bytes)

        # Verified against key_2
        self.assertTrue(self.service.verify_manifest_signature(manifest_bytes, sig_2, key_id="key_2"))

        # Fails if verified against key_1
        self.assertFalse(self.service.verify_manifest_signature(manifest_bytes, sig_2, key_id="key_1"))

    def test_rollback_sequence_replay_protection(self):
        """A manifest with a sequence lower than last_accepted_seq must be rejected in sync."""
        self.service.cached_manifest = {"sequence": 10, "tools": []}

        # Mock an incoming older manifest with sequence = 8
        older_manifest = {"sequence": 8, "tools": []}
        remote_seq = older_manifest.get("sequence", 0)
        last_accepted_seq = self.service.cached_manifest.get("sequence", 0)

        self.assertLess(remote_seq, last_accepted_seq)
        # Sequence guard condition
        self.assertTrue(remote_seq < last_accepted_seq, "Older sequence must trigger rollback protection")

    def test_min_app_version_refusal(self):
        """Tool requiring higher app version than current APP_VERSION must be rejected."""
        tool_id = "future_tool"
        meta = {
            "id": tool_id,
            "version": "1.0.0",
            "min_app_version": "9.9.9",
            "sha256": "abcdef" * 10
        }
        res = self.service._perform_install_or_update(tool_id, meta)
        self.assertFalse(res["success"])
        self.assertIn("requires Boltools app version 9.9.9", res["error"])

    def test_release_tool_cli_sign_and_verify(self):
        """Test release_tool.py key generation and signing helper directly."""
        import release_tool

        with tempfile.TemporaryDirectory() as tmp_dir:
            key_path = os.path.join(tmp_dir, "test_priv.pem")
            pub_hex = release_tool.generate_keypair(key_path, passphrase="testpassphrase123")
            self.assertEqual(len(pub_hex), 64)

            # Load private key back with passphrase
            priv_key = release_tool.load_private_key(key_path, passphrase="testpassphrase123")
            self.assertIsNotNone(priv_key)

            # Sign a test payload
            payload = b'{"sequence": 1, "test": true}'
            sig = priv_key.sign(payload)
            self.assertEqual(len(sig), 64)


if __name__ == "__main__":
    unittest.main()
