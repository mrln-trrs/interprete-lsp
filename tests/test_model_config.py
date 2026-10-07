import unittest
from src.training.model_builder import validate_configuration


class TestModelConfiguration(unittest.TestCase):
    def test_schema_mismatch_is_rejected_before_native_import(self):
        for options in ({"input_shape": (30, 63)}, {"num_classes": 8}, {"num_classes": True},
                        {"recurrent": "transformer"}, {"dropout": float("nan")}, {"dropout": 1}):
            with self.assertRaises(ValueError):
                validate_configuration(**options)

    def test_supported_baselines(self):
        validate_configuration(recurrent="lstm")
        validate_configuration(recurrent="gru")
