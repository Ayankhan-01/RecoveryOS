from datetime import datetime, timedelta

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
        # ============================================================
        # 1. DEFAULT MERCHANT POLICY
        # ============================================================

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

        # ============================================================
        # 2. DEMO CUSTOMERS
        # ============================================================

        customer_count = db.query(Customer).count()

        if customer_count == 0:

            customers = [
                Customer(
                    customer_code="CUS001",
                    segment="premium",
                    lifetime_value=25000,
                    orders_count=42,
                    successful_payments=38,
                    failed_payments=4,
                    previous_recovery_success=0.75,
                    contact_count=0,
                    created_at=datetime.utcnow(),
                ),
                Customer(
                    customer_code="CUS002",
                    segment="regular",
                    lifetime_value=12000,
                    orders_count=20,
                    successful_payments=17,
                    failed_payments=3,
                    previous_recovery_success=0.60,
                    contact_count=1,
                    created_at=datetime.utcnow(),
                ),
                Customer(
                    customer_code="CUS003",
                    segment="premium",
                    lifetime_value=45000,
                    orders_count=65,
                    successful_payments=60,
                    failed_payments=5,
                    previous_recovery_success=0.80,
                    contact_count=0,
                    created_at=datetime.utcnow(),
                ),
                Customer(
                    customer_code="CUS004",
                    segment="regular",
                    lifetime_value=8000,
                    orders_count=14,
                    successful_payments=10,
                    failed_payments=4,
                    previous_recovery_success=0.40,
                    contact_count=2,
                    created_at=datetime.utcnow(),
                ),
                Customer(
                    customer_code="CUS005",
                    segment="new",
                    lifetime_value=3000,
                    orders_count=5,
                    successful_payments=3,
                    failed_payments=2,
                    previous_recovery_success=0.30,
                    contact_count=0,
                    created_at=datetime.utcnow(),
                ),
                Customer(
                    customer_code="CUS006",
                    segment="premium",
                    lifetime_value=32000,
                    orders_count=50,
                    successful_payments=46,
                    failed_payments=4,
                    previous_recovery_success=0.70,
                    contact_count=1,
                    created_at=datetime.utcnow(),
                ),
            ]

            db.add_all(customers)
            db.commit()

            print(f"Created {len(customers)} demo customers.")

        else:
            print("Customers already exist.")

        # ============================================================
        # 3. DEMO FAILED PAYMENTS
        # ============================================================

        payment_count = db.query(Payment).count()

        if payment_count == 0:

            customer_map = {
                customer.customer_code: customer.id
                for customer in db.query(Customer).all()
            }

            now = datetime.utcnow()

            payments = [
                Payment(
                    payment_code="PAY001",
                    customer_id=customer_map["CUS001"],
                    amount=2499.00,
                    payment_method="UPI",
                    failure_reason="INSUFFICIENT_FUNDS",
                    status="failed",
                    created_at=now - timedelta(hours=2),
                ),
                Payment(
                    payment_code="PAY002",
                    customer_id=customer_map["CUS002"],
                    amount=1299.00,
                    payment_method="CARD",
                    failure_reason="CARD_DECLINED",
                    status="failed",
                    created_at=now - timedelta(hours=5),
                ),
                Payment(
                    payment_code="PAY003",
                    customer_id=customer_map["CUS003"],
                    amount=4999.00,
                    payment_method="UPI",
                    failure_reason="BANK_ERROR",
                    status="failed",
                    created_at=now - timedelta(hours=8),
                ),
                Payment(
                    payment_code="PAY004",
                    customer_id=customer_map["CUS004"],
                    amount=799.00,
                    payment_method="CARD",
                    failure_reason="INSUFFICIENT_FUNDS",
                    status="failed",
                    created_at=now - timedelta(hours=12),
                ),
                Payment(
                    payment_code="PAY005",
                    customer_id=customer_map["CUS005"],
                    amount=1999.00,
                    payment_method="NETBANKING",
                    failure_reason="PAYMENT_TIMEOUT",
                    status="failed",
                    created_at=now - timedelta(hours=18),
                ),
                Payment(
                    payment_code="PAY006",
                    customer_id=customer_map["CUS006"],
                    amount=3499.00,
                    payment_method="UPI",
                    failure_reason="BANK_ERROR",
                    status="failed",
                    created_at=now - timedelta(hours=24),
                ),
                Payment(
                    payment_code="PAY007",
                    customer_id=customer_map["CUS001"],
                    amount=1599.00,
                    payment_method="CARD",
                    failure_reason="CARD_DECLINED",
                    status="failed",
                    created_at=now - timedelta(hours=30),
                ),
                Payment(
                    payment_code="PAY008",
                    customer_id=customer_map["CUS003"],
                    amount=2799.00,
                    payment_method="UPI",
                    failure_reason="INSUFFICIENT_FUNDS",
                    status="failed",
                    created_at=now - timedelta(hours=36),
                ),
            ]

            db.add_all(payments)
            db.commit()

            print(f"Created {len(payments)} demo failed payments.")

        else:
            print("Payments already exist.")

        print("RecoveryOS database initialization complete.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()