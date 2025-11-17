"""LTN search scraper with a simple CLI.

Usage examples:
  python scrape_ltn.py --keyword 川普 --pages 3 --start-date 2024-01-01 --end-date 2025-10-12

This script is a small refactor of the original procedural scraper to expose a
command-line interface for keyword, time range, page count and output file.
"""

import argparse
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup  # HTML Parser
from urllib.parse import urlencode, urljoin

# Defaults (kept for backward compatibility)
DEFAULT_KEYWORD = '川普'
DEFAULT_PAGES = 3
DEFAULT_OUTPUT = 'results.jsonl'
BASE = 'https://search.ltn.com.tw/list'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; simple-scraper/1.0; +https://example.com)'
}


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def read_keywords_file(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'Keywords file not found: {path}')
    kws: list[str] = []
    for line in p.read_text(encoding='utf-8').splitlines():
        s = line.strip()
        if s and not s.startswith('#'):
            kws.append(s)
    return kws


def parse_date_arg(value: str) -> str:
    """Accept several common date formats and return YYYYMMDD string.

    Raises argparse.ArgumentTypeError on invalid input.
    """
    for fmt in ('%Y%m%d', '%Y-%m-%d', '%Y/%m/%d'):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime('%Y%m%d')
        except ValueError:
            continue
    raise argparse.ArgumentTypeError("Invalid date format: %r. Use YYYYMMDD or YYYY-MM-DD." % value)


def fetch_article(url: str) -> str:
    """Fetch an article URL and extract main text under div.text.boxTitle.boxText.

    Returns the joined paragraph text (\n separated). Filters out likely ads and twitter content.
    """
    logging.debug('Fetching article content: %s', url)
    resp = _fetch_page(url)
    if resp is None:
        return ''
    soup = BeautifulSoup(resp.text, 'html.parser')

    container = soup.select_one('div.text.boxTitle.boxText')
    paragraphs: list[str] = []
    if not container:
        # Try fallback: any div with class that contains 'text' and 'boxText'
        for div in soup.select('div'):
            cls = div.get('class') or []
            if 'text' in cls and 'boxText' in cls:
                container = div
                break

    if not container:
        logging.debug('Article container not found for %s', url)
        return ''

    for p in container.select('p'):
        txt = p.get_text(separator=' ', strip=True)
        if not txt:
            continue
        # Heuristics: skip twitter embeds or tweets or obvious ads
        low = txt.lower()
        if 'twitter' in low or '推特' in low or '推文' in low:
            logging.debug('Skipping twitter-like paragraph')
            continue
        # Skip common ad markers (heuristic)
        if any(marker in low for marker in ('廣告', 'ad:', 'adsbygoogle', '更多精采', '延伸閱讀')):
            logging.debug('Skipping ad-like paragraph')
            continue
        paragraphs.append(txt)

    content = '\n'.join(paragraphs)
    return content


