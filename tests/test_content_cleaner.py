from app.scraping.content_cleaner import ContentCleaner


def test_clean_html_removes_navigation_and_scripts() -> None:
    html = """
    <html>
        <head>
            <title>Producto BBVA</title>
            <script>alert("remove me")</script>
        </head>
        <body>
            <header>Menú principal</header>
            <main>
                <h1>Cuenta de ahorro BBVA</h1>
                <p>
                    Esta cuenta permite administrar recursos y consultar
                    información financiera de forma sencilla.
                </p>
                <a href="/productos">Conocer más</a>
                <button>Solicitar ahora</button>
            </main>
            <footer>Footer institucional</footer>
        </body>
    </html>
    """

    cleaner = ContentCleaner()

    result = cleaner.clean_html(html)

    assert result["title"] == "Producto BBVA"
    assert "Cuenta de ahorro BBVA" in result["content"]
    assert "administrar recursos" in result["content"]

    assert "Menú principal" not in result["content"]
    assert "Footer institucional" not in result["content"]
    assert "Conocer más" not in result["content"]
    assert "Solicitar ahora" not in result["content"]