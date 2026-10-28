from __future__ import annotations

import getpass

from sqlalchemy import select

from auth.security import hash_password
from database import Base, SessionLocal, engine
from models import User


def main() -> None:
    Base.metadata.create_all(bind=engine)
    name = input("Administrator name: ").strip()
    email = input("Administrator email: ").strip().lower()
    password = getpass.getpass("Administrator password (8+ characters): ")
    if len(name) < 2 or len(password) < 8:
        raise SystemExit("Name must be at least 2 characters and password at least 8 characters.")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            existing.name = name
            existing.password_hash = hash_password(password)
            existing.role = "admin"
            print("Existing account promoted to administrator.")
        else:
            db.add(User(name=name, email=email, password_hash=hash_password(password), role="admin"))
            print("Administrator account created.")
        db.commit()


if __name__ == "__main__":
    main()