def _fetch_page(url: str, timeout: float = 15, max_retries: int = 3, backoff_factor: float = 0.6) -> requests.Response | None:
    """Fetch URL with retry/backoff using tenacity. Returns Response or None on final failure."""
    try:
        # Lazy import tenacity so it's optional at runtime until used
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=backoff_factor, min=backoff_factor, max=60),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _do_request(u: str):
            resp = requests.get(u, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp

        return _do_request(url)
    except Exception as e:
        logging.warning('Failed fetching %s after retries: %s', url, e)
        return None


def scrape(keyword: str, pages: int, start_time: str | None, end_time: str | None, output: str, *, workers: int = 1) -> int:
    """Run the scraping loop and write results to output.

    Returns the number of unique items written.
    """
    main_results = []
    seen_urls = set()

    logging.info("Scraping keyword: %s, pages: %d", keyword, pages)

    # Prepare page URLs
    page_urls: list[tuple[int, str]] = []
    for page in range(1, pages + 1):
        params = {
            'keyword': keyword,
            'sort': 'date',
            'type': 'all',
            'page': page,
        }
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        url = BASE + '?' + urlencode(params)
        page_urls.append((page, url))

    def parse_page_tuple(page_and_url: tuple[int, str]) -> list[dict]:
        page, url = page_and_url
        logging.debug('Fetching page %d: %s', page, url)
        resp = _fetch_page(url)
        if resp is None:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_results: list[dict] = []
        found = 0

        ul = soup.select_one('ul.list.boxTitle')
        if ul:
            for li in ul.select('li'):
                a = li.select_one('a.tit')
                if not a:
                    continue
                href = a.get('href')
                text = a.get_text(strip=True)
                if not href or not text:
                    continue
                full = urljoin(BASE, href)
                if full not in seen_urls:
                    # fetch article content lazily; we'll try to get content here
                    content = fetch_article(full)
                    page_results.append({'title': text, 'url': full, 'content': content})
                    seen_urls.add(full)
                    found += 1

        if found == 0:
            for a in soup.select('a.tit'):
                href = a.get('href')
                text = a.get_text(strip=True)
                if not href or not text:
                    continue
                full = urljoin(BASE, href)
                if full not in seen_urls:
                    content = fetch_article(full)
                    page_results.append({'title': text, 'url': full, 'content': content})
                    seen_urls.add(full)
                    found += 1

        logging.info('Found %d new items on page %d', found, page)
        # polite pause per page when using single-threaded mode
        if workers <= 1:
            time.sleep(0.8)
        return page_results

    if workers > 1:
        logging.info('Using %d worker threads for fetching', workers)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(parse_page_tuple, t): t for t in page_urls}
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    main_results.extend(res)
                except Exception as e:
                    logging.warning('Worker failed: %s', e)
    else:
        for tup in page_urls:
            res = parse_page_tuple(tup)
            main_results.extend(res)

    if main_results:
        print(f"\nTotal unique items found: {len(main_results)}")
    else:
        print(f"No items found across {pages} pages.")

    try:
        with open(output, 'w', encoding='utf-8') as f:
            for item in main_results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"\nSaved {len(main_results)} records to {output}")
    except Exception as e:
        print(f"Failed to write JSONL: {e}")

    return len(main_results)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Scrape LTN search results (simple).')
    p.add_argument('--keyword', '-k', default=DEFAULT_KEYWORD, help='Search keyword (default: %(default)s)')
    p.add_argument('--pages', '-p', type=int, default=DEFAULT_PAGES, help='Number of search result pages to fetch')
    p.add_argument('--start-date', type=parse_date_arg, default=None, help='Start date (YYYYMMDD or YYYY-MM-DD)')
    p.add_argument('--end-date', type=parse_date_arg, default=None, help='End date (YYYYMMDD or YYYY-MM-DD)')
    p.add_argument('--output', '-o', default=DEFAULT_OUTPUT, help='Output JSONL file path')
    p.add_argument('--keywords-file', '-K', default=None, help='Path to file with one keyword per line (batch mode)')
    p.add_argument('--workers', '-w', type=int, default=1, help='Number of worker threads for fetching pages (default 1)')
    p.add_argument('--debug', action='store_true', help='Enable debug logging')
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.pages < 1:
        parser.error('pages must be >= 1')

    setup_logging(bool(args.debug))

    keywords: list[str]
    if args.keywords_file:
        try:
            keywords = read_keywords_file(args.keywords_file)
        except Exception as e:
            parser.error(f'Failed to read keywords file: {e}')
        if not keywords:
            parser.error('Keywords file is empty or contains no valid lines')
    else:
        keywords = [args.keyword]

    # Run scrape for each keyword and merge results into a single output file
    aggregate_count = 0
    combined_results = []
    # When using batch keywords, keep seen set global to dedupe across keywords
    global_seen: set[str] = set()

    for kw in keywords:
        logging.info('Starting keyword: %s', kw)
        # Temporarily adjust behavior: scrape returns item count, but we need items
        # Reuse scrape() but it writes output at the end — instead, call internal logic by running scrape and reading file
        # Simpler: run scraping per keyword and append to combined_results by calling scrape with a temp output
        tmp_out = args.output + '.tmp'
        # Call scrape which will write the temporary file
        scrape(kw, args.pages, args.start_date, args.end_date, tmp_out, workers=args.workers)
        # Read tmp_out and append unique items
        try:
            with open(tmp_out, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue
                    url = item.get('url')
                    if not url:
                        continue
                    if url in global_seen:
                        continue
                    global_seen.add(url)
                    combined_results.append(item)
        except FileNotFoundError:
            logging.warning('Temporary output not found for keyword %s', kw)
        finally:
            # try to remove temp file if exists
            try:
                Path(tmp_out).unlink()
            except Exception:
                pass

    # Write combined results to final output
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            for item in combined_results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        logging.info('Saved %d records to %s', len(combined_results), args.output)
    except Exception as e:
        logging.error('Failed to write final output: %s', e)



if __name__ == '__main__':
    main()
