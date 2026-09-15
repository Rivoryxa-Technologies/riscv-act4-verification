import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('historical_runner',Path(__file__).resolve().parents[1]/'historical/run.py')
historical=importlib.util.module_from_spec(spec);spec.loader.exec_module(historical)

class HistoricalVerdicts(unittest.TestCase):
    def test_correct_result(self):
        self.assertTrue(historical.accepted('after','low_write_at_carry',0,'HISTORICAL_PASS case=low_write_at_carry',False))
    def test_expected_historical_failure(self):
        self.assertTrue(historical.accepted('before','low_write_at_carry',-6,'LOW_WRITE_CARRY_FAILED expected=20 actual=100000020',False))
    def test_timeout_rejected(self):
        self.assertFalse(historical.accepted('before','low_write_at_carry',-9,'LOW_WRITE_CARRY_FAILED',True))
    def test_unrelated_or_missing_failure_rejected(self):
        for log in ('','WATCHDOG_FAILED','HIGH_WRITE_HOLD_FAILED','LOW_WRITE_CARRY_FAILED BUS_HANDSHAKE_FAILED'):
            self.assertFalse(historical.accepted('before','low_write_at_carry',-6,log,False))
    def test_pass_and_failure_conflict(self):
        self.assertFalse(historical.accepted('before','low_write_at_carry',-6,'LOW_WRITE_CARRY_FAILED HISTORICAL_PASS',False))
    def test_execution_error_rejected(self):
        self.assertFalse(historical.accepted('before','low_write_at_carry',127,'LOW_WRITE_CARRY_FAILED',False))
    def test_duplicate_pass_rejected(self):
        self.assertFalse(historical.accepted('after','smoke',0,'HISTORICAL_PASS case=smoke\nHISTORICAL_PASS case=smoke',False))
    def test_normal_cases_must_pass_before(self):
        self.assertFalse(historical.accepted('before','smoke',1,'SMOKE_FAILED',False))
