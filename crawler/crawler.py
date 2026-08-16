import os, hashlib, httpx
from bs4 import BeautifulSoup

SEEDS = [x.strip() for x in os.getenv("CRAWLER_SEEDS", "").split(",") if x.strip()]

def fetch(url):
    r = httpx.get(url, timeout=20, follow_redirects=True,
                  headers={"User-Agent": "JainAI-ResearchCrawler/0.1"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    return {
        "url": str(r.url),
        "title": soup.title.string if soup.title else "",
        "content": text,
        "content_hash": hashlib.sha256(text.encode()).hexdigest()
    }

if __name__ == "__main__":
    print("Jain AI crawler started.")
    for url in SEEDS:
        try:
            print(fetch(url)["url"])
        except Exception as e:
            print("ERROR", url, e)
