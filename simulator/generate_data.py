import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# Make results reproducible.
random.seed(42)
np.random.seed(42)


NUM_CUSTOMERS = 5000
NUM_PAYMENTS = 10000


def main():
    print("RecoveryOS synthetic data generator")
    print(f"Customers: {NUM_CUSTOMERS}")
    print(f"Payments: {NUM_PAYMENTS}")

    segment_profiles = {
        "reliable": {
            "payment_success_rate": 0.96,
            "recovery_rate": 0.75,
            "avg_order_value": 1800,
            "order_frequency": 0.80,
            "contact_response_rate": 0.85,
        },
        "occasional": {
            "payment_success_rate": 0.88,
            "recovery_rate": 0.55,
            "avg_order_value": 1400,
            "order_frequency": 0.50,
            "contact_response_rate": 0.65,
        },
        "price_sensitive": {
            "payment_success_rate": 0.84,
            "recovery_rate": 0.60,
            "avg_order_value": 1100,
            "order_frequency": 0.45,
            "contact_response_rate": 0.70,
        },
        "high_value": {
            "payment_success_rate": 0.93,
            "recovery_rate": 0.80,
            "avg_order_value": 7500,
            "order_frequency": 0.65,
            "contact_response_rate": 0.90,
        },
        "unresponsive": {
            "payment_success_rate": 0.82,
            "recovery_rate": 0.25,
            "avg_order_value": 1600,
            "order_frequency": 0.40,
            "contact_response_rate": 0.15,
        },
        "frequent_failure": {
            "payment_success_rate": 0.65,
            "recovery_rate": 0.35,
            "avg_order_value": 1300,
            "order_frequency": 0.70,
            "contact_response_rate": 0.30,
        },
    }

    segments = list(segment_profiles.keys())

    segment_probabilities = [
        0.30,
        0.25,
        0.15,
        0.10,
        0.10,
        0.10,
    ]

    selected_segments = random.choices(
        segments,
        weights=segment_probabilities,
        k=NUM_CUSTOMERS,
    )

    customers = []

    for customer_number, segment in enumerate(selected_segments, start=1):
        profile = segment_profiles[segment]

        orders_count = max(
            1,
            int(np.random.poisson(profile["order_frequency"] * 10))
        )

        successful_payments = np.random.binomial(
            orders_count,
            profile["payment_success_rate"],
        )

        failed_payments = orders_count - successful_payments

        lifetime_value = (
            successful_payments
            * np.random.normal(
                profile["avg_order_value"],
                profile["avg_order_value"] * 0.25,
            )
        )

        lifetime_value = max(0, lifetime_value)

        customers.append({
            "customer_code": f"CUST_{customer_number:05d}",
            "segment": segment,
            "lifetime_value": round(lifetime_value, 2),
            "orders_count": orders_count,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "previous_recovery_success": profile["recovery_rate"],
            "contact_count": 0,
        })

    customers_df = pd.DataFrame(customers)

    print("\nCustomer segment distribution:")
    print(customers_df["segment"].value_counts())

    print("\nCustomer sample:")
    print(customers_df.head())

    print("\nAverage lifetime value by segment:")
    print(
        customers_df
        .groupby("segment")["lifetime_value"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )

    customers_df.to_csv(
        "customers.csv",
        index=False,
    )

    print("\nSaved customers.csv")

    payments_df = generate_payments(customers_df)

    print("\nPayment status distribution:")
    print(payments_df["status"].value_counts())

    print("\nPayment sample:")
    print(payments_df.head())

    payments_df.to_csv(
        "payments.csv",
        index=False,
    )

    print("\nSaved payments.csv")



def generate_payments(customers_df):
    failure_reasons = [
        "BANK_TIMEOUT",
        "INSUFFICIENT_FUNDS",
        "BANK_DECLINED",
        "NETWORK_ERROR",
        "AUTHENTICATION_FAILED",
    ]

    payment_methods = [
        "UPI",
        "CARD",
        "NETBANKING",
        "WALLET",
    ]

    payments = []

    segment_failure_rates = {
        "reliable": 0.04,
        "occasional": 0.12,
        "price_sensitive": 0.16,
        "high_value": 0.07,
        "unresponsive": 0.18,
        "frequent_failure": 0.35,
    }

    for payment_number in range(1, NUM_PAYMENTS + 1):

        customer = customers_df.sample(
            n=1,
            random_state=payment_number,
        ).iloc[0]

        segment = customer["segment"]

        failure_rate = segment_failure_rates[segment]

        is_failed = random.random() < failure_rate

        amount = np.random.normal(
            loc=customer["lifetime_value"] / max(customer["orders_count"], 1),
            scale=300,
        )

        amount = max(100, amount)

        payment_method = random.choice(payment_methods)

        if is_failed:
            failure_reason = random.choice(failure_reasons)
            status = "FAILED"
        else:
            failure_reason = None
            status = "SUCCESS"

        created_at = datetime.now() - timedelta(
            minutes=random.randint(0, 60 * 24 * 30)
        )

        payments.append({
            "payment_code": f"PAY_{payment_number:06d}",
            "customer_code": customer["customer_code"],
            "amount": round(amount, 2),
            "payment_method": payment_method,
            "failure_reason": failure_reason,
            "status": status,
            "created_at": created_at,
        })

    return pd.DataFrame(payments)
if __name__ == "__main__":
    main()