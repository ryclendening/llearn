from __future__ import annotations

import unittest
from unittest.mock import patch

from auth import config
from auth.service import _token_hash


class AuthSecurityTests(unittest.TestCase):
    def test_session_tokens_are_hashed(self):
        self.assertEqual(len(_token_hash("secret-token")), 64)
        self.assertNotIn("secret-token", _token_hash("secret-token"))

    def test_production_rejects_development_auth_features(self):
        with patch.object(config, "APP_ENV", "production"), patch.object(config, "AUTH_DEV_BYPASS", True):
            with self.assertRaises(RuntimeError):
                config.validate_auth_config()

    def test_production_rejects_default_state_secret(self):
        with (
            patch.object(config, "APP_ENV", "production"),
            patch.object(config, "AUTH_DEV_BYPASS", False),
            patch.object(config, "AUTH_DEV_AUTO_APPROVE_TEACHERS", False),
            patch.object(config, "AUTH_STATE_SECRET", "development-only-change-me"),
        ):
            with self.assertRaises(RuntimeError):
                config.validate_auth_config()


if __name__ == "__main__":
    unittest.main()
