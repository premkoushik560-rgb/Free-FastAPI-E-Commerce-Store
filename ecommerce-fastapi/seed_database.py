from database import Base, SessionLocal, engine
from services.seed import seed_sample_data


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_sample_data(db)
    print("Sample data is ready. Existing products and categories were preserved.")


if __name__ == "__main__":
    main()

