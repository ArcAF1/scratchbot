
import unittest
from unittest.mock import patch, Mock

from crawler import crawler

class DummyDF:
    def __init__(self, rows):
        self.rows = rows

    def to_excel(self, path, index=False):
        pass

    @property
    def iloc(self):
        class ILoc:
            def __init__(self, rows):
                self.rows = rows

            def __getitem__(self, idx):
                return self.rows[idx]

        return ILoc(self.rows)

SAMPLE_HTML = """
<html><body>
<p>Timtaxa för livsmedelskontroll är 1200 kr.</p>
<p>Vi använder efterhandsdebitering.</p>
<p>Timtaxa för bygglov är 900 kr.</p>
</body></html>
"""

SAMPLE_PDF_TEXT = "Timtaxa för livsmedelskontroll 1300 kr. Forskottsdebitering."

class DummyResp:
    def __init__(self, text='', content=b''):
        self.text = text
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        pass

class CrawlerTests(unittest.TestCase):
    def setUp(self):
        self.crawler = crawler.MunicipalCrawler({})

    def test_parse_hourly_rate(self):
        self.assertEqual(
            self.crawler.parse_hourly_rate('Timtaxa 1200 kr', r'(\d+[\,\.]?\d*)'),
            1200.0,
        )
        self.assertEqual(
            self.crawler.parse_hourly_rate('Timtaxa 900,5 kr', r'(\d+[\,\.]?\d*)'),
            900.5,
        )
        self.assertIsNone(
            self.crawler.parse_hourly_rate('Ingen taxa', r'(\d+[\,\.]?\d*)')
        )

    def test_parse_billing_model(self):
        self.assertEqual(
            self.crawler.parse_billing_model('Vi använder efterhandsdebitering.'),
            'efterhands',
        )
        self.assertEqual(
            self.crawler.parse_billing_model('Forskottsdebitering tillämpas.'),
            'forskott',
        )
        self.assertIsNone(
            self.crawler.parse_billing_model('Okänt system.')
        )

    @patch('crawler.crawler.pd')
    @patch('crawler.crawler.PdfReader')
    @patch('crawler.crawler.requests.get')
    @patch('crawler.crawler.requests')
    def test_overall_crawl(self, mock_requests, mock_get, mock_reader, mock_pd):
        def fake_get(url, timeout=10):
            if url.endswith('.pdf'):
                return DummyResp(content=b'pdfbytes')
            return DummyResp(text=SAMPLE_HTML)

        mock_get.side_effect = fake_get
        mock_reader.return_value.pages = [Mock(extract_text=lambda: SAMPLE_PDF_TEXT)]
        mock_pd.DataFrame.side_effect = lambda rows: DummyDF(rows)

        urls = {
            'HTMLTown': 'http://example.com/html',
            'PDFTown': 'http://example.com/file.pdf',
        }
        cr = crawler.MunicipalCrawler(urls)
        df = cr.run()
        row_html = df.iloc[0]
        row_pdf = df.iloc[1]

        self.assertEqual(row_html['food_control_hourly_rate'], 1200.0)
        self.assertEqual(row_html['food_control_billing_model'], 'efterhands')
        self.assertEqual(row_html['building_permit_hourly_rate'], 900.0)

        self.assertEqual(row_pdf['food_control_hourly_rate'], 1300.0)
        self.assertEqual(row_pdf['food_control_billing_model'], 'forskott')
        self.assertIsNone(row_pdf['building_permit_hourly_rate'])

if __name__ == '__main__':
    unittest.main()
