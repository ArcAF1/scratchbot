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


Prepare a mapping of municipality names to URLs in `municipalities.json`
(a sample file is provided). Then run the crawler via the command line:

```bash
python -m crawler.crawler --input municipalities.json --output fees.xlsx
```

You can also launch a small GUI to select files interactively:


```bash
python -m crawler.crawler --gui
```


The script writes the collected data to the specified Excel file.

## Tests

Basic tests use mocked network calls and PDF parsing so no internet
connection or external dependencies are required:


```bash
python -m unittest discover -s tests -v
```

## License


This project is licensed under the MIT License. See `LICENSE` for
details.

## Disclaimer

This is a proof-of-concept implementation. Real municipal websites may
have different structures that require custom scraping logic or parsing
rules. Always review the terms of service of the target websites and
ensure that scraping is allowed.

