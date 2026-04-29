# ArXiv Conference Paper Crawler

A Python-based crawler that searches and downloads academic papers from [arXiv.org](https://arxiv.org) by conference keywords (e.g., CVPR, NeurIPS, ICML), with a built-in year filter to skip papers published before a configurable threshold.

## Features

- **Multi-conference crawling** — Search papers by conference keywords in the Comments field
- **Year filtering** — Automatically skips papers whose Comments field indicates a year at or before the threshold (default: 2022)
- **Smart pagination** — Crawls through all search result pages; the advanced variant stops early once it encounters old papers (since arXiv sorts by newest first)
- **Retry & error handling** — Retries failed requests with exponential backoff (up to 3 retries)
- **CSV export** — Saves paper metadata (title, authors, abstract, submission date, links) to UTF-8 CSV files
- **Web UI** — Includes an HTML front-end for searching and filtering the collected papers

## Project Structure

```
arxiv/
├── Demo/
│   ├── base_search_Spider.py        # Basic crawler (simple search API)
│   ├── advanced_search_Spider.py    # Advanced crawler (stops on old papers)
│   ├── test01.py                    # Basic crawler (no page cap)
│   ├── search_papers.html           # Browser UI for browsing CSV results
│   └── arxiv_*_papers_after_2022.csv  # Sample crawled data
└── README.md
```

### Crawler Variants

| File | API Endpoint | Behavior |
|------|-------------|----------|
| `base_search_Spider.py` | `/search/?` | Uses simple search API. Has a `MAX_PAGES` cap (default 50). Skips individual old papers per-page. |
| `advanced_search_Spider.py` | `/search/advanced?` | Uses advanced search API. **Stops entirely** when it encounters a paper at or before the year threshold. |
| `test01.py` | `/search/?` | Same as base but without a maximum page limit — crawls all available pages. |

### Extracted Fields

Each paper entry includes:
- **Title** — Paper title
- **Authors** — Comma-separated author list
- **Abstract** — Full abstract text
- **Submitted** — Submission date string
- **Comments** — Comments field (used for year filtering)
- **Web link** — Link to the arXiv abstract page
- **PDF link** — Direct PDF download link

## Requirements

- Python 3.7+
- [requests](https://pypi.org/project/requests/)
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
- [pandas](https://pypi.org/project/pandas/)

Install dependencies:

```bash
pip install requests beautifulsoup4 pandas
```

## Usage

1. **Choose a crawler** — Pick the variant that suits your needs (see table above).

2. **Configure targets** — Edit the `targets` list in `main()`:

   ```python
   targets = [
       "CVPR", "ICCV", "ECCV",
       "ICLR", "NeurIPS", "ICML",
       "AAAI", "IJCAI", "WACV", "BMVC", "ACCV"
   ]
   ```

3. **Set year threshold** (optional) — Change `YEAR_THRESHOLD` at the top of the file:

   ```python
   YEAR_THRESHOLD = 2022  # Skip papers from 2022 and earlier
   ```

4. **Run the crawler:**

   ```bash
   python Demo/base_search_Spider.py
   ```

5. **Results** — CSV files are saved in the same directory as `arxiv_{CONFERENCE}_papers_after_{YEAR}.csv`.

## Web UI

Open `Demo/search_papers.html` in a browser to search and filter the crawled papers:

- **Search column** — Choose to search by Title, Abstract, or Authors
- **Keywords** — Comma-separated keywords (e.g., `ReID, VIReID`)
- **Conference filter** — Filter by a specific conference
- Results display title (linked to arXiv), authors, conference, submission date, abstract (expandable), and links

The UI uses [PapaParse](https://www.papaparse.com/) to load the CSV files client-side — no server needed.

## Notes

- arXiv rate-limits requests; the crawler includes a progressive delay (`1 + page_num * 0.1` seconds between pages) to be respectful.
- The year filter relies on the **Comments** field, which often contains publication year information for accepted papers.
- arXiv search results are sorted by announcement date (newest first), so the advanced crawler can safely stop once it reaches old papers.
- All crawled data is for research/educational purposes in compliance with arXiv's [terms of service](https://info.arxiv.org/help/api/tos.html).

## License

This project is for educational and research purposes only.
