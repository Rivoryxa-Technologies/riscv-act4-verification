# SPDX-License-Identifier: MIT
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def test_pins_are_full_hashes_and_https(self):
        pins=json.loads((ROOT/"pins.json").read_text())
        self.assertEqual(len(pins),4)
        for pin in pins.values():
            self.assertRegex(pin["commit"],r"^[0-9a-f]{40}$"); self.assertTrue(pin["url"].startswith("https://"))
    def test_missing_workspace_fails_setup(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/"run.py"),d],text=True,capture_output=True)
            self.assertEqual(p.returncode,2); self.assertIn("ERROR:",p.stdout)
if __name__=="__main__": unittest.main()
