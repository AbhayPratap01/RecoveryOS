# RecoveryOS

**AI-Powered Payment Recovery Decision Engine**

RecoveryOS is an intelligent payment recovery platform that analyzes
failed payment transactions, estimates the probability of success for
multiple recovery strategies, applies policy constraints, selects the
best allowed action, executes the recovery strategy, and maintains a
complete audit trail.

The system combines **machine learning + policy enforcement + recovery
execution + auditability** into one end-to-end workflow.

------------------------------------------------------------------------

## 🚀 Live Demo

**Frontend:**\
https://recovery-os-pi.vercel.app

**Backend API:**\
https://recoveryos-api-eey6.onrender.com

**API Documentation:**\
https://recoveryos-api-eey6.onrender.com/docs

------------------------------------------------------------------------

## 🎯 Problem

Failed payments are not all the same.

A payment may fail because of:

-   Bank decline
-   Network error
-   Expired card
-   Other transaction-specific failure conditions

A simple "always retry" strategy can waste recovery attempts and provide
a poor customer experience.

RecoveryOS instead evaluates the transaction context and estimates which
recovery strategy is most likely to succeed.

The available recovery strategies include:

-   **Retry** --- attempt the payment again
-   **Payment Link** --- provide an alternate payment path
-   **Reminder** --- prompt the customer to retry later

The selected action is then checked against policy constraints before
execution.

------------------------------------------------------------------------

## 🧠 How RecoveryOS Works

``` text
Failed Payment
      │
      ▼
Transaction Features
      │
      ▼
ML Recovery Probability Model
      │
      ├── Retry Probability
      ├── Payment Link Probability
      └── Reminder Probability
      │
      ▼
Policy Engine
      │
      ▼
Best Allowed Recovery Action
      │
      ▼
Recovery Execution
      │
      ▼
Result
      │
      ▼
Audit Event
```

This creates a complete:

**Decision → Policy → Execution → Audit**

pipeline.

------------------------------------------------------------------------

## ✨ Key Features

### 1. AI-Based Recovery Recommendation

For every failed transaction, RecoveryOS evaluates multiple recovery
actions and produces a probability for each action.

Example:

``` text
Retry          47.87%
Payment Link   36.66%
Reminder       32.69%

Recommended Action: Retry
```

The system selects the highest-scoring action that is allowed by policy.

------------------------------------------------------------------------

### 2. Policy-Aware Decision Making

The ML model does not directly control execution.

The selected strategy passes through a policy layer that determines
whether the action is permitted.

``` text
ML Recommendation
       ↓
Policy Check
       ↓
Allowed? ── No ──> Reject / Consider another action
       │
      Yes
       ↓
Execute
```

This separation makes the decision engine safer and easier to audit.

------------------------------------------------------------------------

### 3. Random Transaction Testing

The Overview page includes a **Random Transaction** option.

Instead of requiring a tester to know the transaction IDs contained in
the dataset, the application can load a transaction from the CSV dataset
and populate the form automatically.

This allows a tester to quickly demonstrate different transaction
scenarios.

------------------------------------------------------------------------

### 4. Recovery Execution

After analysis, the selected recovery strategy can be executed through
the backend.

The execution result records whether the recovery was successful and,
when applicable, the amount recovered.

------------------------------------------------------------------------

### 5. Complete Audit Trail

Every important decision can be traced through the audit system.

The Audit Trail records information such as:

-   Transaction ID
-   Timestamp
-   Recovery probabilities
-   Preferred action
-   Final action
-   Policy decision
-   Policy reasons
-   Rejected actions
-   Execution result
-   Recovery status
-   Amount recovered
-   Audit ID

The audit interface allows a tester to select available audited
transactions or manually enter a transaction ID.

------------------------------------------------------------------------

### 6. Analytics Dashboard

The Analytics page presents recovery intelligence including:

-   Transactions evaluated
-   Recovery rate
-   Payments recovered
-   Recovered revenue
-   Recovery strategy performance
-   Policy sensitivity
-   Failure-reason analysis

These visualizations provide a high-level view of model and policy
performance.

------------------------------------------------------------------------

## 🏗️ Project Structure

