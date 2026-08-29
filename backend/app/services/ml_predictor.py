import os

import joblib
import pandas as pd


MODEL_PATH = os.path.join(
    "ml",
    "recovery_model.joblib",
)


class RecoveryPredictor:
    def __init__(self, model_path=MODEL_PATH):
        package = joblib.load(model_path)

        self.model = package["model"]
        self.features = package["features"]

        self.model_name = package.get(
            "model_name",
            "RecoveryOS Random Forest",
        )

        self.model_version = package.get(
            "model_version",
            "unknown",
        )

    def _build_dataframe(self, customers, payments):
        """
        Build one pandas DataFrame for multiple payments.

        This avoids creating a DataFrame and running
        get_dummies() separately for every payment.
        """

        rows = []

        for customer, payment in zip(
            customers,
            payments,
        ):
            rows.append({
                "amount": float(payment.amount),

                "payment_method": (
                    payment.payment_method
                ),

                "failure_reason": (
                    payment.failure_reason
                ),

                "segment": customer.segment,

                "lifetime_value": float(
                    customer.lifetime_value
                ),

                "orders_count": int(
                    customer.orders_count
                ),

                "successful_payments": int(
                    customer.successful_payments
                ),

                "failed_payments": int(
                    customer.failed_payments
                ),

                "previous_recovery_success": float(
                    customer.previous_recovery_success
                ),

                "contact_count": int(
                    customer.contact_count
                ),
            })

        df = pd.DataFrame(rows)

        categorical_columns = [
            "payment_method",
            "failure_reason",
            "segment",
        ]

        df = pd.get_dummies(
            df,
            columns=categorical_columns,
            dtype=int,
        )

        df = df.reindex(
            columns=self.features,
            fill_value=0,
        )

        return df

    def predict_probability(
        self,
        customer,
        payment,
    ):
        """
        Predict probability for one payment.

        Kept for compatibility with the existing
        single-payment evaluation endpoint.
        """

        df = self._build_dataframe(
            [customer],
            [payment],
        )

        probability = self.model.predict_proba(
            df
        )[0][1]

        return round(
            float(probability),
            4,
        )

    def predict_probabilities(
        self,
        customers,
        payments,
    ):
        """
        Predict probabilities for many payments
        in one Random Forest call.
        """

        if not payments:
            return []

        if len(customers) != len(payments):
            raise ValueError(
                "customers and payments must have "
                "the same length"
            )

        df = self._build_dataframe(
            customers,
            payments,
        )

        probabilities = (
            self.model.predict_proba(df)[:, 1]
        )

        return [
            round(float(probability), 4)
            for probability in probabilities
        ]