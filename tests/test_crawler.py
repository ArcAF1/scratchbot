import types
import unittest
from unittest.mock import patch, MagicMock

from crawler.crawler import MunicipalCrawler


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.crawler = MunicipalCrawler({})

    def test_parse_hourly_rate(self):
        text = "Timtaxa f\u00f6r livsmedelskontroll \u00e4r 1200 kronor".lower()
        rate = self.crawler.parse_hourly_rate(text, r"timtaxa.*?livsmedelskontroll.*?(\d+[\,\.]?\d*)")
        self.assertEqual(rate, 1200.0)

    def test_parse_billing_model(self):
        text = "Vi till\u00e4mpar efterhandsdebitering.".lower()
        model = self.crawler.parse_billing_model(text)
        self.assertEqual(model, "efterhands")


class RunTests(unittest.TestCase):
    def test_run_with_patched_dependencies(self):
        html = "<html>Timtaxa f\u00f6r livsmedelskontroll 1000</html>"
        mock_df = MagicMock(name="DataFrame")

        with patch('crawler.crawler.requests') as mock_requests, \
             patch('crawler.crawler.BeautifulSoup') as mock_bs, \
             patch('crawler.crawler.pd') as mock_pd:

            mock_resp = MagicMock()
            mock_resp.text = html
            mock_resp.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_resp

            mock_soup = MagicMock()
            mock_soup.get_text.return_value = html
            mock_bs.return_value = mock_soup

            mock_pd.DataFrame.return_value = mock_df

            crawler = MunicipalCrawler({'Town': 'http://example.com'})
            result = crawler.run()
            self.assertIs(result, mock_df)

