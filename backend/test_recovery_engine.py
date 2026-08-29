from collections import Counter

from app.database import SessionLocal
from app.models.customer import Customer
from app.models.merchant_policy import MerchantPolicy
from app.models.payment import Payment
from app.services.recovery_engine import evaluate_payment


def main():
    db = SessionLocal()

    try:
        policy = db.query(MerchantPolicy).first()

        payments = (
            db.query(Payment)
            .filter(Payment.status == "FAILED")
            .all()
        )

        customers = {
            customer.id: customer
            for customer in db.query(Customer).all()
        }

        action_counts = Counter()
        total_failed_value = 0.0
        total_expected_recovery = 0.0
        total_intervention_cost = 0.0

        for payment in payments:
            customer = customers[payment.customer_id]

            decision = evaluate_payment(
                customer=customer,
                payment=payment,
                policy=policy,
            )

            action_counts[decision.action] += 1

            total_failed_value += float(payment.amount)
            total_expected_recovery += decision.expected_value
            total_intervention_cost += decision.intervention_cost

        print("RecoveryOS Batch Evaluation")
        print("---------------------------")
        print(f"Failed payments: {len(payments)}")
        print(f"Failed payment value: ₹{total_failed_value:,.2f}")

        print("\nAction distribution:")
        for action, count in action_counts.most_common():
            print(f"{action}: {count}")

        print(
            f"\nExpected recovery value: "
            f"₹{total_expected_recovery:,.2f}"
        )

        print(
            f"Intervention cost: "
            f"₹{total_intervention_cost:,.2f}"
        )

        net_value = (
            total_expected_recovery
            - total_intervention_cost
        )

        print(
            f"Net expected value: "
            f"₹{net_value:,.2f}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()