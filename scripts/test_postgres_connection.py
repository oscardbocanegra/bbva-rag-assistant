from sqlalchemy import text

from app.database.connection import get_db_session


def main() -> None:
    with next(get_db_session()) as session:
        result = session.execute(
            text("SELECT current_database(), current_user;")
        ).one()

    print("PostgreSQL connection OK")
    print(f"Database: {result[0]}")
    print(f"User: {result[1]}")


if __name__ == "__main__":
    main()