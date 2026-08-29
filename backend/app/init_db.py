from datetime import datetime

from app.database import Base, engine, SessionLocal
from app.models import (
    Customer,
    Payment,
    RecoveryEvent,
    MerchantPolicy,
)


def initialize_database():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Create the default merchant policy only if one doesn't exist
        policy = db.query(MerchantPolicy).first()

        if policy is None:
            policy = MerchantPolicy(
                id=1,
                max_attempts=2,
                max_contacts=2,
                max_discount_percent=5.00,
                max_intervention_cost=10.00,
                recovery_window_hours=48,
                created_at=datetime.utcnow(),
            )

            db.add(policy)
            db.commit()

            print("RecoveryOS default merchant policy created.")
        else:
            print("RecoveryOS merchant policy already exists.")

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()