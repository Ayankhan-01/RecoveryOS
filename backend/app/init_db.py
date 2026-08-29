from app.database import Base, engine
from app.models import (
    Customer,
    Payment,
    RecoveryEvent,
    MerchantPolicy,
)


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("RecoveryOS database tables verified.")


if __name__ == "__main__":
    initialize_database()