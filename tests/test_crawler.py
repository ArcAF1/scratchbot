
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
    @patch('crawler.crawler.pd')
    @patch('crawler.crawler.requests')
    def test_html_parsing(self, mock_requests, mock_pd):
        mock_requests.get.return_value = DummyResp(text=SAMPLE_HTML)
        mock_pd.DataFrame.side_effect = lambda rows: DummyDF(rows)
        cr = crawler.MunicipalCrawler({'Test': 'http://example.com'})
        df = cr.run()
        row = df.iloc[0]
        self.assertEqual(row['food_control_hourly_rate'], 1200.0)
        self.assertEqual(row['food_control_billing_model'], 'efterhands')
        self.assertEqual(row['building_permit_hourly_rate'], 900.0)

    @patch('crawler.crawler.pd')
    @patch('crawler.crawler.PdfReader')
    @patch('crawler.crawler.requests')
    def test_pdf_parsing(self, mock_requests, mock_reader, mock_pd):
        mock_requests.get.return_value = DummyResp(content=b'pdfbytes')
        mock_reader.return_value.pages = [Mock(extract_text=lambda: SAMPLE_PDF_TEXT)]
        mock_pd.DataFrame.side_effect = lambda rows: DummyDF(rows)
        cr = crawler.MunicipalCrawler({'PDFTest': 'http://example.com/test.pdf'})
        df = cr.run()
        row = df.iloc[0]
        self.assertEqual(row['food_control_hourly_rate'], 1300.0)
        self.assertEqual(row['food_control_billing_model'], 'forskott')
        self.assertIsNone(row['building_permit_hourly_rate'])

    @patch('crawler.crawler.pd')
    @patch('crawler.crawler.PdfReader')
    @patch('crawler.crawler.requests')
    def test_pdf_link_in_html(self, mock_requests, mock_reader, mock_pd):
        html_with_link = '<html><body><a href="fees.pdf">Fees</a></body></html>'
        mock_requests.get.side_effect = [
            DummyResp(text=html_with_link),
            DummyResp(content=b'pdfbytes')
        ]
        mock_reader.return_value.pages = [Mock(extract_text=lambda: SAMPLE_PDF_TEXT)]
        mock_pd.DataFrame.side_effect = lambda rows: DummyDF(rows)
        cr = crawler.MunicipalCrawler({'LinkPDF': 'http://example.com'})
        df = cr.run()
        row = df.iloc[0]
        self.assertEqual(row['food_control_hourly_rate'], 1300.0)
        self.assertEqual(row['food_control_billing_model'], 'forskott')
        self.assertIsNone(row['building_permit_hourly_rate'])

if __name__ == '__main__':
    unittest.main()
