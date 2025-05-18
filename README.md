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

You can run the crawler from the command line. Provide a JSON or CSV
file mapping municipality names to URLs, and specify an output Excel
file:

```bash
python -m crawler.crawler --input municipalities.json --output result.xlsx
```

If you prefer a graphical interface for choosing files, pass `--gui` and
a simple Tkinter dialog will let you select the input and output
locations.

## Testing

Run the unit tests using the built-in `unittest` module:

```bash
python -m unittest discover -s tests -v
```

## License

This project is released under the terms of the MIT license. See the
`LICENSE` file for details.

## Disclaimer

This is a proof-of-concept implementation. Real municipal websites may
have different structures that require custom scraping logic or parsing
rules. Always review the terms of service of the target websites and
ensure that scraping is allowed.