``` text
RecoveryOS/
│
├── backend/
│   ├── __init__.py
│   ├── api.py
│   ├── audit.py
│   ├── data_generator.py
│   ├── decision_engine.py
│   ├── evaluation.py
│   ├── executor.py
│   ├── intervention_model.py
│   ├── ml_dataset.py
│   ├── policy_engine.py
│   └── simulator.py
│
├── data/
│   └── transaction dataset / supporting data
│
├── experiments/
│   └── model evaluation and experimentation files
│
├── frontend/
│   ├── index.html
│   ├── audit.html
│   ├── analytics.html
│   ├── app.js
│   ├── analytics.js
│   ├── audit.js
│   ├── style.css
│   └── data/
│       └── analytics CSV files
│
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

------------------------------------------------------------------------

## 🔌 API Endpoints

The backend is implemented using FastAPI.

### Health

``` http
GET /health
```

Checks whether the recovery engine is running.

------------------------------------------------------------------------

### Get Transactions

``` http
GET /transactions
```

Returns available transactions from the dataset.

------------------------------------------------------------------------

### Get Random Transaction

``` http
GET /transactions/random
```

Returns a randomly selected transaction for testing and demonstration.

------------------------------------------------------------------------

### Get Transaction

``` http
GET /transactions/{transaction_id}
```

Returns a specific transaction.

Example:

``` text
GET /transactions/txn_001212
```

------------------------------------------------------------------------

### Analyze Transaction

``` http
POST /analyze
```

Analyzes a failed payment and returns:

-   Recovery probabilities
-   Preferred action
-   Final action
-   Decision score
-   Policy result
-   Rejected actions
-   Audit ID

------------------------------------------------------------------------

### Execute Recovery

``` http
POST /execute
```

Executes the selected recovery strategy and records the execution
result.

------------------------------------------------------------------------

### Get Audit Log

``` http
GET /audit
```

Returns available audit events.

------------------------------------------------------------------------

### Get Transaction Audit

``` http
GET /audit/{transaction_id}
```

Returns the audit history for a specific transaction.

Example:

``` text
GET /audit/txn_001212
```

------------------------------------------------------------------------

### Get Analytics

``` http
GET /analytics
```

Returns analytics used by the dashboard.

------------------------------------------------------------------------

## 🧪 Example Workflow

A typical test can be performed as follows.

### Step 1 --- Open Overview

Open the deployed frontend and select:

**Random Transaction**

The application loads a real transaction from the dataset.

### Step 2 --- Analyze

Click:

**Analyze Payment**

The backend evaluates the transaction and calculates the probability of
success for each recovery strategy.

### Step 3 --- Review Recommendation

The UI displays:

``` text
Recommended Action
Recovery Probability
Policy Status
AI Explanation
```

### Step 4 --- Execute

Click:

**Execute Recovery**

The backend executes the selected action.

### Step 5 --- Inspect Audit

Open:

**Audit Trail**

The executed transaction becomes available in the audited transaction
list.

Select the transaction to view its complete decision and execution
history.

### Step 6 --- Review Analytics

Open:

**Analytics**

Review the overall recovery performance and strategy/policy
intelligence.

------------------------------------------------------------------------

## 🛠️ Tech Stack

### Backend

-   Python
-   FastAPI
-   Pydantic
-   Pandas
-   Scikit-learn / ML components
-   Uvicorn

### Frontend

-   HTML
-   CSS
-   JavaScript
-   Chart-based analytics UI

### Data

-   CSV-based transaction dataset
-   Evaluation and analytics datasets

### Deployment

-   Frontend: Vercel
-   Backend: Render

------------------------------------------------------------------------

## 💻 Running Locally

### 1. Clone the repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd RecoveryOS
```

### 2. Create a virtual environment

Windows:

``` bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy:

``` text
.env.example
```

to:

``` text
.env
```

and configure the required values.

### 5. Start the backend

From the project root:

``` bash
uvicorn backend.api:app --reload
```

The API will be available at:

``` text
http://127.0.0.1:8000
```

Swagger documentation:

``` text
http://127.0.0.1:8000/docs
```

### 6. Start the frontend

The frontend can be served using a local static server such as VS Code
Live Server.

Open:

``` text
frontend/index.html
```

The frontend should point to the local API during local development.

------------------------------------------------------------------------

## 🔍 Testing

The project includes a `tests/` directory for backend testing.

A basic end-to-end test should verify:

``` text
Transaction
    ↓
Analysis
    ↓
Policy
    ↓
Execution
    ↓
Audit
```

You can also test the API interactively through FastAPI Swagger:

``` text
/docs
```

------------------------------------------------------------------------

## 📊 Example Decision

For a transaction, the model may produce:

``` text
Retry          47.87%
Payment Link   36.66%
Reminder       32.69%
```

The decision engine evaluates these probabilities together with the
policy constraints.

If Retry is permitted:

``` text
Preferred Action: Retry
Policy: Approved
Final Action: Retry
```

The resulting execution is then added to the audit trail.

------------------------------------------------------------------------

## 🔐 Auditability

A central design principle of RecoveryOS is that the ML model should not
be treated as an opaque final authority.

The system separates:

``` text
Prediction
    ↓
Decision
    ↓
Policy
    ↓
Execution
    ↓
Audit
```

This makes it possible to inspect not only **what** action was selected,
but also the recovery probabilities, policy decision, execution result,
and transaction history associated with that decision.

------------------------------------------------------------------------

## 📈 Analytics Philosophy

RecoveryOS evaluates recovery performance at multiple levels:

### Strategy Level

Which recovery strategy performs better?

``` text
Always Retry
Rule Based
ML Only
RecoveryOS
```

### Policy Level

How does changing policy strictness affect recovery?

``` text
Relaxed
Current
Strict
```

### Failure Level

Which payment failure conditions are more recoverable?

This allows the system to move beyond simply predicting an action and
instead provide operational intelligence around payment recovery.

------------------------------------------------------------------------

## 🎥 Recommended Demo Flow

For a short project demonstration:

``` text
1. Open Overview
        ↓
2. Click Random Transaction
        ↓
3. Analyze Payment
        ↓
4. Show AI recommendation + probabilities
        ↓
5. Show Policy Check
        ↓
6. Execute Recovery
        ↓
7. Open Audit Trail
        ↓
8. Select the transaction
        ↓
9. Show Decision → Policy → Execution history
        ↓
10. Open Analytics
```

This demonstrates the complete RecoveryOS pipeline in a few minutes.

------------------------------------------------------------------------

## 📌 Project Status

**Status: Working / Demo Ready**

Implemented:

-   [x] Transaction analysis
-   [x] ML recovery probabilities
-   [x] Recovery strategy selection
-   [x] Policy validation
-   [x] Recovery execution
-   [x] Random transaction testing
-   [x] Audit logging
-   [x] Transaction audit lookup
-   [x] Analytics dashboard
-   [x] Local testing
-   [x] Frontend deployment
-   [x] Backend deployment

------------------------------------------------------------------------

## 👥 Project

**RecoveryOS --- AI-Powered Payment Recovery Decision Engine**

Built as an end-to-end intelligent recovery system combining machine
learning, policy-aware decision making, execution, and auditability.
