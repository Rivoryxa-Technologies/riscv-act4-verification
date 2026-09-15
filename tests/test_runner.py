# SPDX-License-Identifier: MIT
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); import run
class Tests(unittest.TestCase):
    def test_pins_are_full_hashes_and_https(self):
        pins=json.loads((ROOT/"pins.json").read_text())
        repos=[v for v in pins.values() if isinstance(v,dict) and "commit" in v]
        self.assertEqual(len(repos),4)
        for pin in repos:
            self.assertRegex(pin["commit"],r"^[0-9a-f]{40}$"); self.assertTrue(pin["url"].startswith("https://"))
    def test_missing_workspace_fails_setup(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/"run.py"),d],text=True,capture_output=True)
            self.assertEqual(p.returncode,2); self.assertIn("ERROR:",p.stdout)
    def test_result_requires_one_unambiguous_pass(self):
        self.assertTrue(run.case_pass(0,False,["PASSED"]))
        self.assertFalse(run.case_pass(0,False,["PASSED","FAILED"]))
        self.assertFalse(run.case_pass(0,False,["PASSED","PASSED"]))
        self.assertFalse(run.case_pass(1,False,["PASSED"]))
        self.assertFalse(run.case_pass(0,True,["PASSED"]))
    def test_manifest_rejects_missing_duplicate_and_extra(self):
        names=list(run.EXPECTED_NAMES); self.assertTrue(run.manifest_matches(names))
        self.assertFalse(run.manifest_matches(names[:-1]))
        self.assertFalse(run.manifest_matches(names[:-1]+[names[0]]))
        self.assertFalse(run.manifest_matches(names+["extra.elf"]))
    def test_timeout_kills_simulation(self):
        code,text,timed=run.run_sim([sys.executable,"-c","import time; print('started',flush=True); time.sleep(2)"],ROOT,0.05)
        self.assertNotEqual(code,0); self.assertTrue(timed); self.assertIn("started",text); self.assertIn("TIMEOUT",text)
    def test_source_diff_hash_rejects_wrong_source(self):
        pins={"integration_diff_sha256":run.hashlib.sha256(b"allowed").hexdigest()}
        self.assertTrue(run.integration_diff_matches(b"allowed",pins))
        self.assertFalse(run.integration_diff_matches(b"changed",pins))
    def test_hex_is_regenerated_from_elf(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); elf=d/"x.elf"; hexfile=d/"x.hex"; elf.write_bytes(b"fresh"); hexfile.write_bytes(b"stale")
            tool=d/"objcopy"; tool.write_text("#!/bin/sh\ncp \"$3\" \"$4\"\n"); tool.chmod(0o755)
            run.regenerate_hex(str(tool),elf,hexfile,1)
            self.assertEqual(hexfile.read_bytes(),b"fresh")
if __name__=="__main__": unittest.main()
