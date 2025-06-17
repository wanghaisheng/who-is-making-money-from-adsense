import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import time
import os
from datetime import datetime

QUERY = 'intext:"ca-pub-"'
BASE_URL = 'https://www.google.com/search'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/114.0.0.0 Safari/537.36'
}
RESULTS_DIR = 'results'
MAX_PAGES = 5  # How many pages to fetch, each page ~10 results
WAIT_BETWEEN_REQUESTS = 5  # seconds

def get_search_results(query, start=0):
    params = {
        'q': query,
        'hl': 'en',
        'start': start,
        'tbs': 'qdr:h',  # last hour
    }
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch page starting at {start}. Status code: {response.status_code}")
        return None
    return response.text

def parse_domains(html):
    soup = BeautifulSoup(html, 'html.parser')
    domains = set()
    # Google search results links are in <a> tags inside <div class="yuRUbf">
    for div in soup.find_all('div', class_='yuRUbf'):
        a = div.find('a', href=True)
        if a:
            url = a['href']
            domain = urlparse(url).netloc
            # Remove www prefix if any
            if domain.startswith('www.'):
                domain = domain[4:]
            domains.add(domain)
    return domains

def save_domains(domains, date_str):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = os.path.join(RESULTS_DIR, f'{date_str}.txt')
    with open(filename, 'a') as f:
        for d in sorted(domains):
            f.write(d + '\n')
    print(f"Saved {len(domains)} domains to {filename}")

def main():
    all_domains = set()
    date_str = datetime.now().strftime('%Y-%m-%d')

    for page in range(MAX_PAGES):
        start = page * 10
        print(f"Fetching results page {page+1} (start={start}) ...")
        html = get_search_results(QUERY, start)
        if not html:
            break
        domains = parse_domains(html)
        print(f"Found {len(domains)} domains on page {page+1}")
        all_domains.update(domains)
        time.sleep(WAIT_BETWEEN_REQUESTS)

    if all_domains:
        save_domains(all_domains, date_str)
    else:
        print("No domains found.")

if __name__ == '__main__':
    main()
