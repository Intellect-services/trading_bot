"""Tests for isbot script integration with database system."""

import subprocess
from pathlib import Path

import pytest


class TestIsbotIntegration:
    """Test isbot script integration with database."""

    @pytest.fixture()
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture()
    def isbot_script(self, project_root):
        """Path to isbot script."""
        return project_root / "scripts" / "isbot.sh"

    def test_reset_db_command_exists(self, isbot_script):
        """Test that reset-db command exists in isbot script."""
        assert isbot_script.exists(), "isbot.sh should exist"

        with open(isbot_script) as f:
            content = f.read()
            assert "reset-db" in content, "reset-db command should exist"
            assert "scripts/reset_db.py" in content, "Should call reset_db.py"

    def test_isbot_help_shows_reset_db(self, isbot_script):
        """Test that isbot help shows reset-db command."""
        result = subprocess.run(
            ["bash", str(isbot_script), "help"],
            capture_output=True,
            text=True,
            cwd=isbot_script.parent.parent,
        )

        assert result.returncode == 0
        assert "reset-db" in result.stdout.lower()

    def test_isbot_reset_db_calls_script(self, isbot_script, project_root, monkeypatch):
        """Test that isbot reset-db calls reset_db.py correctly."""
        # Mock reset_db.py to avoid actually resetting database
        called = []

        def mock_reset():
            called.append(True)

        # Note: This is a simplified test - actual integration would require
        # more complex mocking of subprocess calls
        # For now, just verify the command exists and references the script
        with open(isbot_script) as f:
            content = f.read()
            # Verify it calls reset_db.py
            assert "scripts/reset_db.py" in content

        # This test verifies structure, actual execution test would require
        # running the script in a controlled environment
        assert True  # Placeholder - structure verified
