import os
import tempfile
import unittest
from pathlib import Path

class ProjectFilesTest(unittest.TestCase):
    def test_required_files_exist(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "bot.py").exists())
        self.assertTrue((root / "requirements.txt").exists())
        self.assertFalse((root / ".env").exists())
        self.assertFalse((root / ".env.example").exists())

if __name__ == "__main__":
    unittest.main()
