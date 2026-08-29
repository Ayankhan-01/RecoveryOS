from statistics import mean, median

from app.database import SessionLocal
from app.models.customer import Customer
from app.models.payment import Payment
from app.services.ml_predictor import RecoveryPredictor
from app.services.recovery_engine import calculate_probability


def main():
    db = SessionLocal()

    try:
        predictor = RecoveryPredictor()

        customers = {
            customer.id: customer
            for customer in db.query(Customer).all()
        }

        payments = (
            db.query(Payment)
            .filter(Payment.status == "FAILED")
            .all()
        )

        ml_probabilities = []
        rule_probabilities = []

        for payment in payments:
            customer = customers[payment.customer_id]

            ml_probability = predictor.predict_probability(
                customer,
                payment,
            )

            rule_probability = calculate_probability(
                customer,
                payment,
            )

            ml_probabilities.append(
                ml_probability
            )

            rule_probabilities.append(
                rule_probability
            )

        print("RecoveryOS Probability Comparison")
        print("---------------------------------")
        print(f"Failed payments: {len(payments)}")

        print("\nML model:")
        print(
            f"Minimum: {min(ml_probabilities):.4f}"
        )
        print(
            f"Maximum: {max(ml_probabilities):.4f}"
        )
        print(
            f"Average: {mean(ml_probabilities):.4f}"
        )
        print(
            f"Median: {median(ml_probabilities):.4f}"
        )

        print("\nRules engine:")
        print(
            f"Minimum: {min(rule_probabilities):.4f}"
        )
        print(
            f"Maximum: {max(rule_probabilities):.4f}"
        )
        print(
            f"Average: {mean(rule_probabilities):.4f}"
        )
        print(
            f"Median: {median(rule_probabilities):.4f}"
        )

        print("\nML probability bands:")
        print(
            ">= 0.65:",
            sum(p >= 0.65 for p in ml_probabilities),
        )
        print(
            "0.40 - 0.6499:",
            sum(
                0.40 <= p < 0.65
                for p in ml_probabilities
            ),
        )
        print(
            "0.20 - 0.3999:",
            sum(
                0.20 <= p < 0.40
                for p in ml_probabilities
            ),
        )
        print(
            "< 0.20:",
            sum(p < 0.20 for p in ml_probabilities),
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()