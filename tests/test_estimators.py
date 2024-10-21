"""
Unit tests for the estimators module.
"""

import os
import unittest
from api_quotes import get_historical_quotes
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
        self.config = {}
        self.config['quotes_api_key'] = os.environ.get('QUOTES_API_KEY')
        spx = get_historical_quotes(
            self.config,
            '^SPX',
            start_date = "2023-01-01",
            end_date = "2023-06-01")
        self.quotes = spx
        self.ens = VolatilityEstimator(estimators=ESTIMATORS)
        self.windows = (30, 60, 90)

    def test_estimate(self):
        """
        Test the estimate method
        """
        result = self.ens.estimate(self.quotes, window=20, components=False)
        self.assertEqual(
            result.xs((20, 'mean'), level=['Window', 'Estimator'], axis=1).iloc[-1].values[0],
            0.1042617700348037)
        self.assertEqual(result.shape, (84, 1))

        result = self.ens.estimate(self.quotes, window=20, components=True, clean=False)
        self.assertEqual(result.shape, (104, 6))



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
            0.1267885190493656)

if __name__ == "__main__":
    unittest.main()
