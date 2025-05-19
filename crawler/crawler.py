
import argparse
import io
import json
import os
import re

try:
    import requests
except Exception:  # pragma: no cover - fallback for test env
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover - fallback for test env
    BeautifulSoup = None

try:
    import pandas as pd
except Exception:  # pragma: no cover - fallback for test env
    pd = None

try:
    from PyPDF2 import PdfReader
except Exception:  # pragma: no cover - fallback for test env
    PdfReader = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:  # pragma: no cover - fallback for test env
    tk = None

class MunicipalCrawler:
    """Simple crawler to extract municipal fee information"""

    def __init__(self, municipality_urls):
        """Initialize with a mapping of municipality names to URLs."""
        self.municipality_urls = municipality_urls

    def fetch_page_text(self, url):
        """Fetch text content from a URL. Handles both HTML and PDF."""
        if requests is None:
            raise RuntimeError("requests library is required to fetch URLs")

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        if url.lower().endswith('.pdf'):
            if PdfReader is None:
                raise RuntimeError("PyPDF2 is required for PDF parsing")
            reader = PdfReader(io.BytesIO(resp.content))
            pages = [p.extract_text() or '' for p in reader.pages]
            return '\n'.join(pages)
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

        """Return parsed data for a single municipality URL."""
        text = self.fetch_page_text(url)

        plain_text = text.lower()

        if not url.lower().endswith('.pdf'):
            pdf_url = None
            if BeautifulSoup is not None:
                soup = BeautifulSoup(text, 'html.parser')
                tag = soup.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                if tag and tag.get('href'):
                    pdf_url = tag['href']
                    if requests is not None:
                        pdf_url = requests.compat.urljoin(url, pdf_url)
                    text = self.fetch_page_text(pdf_url)
                    plain_text = text.lower()
                else:
                    plain_text = soup.get_text(separator=' ').lower()
            else:
                m = re.search(r'href=[\"\']([^\"\']+\.pdf)[\"\']', text, re.IGNORECASE)
                if m:
                    pdf_url = m.group(1)
                    if requests is not None:
                        pdf_url = requests.compat.urljoin(url, pdf_url)
                    text = self.fetch_page_text(pdf_url)
                    plain_text = text.lower()

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
            raise RuntimeError('pandas is required to create DataFrame')

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


def load_municipalities(path):
    """Load municipality mapping from a JSON or CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    if path.lower().endswith('.json'):
        with open(path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    mapping = {}
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                mapping[parts[0]] = parts[1]
    return mapping


def run_gui(args):
    if tk is None:
        raise RuntimeError('tkinter is required for GUI')

    root = tk.Tk()
    root.title('Municipal Crawler')

    input_var = tk.StringVar(value=args.input)
    output_var = tk.StringVar(value=args.output)

    def browse_input():
        filename = filedialog.askopenfilename()
        if filename:
            input_var.set(filename)

    def browse_output():
        filename = filedialog.asksaveasfilename(defaultextension='.xlsx')
        if filename:
            output_var.set(filename)

    def run_crawl():
        try:
            municipalities = load_municipalities(input_var.get())
            crawler = MunicipalCrawler(municipalities)
            df = crawler.run()
            df.to_excel(output_var.get(), index=False)
            messagebox.showinfo('Done', 'Crawling finished')
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    tk.Label(root, text='Municipality file:').grid(row=0, column=0, sticky='w')
    tk.Entry(root, textvariable=input_var, width=40).grid(row=0, column=1)
    tk.Button(root, text='Browse', command=browse_input).grid(row=0, column=2)

    tk.Label(root, text='Output Excel:').grid(row=1, column=0, sticky='w')
    tk.Entry(root, textvariable=output_var, width=40).grid(row=1, column=1)
    tk.Button(root, text='Browse', command=browse_output).grid(row=1, column=2)

    tk.Button(root, text='Run', command=run_crawl).grid(row=2, column=1)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Municipal fee crawler")
    parser.add_argument(
        '--input',
        default='municipalities.csv',
        help='JSON or CSV file with municipality URL mapping'
    )
    parser.add_argument('--output', default='municipal_fees.xlsx',
                        help='Excel file to write results to')
    parser.add_argument('--gui', action='store_true',
                        help='Launch simple Tkinter GUI')
    args = parser.parse_args()

    if args.gui:
        run_gui(args)
        return

    municipalities = load_municipalities(args.input)
    crawler = MunicipalCrawler(municipalities)
    df = crawler.run()
    if pd is None:
        raise RuntimeError('pandas is required to save Excel output')
    df.to_excel(args.output, index=False)
    print(df)


if __name__ == '__main__':
    main()
