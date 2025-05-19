import re
import csv
import json
import argparse
from pathlib import Path
from io import BytesIO

import requests
from bs4 import BeautifulSoup
import pandas as pd
from PyPDF2 import PdfReader

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None

class MunicipalCrawler:
    """Simple crawler to extract municipal fee information"""

    def __init__(self, municipality_urls):
        """
        Parameters
        ----------
        municipality_urls : dict
            Mapping of municipality name -> URL to start scraping
        """
        self.municipality_urls = municipality_urls

    @staticmethod
    def load_municipalities(path):
        path = Path(path)
        if path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        rows = {}
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows[row['municipality']] = row['url']
        return rows

    def fetch_page_text(self, url):
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text

    def fetch_pdf_text(self, url):
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        reader = PdfReader(BytesIO(resp.content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

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
        if url.lower().endswith('.pdf'):
            plain_text = self.fetch_pdf_text(url).lower()
        else:
            text = self.fetch_page_text(url)
            soup = BeautifulSoup(text, 'html.parser')
            plain_text = soup.get_text(separator=' ').lower()

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
                print(f"Failed to scrape {municipality}: {exc}")
                data = {
                    'food_control_hourly_rate': None,
                    'food_control_billing_model': None,
                    'building_permit_hourly_rate': None
                }
            data['municipality'] = municipality
            rows.append(data)
        return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Municipal fee crawler')
    parser.add_argument('--input', default='municipalities.csv', help='CSV or JSON file with municipality URLs')
    parser.add_argument('--output', default='municipal_fees.xlsx', help='Excel file to write results to')
    parser.add_argument('--gui', action='store_true', help='Use Tkinter dialogs to choose files')
    args = parser.parse_args(argv)

    if args.gui and filedialog:
        root = tk.Tk()
        root.withdraw()
        args.input = filedialog.askopenfilename(title='Municipality file', initialfile=args.input)
        args.output = filedialog.asksaveasfilename(title='Output Excel', initialfile=args.output)

    municipalities = MunicipalCrawler.load_municipalities(args.input)
    crawler = MunicipalCrawler(municipalities)
    df = crawler.run()
    df.to_excel(args.output, index=False)
    print(df)


if __name__ == '__main__':
    main()
