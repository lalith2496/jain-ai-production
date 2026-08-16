import hashlib
import os

import httpx
from bs4 import BeautifulSoup

from app.url_security import validate_public_http_url


MAX_REDIRECTS = int(os.getenv("CRAWLER_MAX_REDIRECTS", "5"))
MAX_BYTES = int(os.getenv("CRAWLER_MAX_BYTES", "2000000"))

ALLOWED_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "text/plain",
)


def _fetch(url: str) -> tuple[httpx.Response, bytes]:
    current = validate_public_http_url(url)

    headers = {
        "User-Agent": "JainAI-Education-Crawler/1.0 (+https://jainlibrary.in)"
    }

    with httpx.Client(
        headers=headers,
        timeout=30,
        follow_redirects=False,
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            validate_public_http_url(current)

            with client.stream("GET", current) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        response.raise_for_status()
                    current = str(response.url.join(location))
                    continue

                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if content_type and not any(
                    allowed in content_type
                    for allowed in ALLOWED_CONTENT_TYPES
                ):
                    raise ValueError(
                        f"Unsupported crawler content type: {content_type}"
                    )

                chunks = []
                size = 0

                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ValueError(
                            f"Page exceeds crawler limit of {MAX_BYTES} bytes"
                        )
                    chunks.append(chunk)

                body = b"".join(chunks)
                response.read = lambda: body
                return response, body

        raise ValueError("Too many redirects")


def crawl_url(url: str) -> dict:
    response, body = _fetch(url)

    encoding = response.encoding or "utf-8"
    text = body.decode(encoding, errors="replace")

    soup = BeautifulSoup(text, "html.parser")

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "iframe",
            "svg",
            "canvas",
        ]
    ):
        tag.decompose()

    title = ""

    if soup.title:
        title = soup.title.get_text(strip=True)

    content = "\n".join(
        line.strip()
        for line in soup.stripped_strings
        if line.strip()
    )

    if not content:
        raise ValueError("No readable content found")

    content_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    return {
        "url": str(response.url),
        "title": title,
        "content": content,
        "content_hash": content_hash,
    }
