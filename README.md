# Municipal Fee Crawler


This repository contains a Python-based crawler that extracts hourly rate information and billing models for municipal services. The crawler can read a list of municipal URLs, crawl HTML or PDF documents, and export the results to an Excel file.


## Installation

1. Create a virtual environment (optional but recommended)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

A sample mapping of municipalities to URLs is provided in `data/municipalities.json`.
You can run the crawler from the command line:

```bash
python -m crawler.crawler --input data/municipalities.json --output municipal_fees.xlsx
```

Add `--gui` to open a small window that lets you pick the input and output files interactively:

```bash
python -m crawler.crawler --gui
```

The resulting Excel file contains the scraped data for each municipality.

## Running Tests

The project uses the built-in `unittest` framework. Execute the test suite with:


```bash
python -m unittest discover -s tests -v
```

## License


This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Disclaimer

This is a proof-of-concept implementation. Real municipal websites may require custom scraping rules. Always review the terms of service of the target websites and ensure that scraping is allowed.

