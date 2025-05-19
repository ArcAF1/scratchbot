import unittest
from unittest.mock import patch

try:
    import pandas as pd
    import requests
    from crawler.crawler import MunicipalCrawler
except Exception:  # pragma: no cover - skip tests if deps missing
    MunicipalCrawler = None
    pd = None
    requests = None


@unittest.skipIf(MunicipalCrawler is None, "Required packages not available")
class TestMunicipalCrawler(unittest.TestCase):
    def test_parse_hourly_rate(self):
        crawler = MunicipalCrawler({})
        text = "Timtaxa för livsmedelskontroll är 1200 kronor"
        rate = crawler.parse_hourly_rate(text.lower(), r'timtaxa.*?livsmedelskontroll.*?(\d+[\,\.]?\d*)')
        self.assertEqual(rate, 1200.0)

    def test_parse_billing_model(self):
        crawler = MunicipalCrawler({})
        self.assertEqual(crawler.parse_billing_model('efterhandsdebitering'), 'efterhands')
        self.assertEqual(crawler.parse_billing_model('förhandsdebitering'), 'forskott')
        self.assertIsNone(crawler.parse_billing_model('annat'))

    @patch('crawler.crawler.requests.get')
    def test_run(self, mock_get):
        html = '<html><body>Timtaxa för livsmedelskontroll 1000</body></html>'
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = html
        municipalities = {'Town': 'http://example.com'}
        crawler = MunicipalCrawler(municipalities)
        df = crawler.run()
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, 'municipality'], 'Town')
        self.assertEqual(df.loc[0, 'food_control_hourly_rate'], 1000.0)

if __name__ == '__main__':
    unittest.main()
