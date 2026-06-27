from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from app.scraping.content_cleaner import ContentCleaner
from app.scraping.sitemap_reader import SitemapReader, SitemapUrl


class BBVAScraper:
    """
    Orquesta descubrimiento de URLs, descarga HTML, limpieza de contenido
    y persistencia local de datos crudos y procesados.
    """

    def __init__(
        self,
        sitemap_url: str,
        raw_data_path: str = "data/raw",
        processed_data_path: str = "data/processed",
        request_delay_seconds: float = 1.0,
        timeout_seconds: int = 30,
    ) -> None:
        self.sitemap_reader = SitemapReader(sitemap_url=sitemap_url)
        self.cleaner = ContentCleaner()

        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)

        self.request_delay_seconds = request_delay_seconds
        self.timeout_seconds = timeout_seconds

        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

    def scrape(
        self,
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        max_urls: int = 30,
    ) -> list[dict[str, Any]]:
        sitemap_urls = self.sitemap_reader.fetch_urls()

        selected_urls = self.sitemap_reader.filter_urls(
            urls=sitemap_urls,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            max_urls=max_urls,
        )

        results: list[dict[str, Any]] = []

        for index, sitemap_item in enumerate(selected_urls, start=1):
            try:
                result = self._scrape_url(sitemap_item)
                results.append(result)
                print(f"[{index}/{len(selected_urls)}] OK - {sitemap_item.url}")
            except Exception as exc:
                results.append(
                    {
                        "url": sitemap_item.url,
                        "status": "error",
                        "error": str(exc),
                    }
                )
                print(f"[{index}/{len(selected_urls)}] ERROR - {sitemap_item.url}: {exc}")

            time.sleep(self.request_delay_seconds)

        self._save_run_summary(results)

        return results

    def _scrape_url(self, sitemap_item: SitemapUrl) -> dict[str, Any]:
        html = self._download_page(sitemap_item.url)
        cleaned_content = self.cleaner.clean_html(html)

        content_hash = self._generate_hash(cleaned_content["content"])
        file_key = self._generate_file_key(sitemap_item.url)

        raw_document = {
            "url": sitemap_item.url,
            "sitemap_last_modified": sitemap_item.last_modified,
            "scraped_at": self._utc_now(),
            "html": html,
        }

        processed_document = {
            "document_id": file_key,
            "url": sitemap_item.url,
            "domain": urlparse(sitemap_item.url).netloc,
            "title": cleaned_content["title"],
            "content": cleaned_content["content"],
            "content_hash": content_hash,
            "sitemap_last_modified": sitemap_item.last_modified,
            "scraped_at": self._utc_now(),
        }

        self._save_json(self.raw_data_path / f"{file_key}.json", raw_document)
        self._save_json(self.processed_data_path / f"{file_key}.json", processed_document)

        return {
            "url": sitemap_item.url,
            "status": "success",
            "document_id": file_key,
            "title": cleaned_content["title"],
            "content_length": len(cleaned_content["content"]),
        }

    def _download_page(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
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
            response = client.get(url)
            response.raise_for_status()
            return response.text

        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    def _save_run_summary(self, results: list[dict[str, Any]]) -> None:
        summary = {
            "run_at": self._utc_now(),
            "total_urls": len(results),
            "successful_urls": sum(item["status"] == "success" for item in results),
            "failed_urls": sum(item["status"] == "error" for item in results),
            "results": results,
        }

        filename = f"scrape_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        self._save_json(self.raw_data_path / filename, summary)

    @staticmethod
    def _generate_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_file_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _save_json(path: Path, data: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)