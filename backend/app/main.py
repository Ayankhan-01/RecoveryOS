from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import SessionLocal, Base, engine
from app.models.customer import Customer
from app.models.merchant_policy import MerchantPolicy
from app.models.payment import Payment
from app.models.recovery_event import RecoveryEvent

from app.services.hybrid_engine import (
    evaluate_hybrid,
    build_decision,
)
from app.services.ml_predictor import RecoveryPredictor


app = FastAPI(
    title="RecoveryOS API",
    version="0.1.0",
    description="Payment recovery decision engine",
)
Base.metadata.create_all(bind=engine)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://recoveryos-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ML PREDICTOR
# ============================================================
#
# Load the model ONCE when the API process starts.
#
# Do NOT create RecoveryPredictor() inside every request.
#
# ============================================================

predictor = RecoveryPredictor()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "RecoveryOS",
        "status": "running",
        "version": "0.1.0",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# HELPERS
# ============================================================

def get_policy(db: Session):
    policy = (
        db.query(MerchantPolicy)
        .first()
    )

    if policy is None:
        raise HTTPException(
            status_code=500,
            detail="Merchant policy not configured",
        )

    return policy


def load_customers(db: Session):
    return {
        customer.id: customer
        for customer in db.query(Customer).all()
    }


# ============================================================
# BATCH PAYMENT EVALUATION
# ============================================================
#
# IMPORTANT:
#
# All payments use the SAME decision engine.
#
# ML prediction is performed in ONE batch instead of
# calling the Random Forest once for every payment.
#
# ============================================================

def evaluate_payments_batch(
    customers,
    payments,
    policy,
):
    if not payments:
        return []

    valid_customers = []
    valid_payments = []

    for payment in payments:

        customer = customers.get(
            payment.customer_id
        )

        if customer is None:
            continue

        valid_customers.append(customer)
        valid_payments.append(payment)

    if not valid_payments:
        return []

    # --------------------------------------------------------
    # ONE ML PREDICTION FOR ALL PAYMENTS
    # --------------------------------------------------------

    ml_probabilities = (
        predictor.predict_probabilities(
            valid_customers,
            valid_payments,
        )
    )

    results = []

    # --------------------------------------------------------
    # USE THE SAME build_decision() FUNCTION THAT SINGLE
    # PAYMENT EVALUATION USES.
    #
    # This is the important consistency fix.
    # --------------------------------------------------------

    for customer, payment, ml_probability in zip(
        valid_customers,
        valid_payments,
        ml_probabilities,
    ):

        decision = build_decision(
            customer=customer,
            payment=payment,
            policy=policy,
            ml_probability=ml_probability,
        )

        results.append({
            "payment": payment,
            "customer": customer,
            "decision": decision,
        })

    return results


# ============================================================
# EVALUATE SINGLE PAYMENT
# ============================================================

