
import argparse
import json
import logging
import os
import re
import io
import tkinter as tk
from tkinter import filedialog

try:
    import requests
except ImportError:  # pragma: no cover - fallback in restricted envs
    class _RequestsFallback:
        def __init__(self):
            from urllib.parse import urljoin
            self.compat = type('compat', (), {'urljoin': urljoin})

        def get(self, *a, **k):
            raise RuntimeError("requests not available")

    requests = _RequestsFallback()
try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    class _SimpleSoup:
        def __init__(self, text, parser):
            self.text = text

        def find_all(self, tag, href=False):
            return []

        def get_text(self, separator=' '):
            return self.text

    BeautifulSoup = _SimpleSoup
try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover
    class PdfReader:
        def __init__(self, *a, **k):
            self.pages = []

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    class _SimpleDF(list):
        def __init__(self, rows):
            super().__init__(rows)

        def to_excel(self, path, index=False):
            with open(path, 'w', encoding='utf-8') as fh:
                for row in self:
                    fh.write(str(row) + '\n')

        @property
        def loc(self):
            class _Loc:
                def __init__(self, data):
                    self.data = data

                def __getitem__(self, key):
                    row_idx, col = key
                    return list(self.data[row_idx].values())[list(self.data[row_idx].keys()).index(col)]

            return _Loc(self)

    pd = type('pd', (), {'DataFrame': _SimpleDF})

class MunicipalCrawler:
    """Simple crawler to extract municipal fee information."""


    def __init__(self, municipality_urls):
        """
        Parameters
        ----------
        municipality_urls : dict
            Mapping of municipality name -> URL to start scraping
        """
        self.municipality_urls = municipality_urls

        self.logger = logging.getLogger(self.__class__.__name__)

    def find_pdf_links(self, soup, base_url):
        """Return a list of absolute URLs to PDF files found in the page."""
        pdf_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf'):
                pdf_links.append(requests.compat.urljoin(base_url, href))
        return pdf_links

    def fetch_page_text(self, url):
        """Return text from a URL that may be HTML or PDF."""
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        if url.lower().endswith('.pdf'):
            return self._pdf_to_text(resp.content)
        return resp.text

    def _pdf_to_text(self, data):
        """Extract text from PDF bytes."""
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or '' for page in reader.pages]
        return '\n'.join(pages)

    def parse_hourly_rate(self, text, pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                return None
        return None

    def parse_billing_model(self, text):
        if re.search(r'efterhandsdebitering', text, re.IGNORECASE):
            return 'efterhands'
        if re.search(r'forhands|forskott', text, re.IGNORECASE):
            return 'forskott'
        return None

    def scrape_municipality(self, url):

        text = self.fetch_page_text(url)
        soup = BeautifulSoup(text, 'html.parser')
        plain_text = soup.get_text(separator=' ').lower()

        for pdf_url in self.find_pdf_links(soup, url):
            try:
                plain_text += '\n' + self.fetch_page_text(pdf_url).lower()
            except Exception as exc:  # pragma: no cover - network errors
                self.logger.warning("Failed to fetch PDF %s: %s", pdf_url, exc)

        data = {
            'food_control_hourly_rate': self.parse_hourly_rate(
                plain_text,
                r'timtaxa.*?livsmedelskontroll.*?(\d+[\,\.]?\d*)'
            ),
            'food_control_billing_model': self.parse_billing_model(plain_text),
            'building_permit_hourly_rate': self.parse_hourly_rate(
                plain_text,
                r'timtaxa.*?bygglov.*?(\d+[\,\.]?\d*)'
            )
        }
        return data

    def run(self):
        rows = []
        for municipality, url in self.municipality_urls.items():
            try:
                data = self.scrape_municipality(url)
            except Exception as exc:

                self.logger.error("Failed to scrape %s: %s", municipality, exc)

                data = {
                    'food_control_hourly_rate': None,
                    'food_control_billing_model': None,
                    'building_permit_hourly_rate': None
                }
            data['municipality'] = municipality
            rows.append(data)
        return pd.DataFrame(rows)



def parse_args():
    parser = argparse.ArgumentParser(description="Municipal fee crawler")
    parser.add_argument("--input", default="data/municipalities.json",
                        help="JSON file mapping municipality name to URL")
    parser.add_argument("--output", default="municipal_fees.xlsx",
                        help="Path to output Excel file")
    parser.add_argument("--gui", action="store_true",
                        help="Open a file dialog to select input/output")
    return parser.parse_args()


def gui_select_files():
    root = tk.Tk()
    root.withdraw()
    input_file = filedialog.askopenfilename(title="Municipalities JSON",
                                            filetypes=[("JSON", "*.json")])
    output_file = filedialog.asksaveasfilename(title="Output Excel",
                                               defaultextension=".xlsx",
                                               filetypes=[("Excel", "*.xlsx")])
    root.destroy()
    return input_file, output_file


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_args()

    input_path = args.input
    output_path = args.output
    if args.gui:
        sel_in, sel_out = gui_select_files()
        if sel_in:
            input_path = sel_in
        if sel_out:
            output_path = sel_out

    with open(input_path, "r", encoding="utf-8") as fh:
        municipalities = json.load(fh)

    crawler = MunicipalCrawler(municipalities)
    df = crawler.run()
    df.to_excel(output_path, index=False)

    print(df)


if __name__ == '__main__':
    main()
