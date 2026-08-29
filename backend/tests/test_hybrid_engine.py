from app.models.customer import Customer
from app.models.merchant_policy import MerchantPolicy
from app.models.payment import Payment
from app.services.hybrid_engine import build_decision


def make_customer():
    return Customer(
        customer_code="TEST_CUSTOMER",
        segment="REGULAR",
        lifetime_value=10000.0,
        orders_count=20,
        successful_payments=16,
        failed_payments=4,
        previous_recovery_success=0.6,
        contact_count=2,
    )


def make_payment(amount=1000):
    return Payment(
        payment_code="TEST_PAYMENT",
        amount=amount,
        status="FAILED",
        failure_reason="INSUFFICIENT_FUNDS",
        customer_id=1,
    )


def make_policy(cost=10):
    return MerchantPolicy(
        max_intervention_cost=cost,
    )


def test_hybrid_probability_uses_70_30_weighting():
    decision = build_decision(
        make_customer(),
        make_payment(),
        make_policy(),
        ml_probability=0.8,
    )

    expected = round((0.8 * 0.70) + (decision.rules_probability * 0.30), 4)

    assert decision.hybrid_probability == expected


def test_high_probability_selects_payment_link():
    decision = build_decision(
        make_customer(),
        make_payment(),
        make_policy(),
        ml_probability=0.95,
    )

    assert decision.action == "SEND_PAYMENT_LINK"


def test_medium_probability_selects_reminder():
    decision = build_decision(
        make_customer(),
        make_payment(),
        make_policy(),
        ml_probability=0.55,
    )

    assert decision.action in {"SEND_REMINDER", "SEND_PAYMENT_LINK"}


def test_low_probability_does_not_select_high_cost_action():
    decision = build_decision(
        make_customer(),
        make_payment(),
        make_policy(),
        ml_probability=0.10,
    )

    assert decision.action in {"NO_ACTION", "OFFER_RETRY"}


def test_cost_policy_can_block_intervention():
    decision = build_decision(
        make_customer(),
        make_payment(),
        make_policy(cost=0),
        ml_probability=0.95,
    )

    assert decision.action == "NO_ACTION"
    assert decision.intervention_cost == 0.0
