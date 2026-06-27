from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class SitemapUrl:
    url: str
    last_modified: str | None = None


class SitemapReader:
    """
    Lee un sitemap XML y devuelve URLs candidatas para scraping.
    """

    def __init__(
        self,
        sitemap_url: str,
        allowed_domain: str = "www.bbva.com.co",
        timeout_seconds: int = 30,
    ) -> None:
        self.sitemap_url = sitemap_url
        self.allowed_domain = allowed_domain
        self.timeout_seconds = timeout_seconds

    def fetch_urls(self) -> list[SitemapUrl]:
        xml_content = self._download_sitemap()
        return self._parse_sitemap(xml_content)

    def _download_sitemap(self) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/xml,text/xml,text/html,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.bbva.com.co/",
            "Cache-Control": "no-cache",
        }

        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = client.get(self.sitemap_url)
            response.raise_for_status()
            return response.text

    def _parse_sitemap(self, xml_content: str) -> list[SitemapUrl]:
        soup = BeautifulSoup(xml_content, "xml")

        urls: list[SitemapUrl] = []

        for url_node in soup.find_all("url"):
            loc = url_node.find("loc")
            lastmod = url_node.find("lastmod")

            if not loc or not loc.text:
                continue

            url = loc.text.strip()

            if self._is_allowed_url(url):
                urls.append(
                    SitemapUrl(
                        url=url,
                        last_modified=lastmod.text.strip() if lastmod and lastmod.text else None,
                    )
                )

        return urls

    def filter_urls(
        self,
        urls: Iterable[SitemapUrl],
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        max_urls: int | None = None,
    ) -> list[SitemapUrl]:
        include_paths = include_paths or []
        exclude_paths = exclude_paths or []

        filtered: list[SitemapUrl] = []

        for item in urls:
            path = urlparse(item.url).path.lower()

            if include_paths and not any(fragment.lower() in path for fragment in include_paths):
                continue

            if any(fragment.lower() in path for fragment in exclude_paths):
                continue

            filtered.append(item)

            if max_urls and len(filtered) >= max_urls:
                break

        return filtered

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.netloc != self.allowed_domain:
            return False

        blocked_fragments = [
            "/personas/cards",
            ".content.html",
        ]

        return not any(fragment in parsed.path for fragment in blocked_fragments)