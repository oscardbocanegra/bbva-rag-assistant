from app.scraping.bbva_scraper import BBVAScraper


def main() -> None:
    scraper = BBVAScraper(
        sitemap_url="https://www.bbva.com.co/sitemap.xml",
        raw_data_path="data/raw",
        processed_data_path="data/processed",
        request_delay_seconds=1.0,
    )

    results = scraper.scrape(
        include_paths=[
            "/personas/",
            "/empresas/",
            "/educacion-financiera/",
            "/sostenibilidad/",
            "/informacion-corporativa/",
        ],
        exclude_paths=[
            "/personas/cards",
            "/login",
            "/buscador",
        ],
        max_urls=20,
    )

    successful = sum(item["status"] == "success" for item in results)
    failed = sum(item["status"] == "error" for item in results)

    print("\nScraping completed")
    print(f"Successful pages: {successful}")
    print(f"Failed pages: {failed}")


if __name__ == "__main__":
    main()