@app.get(
    "/payments/{payment_code}/evaluate"
)
def evaluate_payment_endpoint(
    payment_code: str,
):
    db: Session = SessionLocal()

    try:

        # ----------------------------------------------------
        # FIND PAYMENT
        # ----------------------------------------------------

        payment = (
            db.query(Payment)
            .filter(
                Payment.payment_code == payment_code
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        # ----------------------------------------------------
        # FIND CUSTOMER
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == payment.customer_id
            )
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        # ----------------------------------------------------
        # LOAD POLICY
        # ----------------------------------------------------

        policy = get_policy(db)

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Use the GLOBAL predictor.
        #
        # DO NOT create:
        #
        # predictor = RecoveryPredictor()
        #
        # here.
        # ----------------------------------------------------

        decision = evaluate_hybrid(
            customer=customer,
            payment=payment,
            policy=policy,
            predictor=predictor,
        )

        print(
            f"EVALUATE: {payment.payment_code} | "
            f"Customer={customer.customer_code} | "
            f"Rules={decision.rules_probability:.4f} | "
            f"ML={decision.ml_probability:.4f} | "
            f"Hybrid={decision.hybrid_probability:.4f} | "
            f"Action={decision.action}",
            flush=True,
        )

        return {
            "payment_code": (
                payment.payment_code
            ),

            "customer_code": (
                customer.customer_code
            ),

            "amount": float(
                payment.amount
            ),

            "failure_reason": (
                payment.failure_reason
            ),

            "status": (
                payment.status
            ),

            "rules_probability": (
                decision.rules_probability
            ),

            "ml_probability": (
                decision.ml_probability
            ),

            "hybrid_probability": (
                decision.hybrid_probability
            ),

            "action": (
                decision.action
            ),

            "expected_value": (
                decision.expected_value
            ),

            "intervention_cost": (
                decision.intervention_cost
            ),

            "reason": (
                decision.reason
            ),

            "model": (
                predictor.model_name
            ),

            "model_version": (
                predictor.model_version
            ),
        }

    finally:
        db.close()


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get(
    "/dashboard/summary"
)
def dashboard_summary():

    db: Session = SessionLocal()

    try:

        print(
            "SUMMARY: START",
            flush=True,
        )

        # ----------------------------------------------------
        # POLICY
        # ----------------------------------------------------

        policy = get_policy(db)

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        customers = load_customers(db)

        # ----------------------------------------------------
        # FAILED PAYMENTS
        # ----------------------------------------------------

        payments = (
            db.query(Payment)
            .filter(
                Payment.status == "FAILED"
            )
            .all()
        )

        print(
            f"SUMMARY: {len(payments)} FAILED PAYMENTS",
            flush=True,
        )

        # ----------------------------------------------------
        # BATCH EVALUATION
        # ----------------------------------------------------

        evaluations = evaluate_payments_batch(
            customers=customers,
            payments=payments,
            policy=policy,
        )

        print(
            "SUMMARY: BATCH EVALUATION COMPLETE",
            flush=True,
        )

        # ----------------------------------------------------
        # TOTALS
        # ----------------------------------------------------

        total_failed_value = 0.0
        total_expected_value = 0.0
        total_intervention_cost = 0.0

        action_counts = {
            "SEND_PAYMENT_LINK": 0,
            "SEND_REMINDER": 0,
            "OFFER_RETRY": 0,
            "NO_ACTION": 0,
        }

        probability_sum = 0.0

        for item in evaluations:

            payment = item["payment"]
            decision = item["decision"]

            total_failed_value += float(
                payment.amount
            )

            total_expected_value += (
                decision.expected_value
            )

            total_intervention_cost += (
                decision.intervention_cost
            )

            action_counts[
                decision.action
            ] += 1

            probability_sum += (
                decision.hybrid_probability
            )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Use evaluated payment count rather than blindly
        # assuming every database payment had a customer.
        # ----------------------------------------------------

        payment_count = len(payments)

        average_probability = (
            probability_sum / len(evaluations)
            if evaluations
            else 0.0
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {
            "failed_payments": payment_count,

            "failed_payment_value": round(
                total_failed_value,
                2,
            ),

            "average_recovery_probability": round(
                average_probability,
                4,
            ),

            "expected_recovery_value": round(
                total_expected_value,
                2,
            ),

            "intervention_cost": round(
                total_intervention_cost,
                2,
            ),

            "net_expected_value": round(
                total_expected_value - total_intervention_cost,
                2,
            ),

            "actions": action_counts,

            "model": (
                predictor.model_name
            ),

            "model_version": (
                predictor.model_version
            ),
        }

    finally:
        db.close()


# ============================================================
# LIST FAILED PAYMENTS
# ============================================================

@app.get(
    "/payments"
)
def list_failed_payments():

    db: Session = SessionLocal()

    try:

        print(
            "PAYMENTS: START",
            flush=True,
        )

        # ----------------------------------------------------
        # POLICY
        # ----------------------------------------------------

        policy = get_policy(db)

        print(
            "PAYMENTS: POLICY LOADED",
            flush=True,
        )

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        customers = load_customers(db)

        print(
            f"PAYMENTS: CUSTOMERS LOADED: "
            f"{len(customers)}",
            flush=True,
        )

        # ----------------------------------------------------
        # FAILED PAYMENTS
        # ----------------------------------------------------

        payments = (
            db.query(Payment)
            .filter(
                Payment.status == "FAILED"
            )
            .order_by(
                Payment.id
            )
            .all()
        )

        print(
            f"PAYMENTS: PAYMENTS LOADED: "
            f"{len(payments)}",
            flush=True,
        )

        # ----------------------------------------------------
        # BATCH EVALUATION
        # ----------------------------------------------------

        evaluations = evaluate_payments_batch(
            customers=customers,
            payments=payments,
            policy=policy,
        )

        print(
            "PAYMENTS: BATCH ML EVALUATION COMPLETE",
            flush=True,
        )

        # ----------------------------------------------------
        # BUILD RESPONSE
        # ----------------------------------------------------

        results = []

        for item in evaluations:

            payment = item["payment"]
            customer = item["customer"]
            decision = item["decision"]

            results.append({

                "payment_code": (
                    payment.payment_code
                ),

                "customer_code": (
                    customer.customer_code
                ),

                "amount": float(
                    payment.amount
                ),

                "failure_reason": (
                    payment.failure_reason
                ),

                "rules_probability": (
                    decision.rules_probability
                ),

                "ml_probability": (
                    decision.ml_probability
                ),

                "hybrid_probability": (
                    decision.hybrid_probability
                ),

                "action": (
                    decision.action
                ),

                "expected_value": (
                    decision.expected_value
                ),

                "intervention_cost": (
                    decision.intervention_cost
                ),

                "reason": (
                    decision.reason
                ),
            })

        print(
            f"PAYMENTS: COMPLETE: "
            f"{len(results)} RESULTS",
            flush=True,
        )

        return {
            "count": len(results),
            "payments": results,
        }

    finally:
        db.close()


# ============================================================
# EXECUTE RECOVERY ACTION
# ============================================================

@app.post(
    "/payments/{payment_code}/execute"
)
def execute_recovery_action(
    payment_code: str,
):

    db: Session = SessionLocal()

    try:

        print(
            f"ACTION: START {payment_code}",
            flush=True,
        )

        # ----------------------------------------------------
        # FIND PAYMENT
        # ----------------------------------------------------

        payment = (
            db.query(Payment)
            .filter(
                Payment.payment_code == payment_code
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        # ----------------------------------------------------
        # FIND CUSTOMER
        # ----------------------------------------------------

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == payment.customer_id
            )
            .first()
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found",
            )

        # ----------------------------------------------------
        # POLICY
        # ----------------------------------------------------

        policy = get_policy(db)

        # ----------------------------------------------------
        # EVALUATE ONLY THIS PAYMENT
        #
        # Uses the SAME decision engine as:
        #
        # /payments
        # /dashboard/summary
        # /evaluate
        #
        # ----------------------------------------------------

                # ----------------------------------------------------
        # STOPPING RULE
        #
        # Maximum 3 executed recovery interventions
        # are allowed for one payment.
        # ----------------------------------------------------

        MAX_RECOVERY_ATTEMPTS = 3

        executed_attempts = (
            db.query(RecoveryEvent)
            .filter(
                RecoveryEvent.payment_id == payment.id,
                RecoveryEvent.executed == True,
            )
            .count()
        )

        print(
            f"ACTION: PREVIOUS EXECUTED ATTEMPTS "
            f"{executed_attempts}/{MAX_RECOVERY_ATTEMPTS}",
            flush=True,
        )

        if executed_attempts >= MAX_RECOVERY_ATTEMPTS:

            print(
                f"ACTION: STOPPING RULE REACHED "
                f"for {payment.payment_code}",
                flush=True,
            )

            return {
                "success": False,
                "payment_code": payment.payment_code,
                "customer_code": customer.customer_code,
                "action": "NO_ACTION",
                "executed": False,
                "outcome": "STOPPING_RULE_REACHED",
                "predicted_probability": 0.0,
                "expected_value": 0.0,
                "intervention_cost": 0.0,
                "recovered_amount": 0.0,
                "message": (
                    "Maximum recovery attempts "
                    "reached. No further intervention "
                    "will be executed."
                ),
                "reason": (
                    "Stopping rule reached: maximum "
                    "of 3 recovery interventions allowed."
                ),
            }

        # ----------------------------------------------------
        # EVALUATE ONLY THIS PAYMENT
        # ----------------------------------------------------

        decision = evaluate_hybrid(
            customer=customer,
            payment=payment,
            policy=policy,
            predictor=predictor,
        )

        print(
            f"ACTION: RECOMMENDED "
            f"{decision.action} | "
            f"Probability="
            f"{decision.hybrid_probability:.4f}",
            flush=True,
        )

        # ----------------------------------------------------
        # NO ACTION
        # ----------------------------------------------------

        if decision.action == "NO_ACTION":

            return {
                "success": False,

                "payment_code": (
                    payment.payment_code
                ),

                "action": "NO_ACTION",

                "executed": False,

                "message": (
                    "Recovery engine recommends "
                    "no intervention."
                ),

                "reason": (
                    decision.reason
                ),
            }

        # ----------------------------------------------------
        # CREATE RECOVERY EVENT
        # ----------------------------------------------------

        event = RecoveryEvent(

            payment_id=(
                payment.id
            ),

            action=(
                decision.action
            ),

            predicted_probability=(
                decision.hybrid_probability
            ),

            expected_value=(
                decision.expected_value
            ),

            executed=True,

            outcome="ACTION_EXECUTED",

            recovered_amount=0.0,

            intervention_cost=(
                decision.intervention_cost
            ),

            created_at=datetime.utcnow(),
        )

        db.add(event)

        db.commit()

        db.refresh(event)

        print(
            f"ACTION: EVENT CREATED "
            f"{event.id}",
            flush=True,
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Payment status remains FAILED.
        #
        # Executing an intervention does NOT mean the
        # payment has actually been recovered.
        #
        # ----------------------------------------------------

        return {

            "success": True,

            "event_id": (
                event.id
            ),

            "payment_code": (
                payment.payment_code
            ),

            "customer_code": (
                customer.customer_code
            ),

            "action": (
                decision.action
            ),

            "executed": True,

            "outcome": (
                event.outcome
            ),

            "predicted_probability": (
                decision.hybrid_probability
            ),

            "expected_value": (
                decision.expected_value
            ),

            "intervention_cost": (
                decision.intervention_cost
            ),

            "recovered_amount": 0.0,

            "message": (
                f"{decision.action} "
                "simulated successfully."
            ),

            "reason": (
                decision.reason
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        db.rollback()

        print(
            f"ACTION: ERROR {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to execute recovery action."
            ),
        )

    finally:
        db.close()


# ============================================================
# RECOVERY EVENT HISTORY
# ============================================================

@app.get(
    "/payments/{payment_code}/events"
)
def get_payment_recovery_events(
    payment_code: str,
):

    db: Session = SessionLocal()

    try:

        # ----------------------------------------------------
        # FIND PAYMENT
        # ----------------------------------------------------

        payment = (
            db.query(Payment)
            .filter(
                Payment.payment_code == payment_code
            )
            .first()
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        # ----------------------------------------------------
        # GET EVENTS
        # ----------------------------------------------------

        events = (
            db.query(RecoveryEvent)
            .filter(
                RecoveryEvent.payment_id == payment.id
            )
            .order_by(
                RecoveryEvent.created_at.desc()
            )
            .all()
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "payment_code": (
                payment.payment_code
            ),

            "count": len(events),

            "events": [

                {

                    "event_id": (
                        event.id
                    ),

                    "action": (
                        event.action
                    ),

                    "predicted_probability": (
                        event.predicted_probability
                    ),

                    "expected_value": (
                        event.expected_value
                    ),

                    "executed": (
                        event.executed
                    ),

                    "outcome": (
                        event.outcome
                    ),

                    "recovered_amount": (
                        event.recovered_amount
                    ),

                    "intervention_cost": (
                        event.intervention_cost
                    ),

                    "created_at": (
                        event.created_at.isoformat()
                        if event.created_at
                        else None
                    ),

                }

                for event in events
            ],
        }

    finally:
        db.close()