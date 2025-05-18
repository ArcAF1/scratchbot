
import unittest
from unittest.mock import patch, Mock

from crawler.crawler import MunicipalCrawler

HTML_PAGE = """
<html><body>
<p>Timtaxa f\xc3\xb6r livsmedelskontroll 1200 kronor</p>
<p>Efterhandsdebitering</p>
<a href='fees.pdf'>Fees</a>
</body></html>
"""

PDF_TEXT = "Timtaxa f\xc3\xb6r bygglov 800"

class CrawlerTests(unittest.TestCase):
    @patch('crawler.crawler.MunicipalCrawler._pdf_to_text', return_value=PDF_TEXT)
    @patch('crawler.crawler.requests.get')
    @patch('crawler.crawler.BeautifulSoup')
    def test_scrape_with_pdf(self, mock_bs, mock_get, mock_pdf):
        class FakeSoup:
            def __init__(self, text, parser):
                self.text = text

            def find_all(self, tag, href=False):
                return [{'href': 'fees.pdf'}]

            def get_text(self, separator=' '):
                return self.text

        mock_bs.side_effect = FakeSoup
        html_resp = Mock(status_code=200, text=HTML_PAGE)
        pdf_resp = Mock(status_code=200, content=b'dummy')
        mock_get.side_effect = [html_resp, pdf_resp]

        crawler = MunicipalCrawler({'Town': 'http://example.com'})
        df = crawler.run()
        self.assertEqual(df.loc[0, 'food_control_hourly_rate'], 1200.0)
        self.assertEqual(df.loc[0, 'food_control_billing_model'], 'efterhands')
        self.assertEqual(df.loc[0, 'building_permit_hourly_rate'], 800.0)

if __name__ == '__main__':
    unittest.main()

