import os

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.database import SessionLocal


MODEL_PATH = "ml/recovery_model.joblib"


def load_data():
    db = SessionLocal()

    try:
        query = text(
            """
            SELECT
                p.payment_code,
                p.amount,
                p.payment_method,
                p.failure_reason,
                c.segment,
                c.lifetime_value,
                c.orders_count,
                c.successful_payments,
                c.failed_payments,
                c.previous_recovery_success,
                c.contact_count
            FROM payments p
            JOIN customers c
                ON p.customer_id = c.id
            WHERE p.status = 'FAILED'
            """
        )

        df = pd.read_sql(query, db.bind)

    finally:
        db.close()

    return df


def create_recovery_outcome(df):
    rng = np.random.default_rng(42)

    probability = (
        0.20
        + 0.35 * df["previous_recovery_success"]
        + 0.08 * (df["segment"] == "reliable")
        + 0.06 * (df["segment"] == "high_value")
        + 0.04 * (df["segment"] == "occasional")
        - 0.12 * (df["segment"] == "frequent_failure")
        - 0.10 * (df["segment"] == "unresponsive")
        - 0.08 * (df["segment"] == "price_sensitive")
        - 0.08 * (df["failure_reason"] == "AUTHENTICATION_FAILED")
        - 0.06 * (df["failure_reason"] == "BANK_DECLINED")
        + 0.05 * (df["failure_reason"] == "BANK_TIMEOUT")
        + 0.03 * (df["failure_reason"] == "NETWORK_ERROR")
        - 0.04 * (df["failed_payments"] >= 3)
        + 0.03 * (df["contact_count"] == 0)
    )

    probability = probability.clip(0.02, 0.95)

    df["recovery_probability_target"] = probability

    df["recovered"] = (
        rng.random(len(df)) < probability
    ).astype(int)

    return df


def prepare_features(df):
    features = df[
        [
            "amount",
            "payment_method",
            "failure_reason",
            "segment",
            "lifetime_value",
            "orders_count",
            "successful_payments",
            "failed_payments",
            "previous_recovery_success",
            "contact_count",
        ]
    ].copy()

    target = df["recovered"]

    categorical_columns = [
        "payment_method",
        "failure_reason",
        "segment",
    ]

    features = pd.get_dummies(
        features,
        columns=categorical_columns,
        dtype=int,
    )

    return features, target


def main():
    print("RecoveryOS ML model training")
    print("----------------------------")

    df = load_data()

    print(f"Failed payments loaded: {len(df)}")

    df = create_recovery_outcome(df)

    print(
        f"Synthetic recovery rate: "
        f"{df['recovered'].mean() * 100:.2f}%"
    )

    features, target = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.20,
        random_state=42,
        stratify=target,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
    )

    print("\nTraining Random Forest...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    auc = roc_auc_score(
        y_test,
        probabilities,
    )

    print("\nModel evaluation")
    print("----------------")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"ROC-AUC:  {auc:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
        )
    )

    feature_importance = pd.Series(
        model.feature_importances_,
        index=features.columns,
    ).sort_values(
        ascending=False
    )

    print("\nTop feature importance:")
    print(feature_importance.head(10))

    os.makedirs("ml", exist_ok=True)

    model_package = {
        "model": model,
        "features": list(features.columns),
        "model_name": "RecoveryOS Random Forest",
        "model_version": "0.1.0",
        "target": "synthetic_recovery_outcome",
        "training_rows": len(X_train),
        "testing_rows": len(X_test),
        "roc_auc": round(auc, 4),
        "accuracy": round(accuracy, 4),
    }

    joblib.dump(
        model_package,
        MODEL_PATH,
    )

    print(
        f"\nModel saved to: {MODEL_PATH}"
    )


if __name__ == "__main__":
    main()