# Municipal Fee Crawler

This repository contains a simple Python-based crawler that extracts
hourly rate information for municipal services from publicly available
web pages. The focus is on gathering data for:

- Timtaxan för livsmedelskontroll
- Debiteringsmodell för livsmedelskontroll
- Timtaxan för bygglov

The extracted data is written to `municipal_fees.xlsx` for further
analysis.


## Installation

1. Create a virtual environment (optional but recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage


By default the crawler reads municipality URLs from `municipalities.csv`
and writes the results to `municipal_fees.xlsx`. You can run the crawler
directly:

```bash
python run_crawler.py
```

You can also specify files explicitly:

```bash
python -m crawler.crawler --input municipalities.csv --output out.xlsx
```

Add `--gui` to choose the files via Tkinter dialogs.

The Excel file will contain one row per municipality with the parsed
information.

## Testing

Run the unit tests with:


```bash
python -m unittest discover -s tests -v
```

## License


This project is released under the terms of the MIT License. See the
`LICENSE` file for details.


## Disclaimer

This is a proof-of-concept implementation. Real municipal websites may
have different structures that require custom scraping logic or parsing
rules. Always review the terms of service of the target websites and
ensure that scraping is allowed.

