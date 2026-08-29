from dataclasses import dataclass

from app.models.customer import Customer
from app.models.merchant_policy import MerchantPolicy
from app.models.payment import Payment
from app.services.ml_predictor import RecoveryPredictor
from app.services.recovery_engine import calculate_probability


ML_WEIGHT = 0.70
RULE_WEIGHT = 0.30


@dataclass
class HybridDecision:
    action: str
    rules_probability: float
    ml_probability: float
    hybrid_probability: float
    expected_value: float
    intervention_cost: float
    reason: str


def build_decision(
    customer: Customer,
    payment: Payment,
    policy: MerchantPolicy,
    ml_probability: float,
) -> HybridDecision:

    # --------------------------------------------------------
    # RULES PROBABILITY
    # --------------------------------------------------------

    rules_probability = calculate_probability(
        customer=customer,
        payment=payment,
    )

    # --------------------------------------------------------
    # HYBRID PROBABILITY
    # --------------------------------------------------------

    hybrid_probability = (
        (ml_probability * ML_WEIGHT)
        + (rules_probability * RULE_WEIGHT)
    )

    hybrid_probability = round(
        hybrid_probability,
        4,
    )

    amount = float(payment.amount)

    # --------------------------------------------------------
    # ACTION SELECTION
    # --------------------------------------------------------

    if hybrid_probability >= 0.65:

        action = "SEND_PAYMENT_LINK"
        cost = 5.00

        reason = (
            "High hybrid recovery probability; "
            "send payment link."
        )

    elif hybrid_probability >= 0.40:

        action = "SEND_REMINDER"
        cost = 2.00

        reason = (
            "Moderate hybrid recovery probability; "
            "send reminder."
        )

    elif hybrid_probability >= 0.20:

        action = "OFFER_RETRY"
        cost = 1.00

        reason = (
            "Low-to-moderate hybrid probability; "
            "offer payment retry."
        )

    else:

        action = "NO_ACTION"
        cost = 0.00

        reason = (
            "Hybrid recovery probability is too low "
            "to justify intervention."
        )

    # --------------------------------------------------------
    # MERCHANT COST POLICY
    # --------------------------------------------------------

    if cost > float(policy.max_intervention_cost):

        return HybridDecision(
            action="NO_ACTION",
            rules_probability=rules_probability,
            ml_probability=ml_probability,
            hybrid_probability=hybrid_probability,
            expected_value=0.00,
            intervention_cost=0.00,
            reason=(
                "Intervention exceeds merchant cost policy."
            ),
        )

    # --------------------------------------------------------
    # NO ACTION
    # --------------------------------------------------------

    if action == "NO_ACTION":

        return HybridDecision(
            action="NO_ACTION",
            rules_probability=rules_probability,
            ml_probability=ml_probability,
            hybrid_probability=hybrid_probability,
            expected_value=0.00,
            intervention_cost=0.00,
            reason=reason,
        )

    # --------------------------------------------------------
    # EXPECTED VALUE
    # --------------------------------------------------------

    gross_expected_recovery = (
        amount * hybrid_probability
    )

    expected_value = (
        gross_expected_recovery - cost
    )

    # --------------------------------------------------------
    # NEGATIVE EXPECTED VALUE
    # --------------------------------------------------------

    if expected_value <= 0:

        return HybridDecision(
            action="NO_ACTION",
            rules_probability=rules_probability,
            ml_probability=ml_probability,
            hybrid_probability=hybrid_probability,
            expected_value=0.00,
            intervention_cost=0.00,
            reason=(
                "Expected recovery value does not "
                "justify intervention."
            ),
        )

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    return HybridDecision(
        action=action,
        rules_probability=rules_probability,
        ml_probability=ml_probability,
        hybrid_probability=hybrid_probability,
        expected_value=round(
            expected_value,
            2,
        ),
        intervention_cost=cost,
        reason=reason,
    )


def evaluate_hybrid(
    customer: Customer,
    payment: Payment,
    policy: MerchantPolicy,
    predictor: RecoveryPredictor,
) -> HybridDecision:

    ml_probability = predictor.predict_probability(
        customer=customer,
        payment=payment,
    )

    return build_decision(
        customer=customer,
        payment=payment,
        policy=policy,
        ml_probability=ml_probability,
    )