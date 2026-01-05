import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse

EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Professional Email Extractor)"
}

class Scraper:
    def __init__(self, start_url, max_pages=50, delay=2):
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay
        self.visited = set()
        self.to_visit = [start_url]
        self.emails = set()
        self.logs = []
        self.progress = 0  # percentage

        self.domain = urlparse(start_url).netloc
        self.logs.append(f"[INIT] Target domain: {self.domain}")

    def step(self):
        """Process one page and update progress"""
        if not self.to_visit or len(self.visited) >= self.max_pages:
            self.progress = 100
            return False  # finished

        url = self.to_visit.pop(0)
        if url in self.visited:
            return True  # skip but continue

        self.logs.append(f"[OPEN] Visiting: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            self.visited.add(url)

            soup = BeautifulSoup(response.text, "lxml")
            text = soup.get_text(separator=" ")

            # Regex emails
            found = re.findall(EMAIL_REGEX, text)
            for email in found:
                if email not in self.emails:
                    self.emails.add(email)
                    self.logs.append(f"[FOUND] Email: {email}")

            # mailto links
            for link in soup.select('a[href^="mailto:"]'):
                email = link['href'].replace("mailto:", "").split("?")[0]
                if email not in self.emails:
                    self.emails.add(email)
                    self.logs.append(f"[FOUND] Mailto: {email}")

            # internal links
            for a in soup.find_all("a", href=True):
                full_url = urljoin(url, a["href"])
                if urlparse(full_url).netloc == self.domain and full_url not in self.visited:
                    self.to_visit.append(full_url)

            time.sleep(self.delay)

        except Exception as e:
            self.logs.append(f"[ERROR] {str(e)}")

        # update progress
        self.progress = int(len(self.visited) / self.max_pages * 100)
        if self.progress > 100:
            self.progress = 100

        return True

    def get_results(self):
        return sorted(self.emails), self.logs
