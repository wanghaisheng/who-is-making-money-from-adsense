import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import os
from datetime import datetime

# List of target domains you want to track
TARGET_DOMAINS = [
    "ko-fi.com",
    "patreon.com",
    "buymeacoffee.com"
]

BASE_URL = 'https://www.google.com/search'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/114.0.0.0 Safari/537.36'
}
RESULTS_DIR = 'results'
MAX_PAGES = 5
WAIT_BETWEEN_REQUESTS = 5
TOP_DOMAINS_FILE = 'top_1m_domains.csv'  # Your top 1M domain list CSV

def get_search_results(query, start=0):
    params = {
        'q': query,
        'hl': 'en',
        'start': start,
        'tbs': 'qdr:h',  # filter by last hour
    }
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch page at start={start}: {response.status_code}")
        return None
    return response.text

def parse_domains(html):
    soup = BeautifulSoup(html, 'html.parser')
    domains = set()
    for div in soup.find_all('div', class_='yuRUbf'):
        a_tag = div.find('a', href=True)
        if a_tag:
            url = a_tag['href']
            domain = urlparse(url).netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            domains.add(domain.lower())
    return domains

def load_top_domains(filename):
    if not os.path.exists(filename):
        print(f"Top domains file '{filename}' not found!")
        return set()
    with open(filename, 'r') as f:
        return set(line.strip().lower() for line in f if line.strip())

def save_domains(domains, date_str, target_domain, top_domains):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    # File named with date + target domain (dots replaced with underscores for safety)
    safe_target = target_domain.replace('.', '_')
    filename = os.path.join(RESULTS_DIR, f"{date_str}_{safe_target}.txt")
    
    # Load existing domains already saved
    existing_domains = set()
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing_domains = set(line.strip().lower() for line in f if line.strip())
    
    # Filter new domains: exclude those in existing or top 1M domains
    filtered_domains = {d for d in domains if d not in existing_domains and d not in top_domains}

    if not filtered_domains:
        print(f"No new filtered domains to append for {target_domain}.")
        return

    with open(filename, 'a') as f:
        for domain in sorted(filtered_domains):
            f.write(domain + "\n")
    print(f"Appended {len(filtered_domains)} new domains to {filename}")

def main():
    date_str = datetime.now().strftime('%Y-%m-%d')
    top_domains = load_top_domains(TOP_DOMAINS_FILE)

    for target_domain in TARGET_DOMAINS:
        print(f"Starting search for: {target_domain}")
        query = f'intext:"{target_domain}"'
        all_domains = set()

        for page_num in range(MAX_PAGES):
            start = page_num * 10
            print(f"Fetching Google page {page_num+1} (start={start}) for {target_domain}...")
            html = get_search_results(query, start)
            if not html:
                break
            domains = parse_domains(html)
            print(f"Found {len(domains)} domains on page {page_num+1} for {target_domain}")
            all_domains.update(domains)
            time.sleep(WAIT_BETWEEN_REQUESTS)

        if all_domains:
            save_domains(all_domains, date_str, target_domain, top_domains)
        else:
            print(f"No domains found for {target_domain}")

if __name__ == "__main__":
    main()
