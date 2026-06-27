from __future__ import annotations

import re

from bs4 import BeautifulSoup


class ContentCleaner:
    """
    Extrae contenido textual útil desde HTML institucional.

    El objetivo es reducir navegación, botones, banners y elementos visuales
    que no aportan contexto al sistema RAG.
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
        """
        Recibe HTML crudo y devuelve título + contenido limpio.
        """
        soup = BeautifulSoup(html, "lxml")

        for tag_name in self.REMOVABLE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        title = self._extract_title(soup)
        content = self._extract_main_content(soup)

        return {
            "title": title,
            "content": content,
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Prioriza el título HTML y usa H1 como alternativa.
        """
        if soup.title and soup.title.string:
            return self._normalize_whitespace(soup.title.string)

        h1 = soup.find("h1")
        if h1:
            return self._normalize_whitespace(
                h1.get_text(" ", strip=True)
            )

        return "Untitled document"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extrae bloques textuales relevantes desde main, article, role=main o body.
        """
        main_node = (
            soup.find("main")
            or soup.find("article")
            or soup.find(attrs={"role": "main"})
            or soup.body
        )

        if not main_node:
            return ""

        # Los enlaces y botones suelen agregar CTAs, navegación y duplicados.
        for tag in main_node.find_all(["button", "a"]):
            tag.decompose()

        text_blocks: list[str] = []

        for element in main_node.find_all(["h1", "h2", "h3", "p", "li"]):
            text = self._normalize_whitespace(
                element.get_text(" ", strip=True)
            )

            if self._is_relevant_text(text):
                text_blocks.append(text)

        # Conserva orden y elimina duplicados exactos.
        deduplicated_blocks = list(dict.fromkeys(text_blocks))

        return "\n\n".join(deduplicated_blocks)

    @staticmethod
    def _is_relevant_text(text: str) -> bool:
        """
        Filtra fragmentos cortos, controles de interfaz y CTAs frecuentes.
        """
        if len(text) < 30:
            return False

        ignored_fragments = [
            "conocer más",
            "ver más",
            "ver tarjetas",
            "quiero participar",
            "solicitar tarjeta",
            "consultar",
            "descargar",
            "ir a",
            "1 of",
            "2 of",
            "3 of",
            "menú",
            "buscador",
            "cerrar",
            "aceptar",
            "cookies",
            "política de privacidad",
            "términos y condiciones",
        ]

        normalized = text.lower()

        return not any(
            fragment in normalized
            for fragment in ignored_fragments
        )

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """
        Normaliza saltos de línea, tabs y múltiples espacios.
        """
        return re.sub(r"\s+", " ", text).strip()