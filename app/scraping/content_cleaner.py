from __future__ import annotations

import re

from bs4 import BeautifulSoup


class ContentCleaner:
    """
    Extrae texto útil desde HTML y elimina navegación, scripts,
    botones y elementos visuales no relevantes para RAG.
    """

    REMOVABLE_TAGS = [
        "script",
        "style",
        "noscript",
        "svg",
        "iframe",
        "footer",
        "nav",
        "header",
        "aside",
        "form",
        "button",
    ]

    def clean_html(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html, "lxml")

        for tag_name in self.REMOVABLE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        return {
            "title": self._extract_title(soup),
            "content": self._extract_main_content(soup),
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return self._normalize_whitespace(soup.title.string)

        h1 = soup.find("h1")
        if h1:
            return self._normalize_whitespace(
                h1.get_text(" ", strip=True)
            )

        return "Untitled document"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        main_node = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.body
        )

        if main_node is None:
            return ""

        for tag in main_node.find_all(["a", "button"]):
            tag.decompose()

        text_blocks: list[str] = []

        for element in main_node.find_all(["h1", "h2", "h3", "p", "li"]):
            text = self._normalize_whitespace(
                element.get_text(" ", strip=True)
            )

            if self._is_relevant_text(text):
                text_blocks.append(text)

        unique_blocks = list(dict.fromkeys(text_blocks))

        return "\n\n".join(unique_blocks)

    @staticmethod
    def _is_relevant_text(text: str) -> bool:
        if not text:
            return False

        ignored_exact_texts = {
            "conocer más",
            "ver más",
            "ver tarjetas",
            "solicitar ahora",
            "quiero participar",
            "consultar",
            "descargar",
            "cerrar",
            "aceptar",
            "menú",
            "buscador",
        }

        normalized = text.lower().strip()

        if normalized in ignored_exact_texts:
            return False

        # Mantiene títulos cortos como “Cuenta de ahorro BBVA”.
        return len(normalized) >= 5

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()