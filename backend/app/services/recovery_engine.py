from dataclasses import dataclass

from app.models.customer import Customer
from app.models.merchant_policy import MerchantPolicy
from app.models.payment import Payment


@dataclass
class RecoveryDecision:
    action: str
    probability: float
    expected_value: float
    intervention_cost: float
    reason: str


def calculate_probability(
    customer: Customer,
    payment: Payment,
) -> float:
    probability = customer.previous_recovery_success

    # Customer behavior
    if customer.failed_payments == 0:
        probability += 0.10

    if customer.failed_payments >= 3:
        probability -= 0.15

    # Contact history
    if customer.contact_count == 0:
        probability += 0.05

    if customer.contact_count >= 2:
        probability -= 0.20

    # Failure reason
    if payment.failure_reason == "BANK_TIMEOUT":
        probability += 0.10

    elif payment.failure_reason == "NETWORK_ERROR":
        probability += 0.05

    elif payment.failure_reason == "INSUFFICIENT_FUNDS":
        probability -= 0.10

    elif payment.failure_reason == "BANK_DECLINED":
        probability -= 0.15

    elif payment.failure_reason == "AUTHENTICATION_FAILED":
        probability -= 0.20

    # High-value customer
    if customer.lifetime_value >= 25000:
        probability += 0.05

    # Keep probability between 0 and 1.
    probability = max(0.0, min(1.0, probability))

    return round(probability, 4)


def choose_action(
    probability: float,
    payment: Payment,
    policy: MerchantPolicy,
) -> RecoveryDecision:

    amount = float(payment.amount)

    if probability >= 0.65:
        action = "SEND_PAYMENT_LINK"
        cost = 5.00
        reason = (
            "High recovery probability; "
            "use the lowest-cost intervention."
        )

    elif probability >= 0.40:
        action = "SEND_REMINDER"
        cost = 2.00
        reason = (
            "Moderate recovery probability; "
            "reminder is sufficient."
        )

    elif probability >= 0.20:
        action = "OFFER_RETRY"
        cost = 1.00
        reason = (
            "Low-to-moderate probability; "
            "allow another payment attempt."
        )

    else:
        action = "NO_ACTION"
        cost = 0.00
        reason = (
            "Recovery probability is too low "
            "to justify intervention."
        )

    # Merchant safety limit.
    if cost > float(policy.max_intervention_cost):
        return RecoveryDecision(
            action="NO_ACTION",
            probability=probability,
            expected_value=0.00,
            intervention_cost=0.00,
            reason="Intervention exceeds merchant cost policy.",
        )

    gross_expected_recovery = amount * probability
    expected_value = gross_expected_recovery - cost

    if action == "NO_ACTION":
        expected_value = 0.00

    elif expected_value <= 0:
        return RecoveryDecision(
            action="NO_ACTION",
            probability=probability,
            expected_value=0.00,
            intervention_cost=0.00,
            reason=(
                "Expected recovery value does not "
                "justify intervention."
            ),
        )

    return RecoveryDecision(
        action=action,
        probability=probability,
        expected_value=round(expected_value, 2),
        intervention_cost=cost,
        reason=reason,
    )


def evaluate_payment(
    customer: Customer,
    payment: Payment,
    policy: MerchantPolicy,
) -> RecoveryDecision:

    probability = calculate_probability(
        customer=customer,
        payment=payment,
    )

    return choose_action(
        probability=probability,
        payment=payment,
        policy=policy,
    )