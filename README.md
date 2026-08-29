\# RecoveryOS



> Intelligent payment recovery decision system powered by rules, machine learning, and expected-value optimization.



RecoveryOS is a prototype payment recovery platform that evaluates failed payments and recommends the most appropriate recovery action.



The system combines:



\- Rule-based recovery probability

\- Machine-learning probability

\- Hybrid probability scoring

\- Merchant intervention-cost policies

\- Expected-value calculation

\- Recovery action recommendations

\- Recovery action execution

\- Recovery event history

\- A web dashboard for monitoring and analysis



\---



\## Overview



Failed payments do not all require the same recovery strategy.



A high-probability payment may justify sending a payment link, while another payment may only justify a reminder or retry. Some payments may not justify any intervention at all.



RecoveryOS attempts to make this decision systematically.



For every failed payment, the system evaluates the customer, payment, merchant policy, and machine-learning prediction to determine:



1\. Probability of recovery

2\. Recommended recovery action

3\. Intervention cost

4\. Expected recovery value

5\. Whether the intervention is economically justified



The core decision engine combines machine-learning and rule-based probabilities:



```text

Hybrid Probability

=

(ML Probability × 0.70)

\+

(Rules Probability × 0.30)

System Architecture

&#x20;                        ┌─────────────────────┐

&#x20;                        │     React / Vite     │

&#x20;                        │      Frontend        │

&#x20;                        └──────────┬──────────┘

&#x20;                                   │

&#x20;                                   │ HTTP / JSON

&#x20;                                   ▼

&#x20;                        ┌─────────────────────┐

&#x20;                        │       FastAPI       │

&#x20;                        │       Backend       │

&#x20;                        └──────────┬──────────┘

&#x20;                                   │

&#x20;                 ┌─────────────────┼─────────────────┐

&#x20;                 │                 │                 │

&#x20;                 ▼                 ▼                 ▼

&#x20;         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐

&#x20;         │ Rules Engine │  │ ML Predictor │  │ Merchant     │

&#x20;         │              │  │              │  │ Policy       │

&#x20;         └──────┬───────┘  └──────┬───────┘  └──────────────┘

&#x20;                │                 │

&#x20;                └────────┬────────┘

&#x20;                         ▼

&#x20;                ┌──────────────────┐

&#x20;                │  Hybrid Decision │

&#x20;                │      Engine      │

&#x20;                └────────┬─────────┘

&#x20;                         │

&#x20;                         ▼

&#x20;                ┌──────────────────┐

&#x20;                │ Recovery Actions │

&#x20;                └────────┬─────────┘

&#x20;                         │

&#x20;                         ▼

&#x20;                ┌──────────────────┐

&#x20;                │ Recovery Events  │

&#x20;                └──────────────────┘

Technology Stack

Backend

Python

FastAPI

SQLAlchemy

Scikit-learn

Joblib

Pytest

Frontend

React

Vite

JavaScript

CSS

Data

Customer records

Payment records

Merchant policies

Recovery events

ML training and testing datasets

Project Structure

recovery-os/

│

├── backend/

│   ├── app/

│   │   ├── database.py

│   │   ├── init\_db.py

│   │   ├── main.py

│   │   │

│   │   ├── models/

│   │   │   ├── customer.py

│   │   │   ├── merchant\_policy.py

│   │   │   ├── payment.py

│   │   │   └── recovery\_event.py

│   │   │

│   │   └── services/

│   │       ├── hybrid\_engine.py

│   │       ├── ml\_predictor.py

│   │       └── recovery\_engine.py

│   │

│   ├── ml/

│   │   ├── train\_model.py

│   │   ├── recovery\_model.joblib

│   │   └── data/

│   │       ├── train.csv

│   │       └── test.csv

│   │

│   └── tests/

│       ├── \_\_init\_\_.py

│       └── test\_hybrid\_engine.py

│

├── frontend/

│   ├── src/

│   │   ├── App.jsx

│   │   ├── App.css

│   │   └── index.css

│   ├── public/

│   ├── package.json

│   └── vite.config.js

│

├── simulator/

│   ├── generate\_data.py

│   ├── customers.csv

│   └── payments.csv

│

└── README.md

Recovery Decision Engine



RecoveryOS uses three major stages.



1\. Rules Probability



The rules engine calculates a recovery probability from customer and payment information.



Customer + Payment

&#x20;       │

&#x20;       ▼

&#x20;  Rules Engine

&#x20;       │

&#x20;       ▼

Rules Probability

2\. Machine Learning Probability



The ML predictor generates a probability estimate using the trained recovery model.



Customer + Payment

&#x20;       │

&#x20;       ▼

&#x20;   ML Model

&#x20;       │

&#x20;       ▼

ML Probability

3\. Hybrid Probability



The two probabilities are combined:



Hybrid Probability

=

(ML Probability × 0.70)

\+

(Rules Probability × 0.30)



The result is rounded to four decimal places.



Recovery Actions



The current decision thresholds are:



Hybrid Probability	Action

>= 0.65	SEND\_PAYMENT\_LINK

>= 0.40	SEND\_REMINDER

>= 0.20	OFFER\_RETRY

< 0.20	NO\_ACTION



The intervention costs are:



Action	Cost

SEND\_PAYMENT\_LINK	5.00

SEND\_REMINDER	2.00

OFFER\_RETRY	1.00

NO\_ACTION	0.00

Expected Value



RecoveryOS does not select an action based only on probability.



It also checks whether the intervention is economically justified.



Gross Expected Recovery

=

Payment Amount × Hybrid Probability

Expected Value

=

Gross Expected Recovery - Intervention Cost



If expected value is less than or equal to zero:



NO\_ACTION



is returned.



Merchant Cost Policy



The merchant can define a maximum intervention cost.



If the recommended intervention exceeds the merchant's configured limit, RecoveryOS blocks the intervention and returns:



NO\_ACTION

Backend API

Root

GET /

Health Check

GET /health

Dashboard Summary

GET /dashboard/summary



Returns aggregate information including:



Failed payment count

Failed payment value

Average recovery probability

Expected recovery value

Intervention cost

Action distribution

ML model information

Failed Payments

GET /payments



Returns failed payments and their recovery decisions.



Evaluate Payment

GET /payments/{payment\_code}/evaluate



Example:



GET /payments/PAY\_000001/evaluate

Execute Recovery

POST /payments/{payment\_code}/execute



Executes the recommended recovery action.



The current execution layer is simulated and records a recovery event.



Recovery Event History

GET /payments/{payment\_code}/events



Returns recovery events associated with a payment.



Frontend Dashboard



The React dashboard provides:



Failed payment metrics

Failed payment value

Average recovery probability

Expected recovery value

Recovery action distribution

ML model information

Failed payment table

Payment/customer search

Action filtering

Failure-reason filtering

Minimum/maximum amount filtering

Pagination



The current page size is:



50 payments

Payment Evaluation



Selecting a payment opens its evaluation panel.



The panel displays:



Payment amount

Hybrid probability

Recommended action

Rules probability

ML probability

Expected value

Intervention cost

Failure reason

Payment status

Model

Model version

Decision reason

Recovery Execution



For eligible payments, the dashboard provides:



Execute Recovery Action



After execution, the interface displays:



Execution status

Event ID

Action

Predicted probability



The payment's recovery event history is then refreshed.



Machine Learning



The trained recovery model is located at:



backend/ml/recovery\_model.joblib



Training data:



backend/ml/data/train.csv



Testing data:



backend/ml/data/test.csv



The current model should be considered a prototype model rather than a production-grade financial prediction system.



Testing



Backend tests are executed with:



cd backend

python -m pytest -q



Current test coverage includes:



70/30 ML and rules weighting

High-probability payment-link decisions

Medium-probability reminder decisions

Low-probability action behavior

Merchant cost-policy blocking



Current test result:



5 passed

Local Development

Start Backend

cd backend

uvicorn app.main:app --reload



Backend:



http://127.0.0.1:8000



FastAPI documentation:



http://127.0.0.1:8000/docs

Start Frontend



Open another terminal:



cd frontend

npm install

npm run dev

Production Build

cd frontend

npm run build



The production build is generated in:



frontend/dist/

Typical Recovery Workflow

Failed Payment

&#x20;     │

&#x20;     ▼

Load Customer + Payment

&#x20;     │

&#x20;     ├───────────────┐

&#x20;     ▼               ▼

Rules Engine       ML Model

&#x20;     │               │

&#x20;     ▼               ▼

Rules Probability   ML Probability

&#x20;     │               │

&#x20;     └───────┬───────┘

&#x20;             ▼

&#x20;      Hybrid Probability

&#x20;             │

&#x20;             ▼

&#x20;       Action Selection

&#x20;             │

&#x20;             ▼

&#x20;      Merchant Cost Check

&#x20;             │

&#x20;             ▼

&#x20;       Expected Value

&#x20;             │

&#x20;      ┌──────┴──────┐

&#x20;      ▼             ▼

&#x20;Positive EV      Non-positive EV

&#x20;      │             │

&#x20;      ▼             ▼

Recovery Action   NO\_ACTION

&#x20;      │

&#x20;      ▼

Recovery Event

Design Principles

Consistent Decision Logic



Payment evaluation should use the same decision engine regardless of whether it is evaluated individually or as part of a batch.



Economic Decision Making



Probability alone is not sufficient.



An intervention should also make financial sense.



Merchant Constraints



Merchant intervention-cost policies can override an otherwise recommended action.



Explainability



Every decision contains a reason explaining why the action was selected.



Event Tracking



Recovery actions are recorded as recovery events.



Current Status



RecoveryOS is a working prototype.



Implemented:



FastAPI backend

SQLAlchemy data models

Rules-based recovery probability

ML probability prediction

70/30 hybrid probability engine

Expected-value decisioning

Merchant intervention-cost policy

Batch payment evaluation

Payment evaluation API

Recovery execution simulation

Recovery event history

React dashboard

Payment search

Payment filters

Pagination

Hybrid-engine tests

Production frontend build

Prototype Limitations



RecoveryOS should not currently be treated as a production payment-recovery system.



The recovery execution layer is simulated.



The ML model is based on the current prototype dataset.



Before production deployment, the system would require additional work around:



Authentication and authorization

Secure API deployment

Real payment-provider integrations

Real messaging integrations

Model validation

Model monitoring

Data-quality monitoring

Production database configuration

Observability

Rate limiting

Audit and security controls

Retry and failure handling

Privacy and compliance

Automated integration testing

Project Goal



The long-term goal of RecoveryOS is to evolve from a recovery decision engine into an intelligent recovery orchestration platform.



Predict

&#x20;  ↓

Decide

&#x20;  ↓

Optimize

&#x20;  ↓

Execute

&#x20;  ↓

Measure

&#x20;  ↓

Learn

License



This project is currently a private development prototype.





\## Step 2 — Save



In Notepad:



\*\*Ctrl + S\*\*



Then close Notepad.



\## Step 3 — Verify README exists



In PowerShell, you should still be here:



```text

C:\\Users\\ayank\\recovery-os



Run:



Get-Item .\\README.md



Then:



Get-Content .\\README.md | Select-Object -First 10

Step 4 — Run tests

cd .\\backend

python -m pytest -q



Expected:



5 passed

Step 5 — Build frontend

cd ..\\frontend

npm run build



Expected:



✓ built

