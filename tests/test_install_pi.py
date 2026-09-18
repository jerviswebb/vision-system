import subprocess
import unittest
from pathlib import Path


class InstallPiTests(unittest.TestCase):
    def test_installer_is_complete_and_profile_configurable(self):
        repo_root = Path(__file__).resolve().parent.parent
        installer_path = repo_root / "deploy" / "install_pi.sh"
        installer = installer_path.read_text(encoding="utf-8")
        service = (repo_root / "deploy" / "vision.service").read_text(
            encoding="utf-8"
        )
        syntax = subprocess.run(
            ["bash", "-n", str(installer_path)], text=True, capture_output=True
        )

        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        self.assertEqual(syntax.stderr, "")
        self.assertIn("\nPY\n\nmkdir -p", installer)
        self.assertIn(
            'MODEL_PROFILE="${VISION_MODEL_PROFILE:-yellow_daifuku}"', installer
        )
        self.assertIn(
            "Environment=VISION_MODEL_PROFILE=$MODEL_PROFILE", installer
        )
        self.assertNotIn("--profile yellow_daifuku", installer)
        self.assertIn(
            "Environment=VISION_MODEL_PROFILE=yellow_daifuku", service
        )
        self.assertNotIn("--profile yellow_daifuku", service)


if __name__ == "__main__":
    unittest.main()
