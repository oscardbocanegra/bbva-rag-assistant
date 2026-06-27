from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scraping.content_cleaner import ContentCleaner


class LocalSnapshotLoader:
    """
    Procesa archivos HTML guardados localmente y los transforma en documentos
    crudos y limpios compatibles con el pipeline de ingestión RAG.
    """

    def __init__(
        self,
        snapshots_path: str = "data/source_snapshots",
        raw_data_path: str = "data/raw",
        processed_data_path: str = "data/processed",
    ) -> None:
        self.snapshots_path = Path(snapshots_path)
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)
        self.cleaner = ContentCleaner()

        self.snapshots_path.mkdir(parents=True, exist_ok=True)
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

    def process_all(self) -> list[dict[str, Any]]:
        html_files = sorted(self.snapshots_path.glob("*.html"))

        if not html_files:
            raise FileNotFoundError(
                f"No se encontraron archivos HTML en: {self.snapshots_path}"
            )

        results: list[dict[str, Any]] = []

        for html_file in html_files:
            try:
                result = self.process_file(html_file)
                results.append(result)

                print(
                    f"OK - {html_file.name} | "
                    f"{result['content_length']} caracteres limpios"
                )
            except Exception as exc:
                results.append(
                    {
                        "file_name": html_file.name,
                        "status": "error",
                        "error": str(exc),
                    }
                )

                print(f"ERROR - {html_file.name}: {exc}")

        self._save_run_summary(results)
        return results

    def process_file(self, html_file: Path) -> dict[str, Any]:
        html = html_file.read_text(encoding="utf-8", errors="ignore")
        cleaned_content = self.cleaner.clean_html(html)

        document_id = self._generate_document_id(html_file, cleaned_content["content"])
        source_url = self._extract_source_url(html_file, html)

        raw_document = {
            "document_id": document_id,
            "source_type": "local_snapshot",
            "source_file": html_file.name,
            "source_url": source_url,
            "loaded_at": self._utc_now(),
            "html": html,
        }

        processed_document = {
            "document_id": document_id,
            "source_type": "local_snapshot",
            "source_file": html_file.name,
            "url": source_url,
            "domain": "www.bbva.com.co",
            "title": cleaned_content["title"],
            "content": cleaned_content["content"],
            "content_hash": self._generate_hash(cleaned_content["content"]),
            "scraped_at": self._utc_now(),
        }

        self._save_json(self.raw_data_path / f"{document_id}.json", raw_document)
        self._save_json(
            self.processed_data_path / f"{document_id}.json",
            processed_document,
        )

        return {
            "file_name": html_file.name,
            "status": "success",
            "document_id": document_id,
            "title": cleaned_content["title"],
            "content_length": len(cleaned_content["content"]),
        }

    @staticmethod
    def _extract_source_url(html_file: Path, html: str) -> str:
        """
        Intenta recuperar la URL canónica del HTML.
        Si no existe, usa la home de BBVA para la página principal.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        canonical = soup.find("link", rel="canonical")
        if canonical and canonical.get("href"):
            return str(canonical["href"]).strip()

        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            return str(og_url["content"]).strip()

        if html_file.stem.lower() in {"home", "index", "bbva_home"}:
            return "https://www.bbva.com.co/"

        return f"local://{html_file.name}"

    @staticmethod
    def _generate_document_id(html_file: Path, content: str) -> str:
        value = f"{html_file.name}:{content}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _generate_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _save_run_summary(self, results: list[dict[str, Any]]) -> None:
        summary = {
            "source_type": "local_snapshot",
            "run_at": self._utc_now(),
            "total_files": len(results),
            "successful_files": sum(
                item["status"] == "success" for item in results
            ),
            "failed_files": sum(
                item["status"] == "error" for item in results
            ),
            "results": results,
        }

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._save_json(
            self.raw_data_path / f"local_snapshot_run_{timestamp}.json",
            summary,
        )

    @staticmethod
    def _save_json(path: Path, data: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()