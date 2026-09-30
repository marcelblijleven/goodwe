from unittest import TestCase

from goodwe.model import (
    SINGLE_PHASE_MODELS,
    is_2_battery,
    is_3_mppt,
    is_4_mppt,
    is_single_phase,
)


class ModelMock:
    """Minimal stand-in exposing only the attributes model.py inspects."""

    def __init__(self, serial_number, model_name):
        self.serial_number = serial_number
        self.model_name = model_name


class TestSinglePhase(TestCase):
    def test_dns_g40_with_unmatched_serial_is_single_phase(self):
        # A DNS-G40 reporting a serial that carries none of the known tags.
        inverter = ModelMock("55000NBA263L1473", "GW5K-DNS-G40")
        self.assertTrue(is_single_phase(inverter))

    def test_dns_g43_is_single_phase(self):
        inverter = ModelMock("55000NBA263L1474", "GW6K-DNS-G43")
        self.assertTrue(is_single_phase(inverter))

    def test_serial_match_still_works(self):
        for tag in SINGLE_PHASE_MODELS:
            inverter = ModelMock("2107PT%s7DFM0083" % tag, "GW5K-UNKNOWN")
            self.assertTrue(is_single_phase(inverter), tag)

    def test_three_phase_models_are_still_three_phase(self):
        for serial, model in (
            ("2107PTFE7DFM0083", "GW5K-DT"),
            ("1234DTU5678ABCD", "GW10K-DTU"),
            ("1234DTN5678ABCD", "GW10K-DTN"),
            ("1234KMT5678ABCD", "GW10K-KMT"),
            ("1234DTB5678ABCD", "GW10K-DTB"),
            ("1234DTN5678ABCD", "GW50K-DTN"),
        ):
            inverter = ModelMock(serial, model)
            self.assertFalse(is_single_phase(inverter), model)

    def test_missing_model_name_does_not_raise(self):
        inverter = ModelMock("1234DSN5678ABCD", None)
        self.assertTrue(is_single_phase(inverter))


class TestOtherModelHelpersUnaffected(TestCase):
    """The allowlist must not disturb the MPPT or battery helpers."""

    def test_3_mppt_unchanged(self):
        self.assertTrue(is_3_mppt(ModelMock("2107MSU7DFM0083", "GW8K-MSU")))
        self.assertFalse(is_3_mppt(ModelMock("2107PTFE7DFM0083", "GW5K-DT")))

    def test_4_mppt_unchanged(self):
        self.assertTrue(is_4_mppt(ModelMock("1234KMT5678ABCD", "GW10K-KMT")))
        self.assertFalse(is_4_mppt(ModelMock("1234DSN5678ABCD", "GW5K-DSN")))

    def test_2_battery_unchanged(self):
        self.assertTrue(is_2_battery(ModelMock("210725KET7DFM0083", "GW25K-ET")))
        self.assertFalse(is_2_battery(ModelMock("2107PTFE7DFM0083", "GW5K-ET")))
