# AWS SBCL Scraper

A local Python scraper for collecting **public AWS Builder Center profile data** for SBCL workflows.

The project is designed to keep scraped data and exports on your local machine. It does not attempt to access private account information or infer private email addresses.

## Requirements

- Python 3.11 or newer
- Git

## 1. Clone the repository

```bash
git clone https://github.com/C0dEr8627/aws-sbcl.git
cd aws-sbcl
```

## 2. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install the project

Install the package in editable mode together with the test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

The project uses `httpx`, `beautifulsoup4`, `typer`, and `openpyxl` for HTTP access, HTML parsing, the local CLI, and XLSX export respectively.

## 4. Verify the installation

Run the test suite:

```bash
pytest
```

You can also verify that the CLI entry point is available:

```bash
sbcl-scraper --help
```

> The CLI is being built incrementally. Commands are added as the scraper workflow is implemented.

## Project structure

```text
aws-sbcl/
├── docs/                 # Architecture and data-source documentation
├── src/
│   └── sbcl_scraper/    # Scraper package
│       ├── client.py    # Builder Center HTTP client
│       ├── discovery.py # Profile candidate discovery
│       ├── export.py    # CSV/XLSX exports
│       ├── filtering.py # Target-profile filtering
│       ├── models.py    # Normalized Builder model
│       ├── profile.py   # Profile workflow
│       ├── profile_parser.py
│       ├── store.py     # Local SQLite storage
│       └── workflow.py  # Scrape and normalization workflow
├── tests/               # Automated tests
├── data/                # Local SQLite data (ignored by Git)
├── exports/             # Local CSV/XLSX exports (ignored by Git)
└── pyproject.toml       # Project configuration and dependencies
```

## Target profile criteria

A Builder profile is considered a target when all three conditions are true:

```text
Public profile location ends with "India"
Followers = 0
Following = 0
```

The Indian status is determined only from the profile's publicly displayed location. Names and aliases are not used to infer location.

## Data handling

The scraper works with publicly available Builder Center profile information such as:

- Alias
- Display name
- Public location
- Followers
- Following
- Public email, only when explicitly exposed by the profile
- Profile URL
- Scrape timestamp

No private email scraping or email inference is performed.

## Exports

The supported export formats are:

- CSV
- XLSX

JSON export is intentionally not part of the current workflow.

## Local storage

Scraped normalized profiles are stored in a local SQLite database. Local database files, generated exports, logs, virtual environments, and browser/authentication state are excluded from Git through `.gitignore`.

## Development

After activating the virtual environment, run:

```bash
pytest
```

Keep implementation changes on the `main` branch for this project.

## Documentation

See the `docs/` directory for:

- Builder Center public data-source notes
- System architecture
- Development phases and implementation plan
