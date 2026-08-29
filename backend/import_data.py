import pandas as pd

from app.database import SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment


def import_customers():
    df = pd.read_csv("../simulator/customers.csv")

    db = SessionLocal()

    try:
        customers = []

        for _, row in df.iterrows():
            customer = Customer(
                customer_code=row["customer_code"],
                segment=row["segment"],
                lifetime_value=float(row["lifetime_value"]),
                orders_count=int(row["orders_count"]),
                successful_payments=int(row["successful_payments"]),
                failed_payments=int(row["failed_payments"]),
                previous_recovery_success=float(
                    row["previous_recovery_success"]
                ),
                contact_count=int(row["contact_count"]),
                created_at=pd.Timestamp.now().to_pydatetime(),
            )

            customers.append(customer)

        db.add_all(customers)
        db.commit()

        print(f"Imported {len(customers)} customers.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def import_payments():
    df = pd.read_csv("../simulator/payments.csv")

    db = SessionLocal()

    try:
        customer_map = {
            customer.customer_code: customer.id
            for customer in db.query(Customer).all()
        }

        payments = []

        for _, row in df.iterrows():
            customer_id = customer_map[row["customer_code"]]

            failure_reason = row["failure_reason"]

            if pd.isna(failure_reason):
                failure_reason = None

            payment = Payment(
                payment_code=row["payment_code"],
                customer_id=customer_id,
                amount=float(row["amount"]),
                payment_method=row["payment_method"],
                failure_reason=failure_reason,
                status=row["status"],
                created_at=pd.to_datetime(
                    row["created_at"]
                ).to_pydatetime(),
            )

            payments.append(payment)

        db.add_all(payments)
        db.commit()

        print(f"Imported {len(payments)} payments.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_payments()