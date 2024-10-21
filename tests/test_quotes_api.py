"""
Unit tests for the quotes api module.
"""

import os
import unittest
from api_quotes import get_historical_quotes

class TestAPIs(unittest.TestCase):
    """
    Main method
    """

    def setUp(self):
        self.config = {}
        self.config['quotes_api_key'] = os.environ.get('QUOTES_API_KEY')

    def test_historical_quotes(self):
        """
        Test historical quotes
        """
        result = get_historical_quotes(
            self.config,
            '^SPX',
            start_date="2023-01-01",
            end_date="2023-06-01"
        )
        self.assertEqual(result.loc["2023-01-04", "open"], 3840.36011)
        self.assertEqual(result.loc["2023-05-18", "close"], 4198.0498)
        self.assertEqual(result.shape, (104, 11))

if __name__ == "__main__":
    unittest.main()
