import re
try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    requests = None

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    BeautifulSoup = None

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    pd = None

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

    def fetch_page_text(self, url):
        if requests is None:
            raise ImportError("requests package is required to fetch pages")
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text

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
        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 package is required")
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
        if pd is None:
            raise ImportError("pandas package is required")
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
    import argparse

    parser = argparse.ArgumentParser(description="Municipal fee crawler")
    parser.add_argument("--input", help="JSON or CSV file with municipality URL mapping")
    parser.add_argument(
        "--output", default="municipal_fees.xlsx", help="Excel file to write results to"
    )
    parser.add_argument("--gui", action="store_true", help="Run with simple Tkinter file chooser")
    args = parser.parse_args(argv)

    if args.gui:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()

        if not args.input:
            args.input = filedialog.askopenfilename(title="Municipality mapping")
        args.output = filedialog.asksaveasfilename(
            title="Output Excel", defaultextension=".xlsx"
        ) or args.output

    municipalities = {
        "ExampleTown": "https://example.com/municipality/exampletown/fees"
    }

    if args.input:
        import json, csv, os

        ext = os.path.splitext(args.input)[1].lower()
        with open(args.input, "r", encoding="utf-8") as fh:
            if ext == ".json":
                municipalities = json.load(fh)
            elif ext == ".csv":
                municipalities = {
                    row[0]: row[1] for row in csv.reader(fh) if len(row) >= 2
                }
            else:
                raise ValueError("Unsupported input format: %s" % ext)

    crawler = MunicipalCrawler(municipalities)
    df = crawler.run()
    df.to_excel(args.output, index=False)
    print(df)


if __name__ == '__main__':
    main()
