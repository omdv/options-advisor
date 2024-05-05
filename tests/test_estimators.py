"""
Unit tests for the estimators module.
"""

import unittest
import yfinance as yf
from volatility.estimators import VolatilityEstimator, multi_window_estimates

ESTIMATORS = [
    "close_to_close",
    "parkinson",
    "garman_klass",
    "rogers_satchell",
    "yang_zhang",
]

class TestEstimators(unittest.TestCase):
    """
    Main method
    testing on H1, 2023 spx data
    """
    def setUp(self):
        spx = yf.Ticker("^SPX")
        self.quotes = spx.history(
            start="2023-01-01",
            end="2023-06-01")
        self.ens = VolatilityEstimator(estimators=ESTIMATORS)
        self.windows = (30, 60, 90)

    def test_estimate(self):
        """
        Test the estimate method
        """
        result = self.ens.estimate(self.quotes, window=20, components=False)
        self.assertEqual(
            result.xs((20, 'mean'), level=['Window', 'Estimator'], axis=1).iloc[-1].values[0],
            0.1048614127148697)
        self.assertEqual(result.shape, (83, 1))

        result = self.ens.estimate(self.quotes, window=20, components=True, clean=False)
        self.assertEqual(result.shape, (103, 6))



    def test_multi_window_estimates(self):
        """
        Test components
        """
        result = multi_window_estimates(
            self.ens,
            self.quotes,
            windows=self.windows,
            components=True)
        self.assertEqual(
            result.xs((60, 'mean'), level=['Window', 'Estimator'], axis=1).iloc[-1].values[0],
            0.12725502562574045)

if __name__ == "__main__":
    unittest.main()
