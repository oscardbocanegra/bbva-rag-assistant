from app.scraping.local_snapshot_loader import LocalSnapshotLoader


def main() -> None:
    loader = LocalSnapshotLoader(
        snapshots_path="data/source_snapshots",
        raw_data_path="data/raw",
        processed_data_path="data/processed",
    )

    results = loader.process_all()

    successful = sum(item["status"] == "success" for item in results)
    failed = sum(item["status"] == "error" for item in results)

    print("\nLocal snapshot ingestion completed")
    print(f"Successful files: {successful}")
    print(f"Failed files: {failed}")


if __name__ == "__main__":
    main()