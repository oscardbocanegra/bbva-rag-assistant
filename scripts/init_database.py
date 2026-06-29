from app.database.connection import get_engine
from app.database.models import Base


def main() -> None:
    engine = get_engine()

    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully")


if __name__ == "__main__":
    main()