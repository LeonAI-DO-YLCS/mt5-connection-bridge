# MT5 Bridge Development Blueprint — Current State

This blueprint outlines the current state of the **MT5 Connection Bridge**, focusing on the work completed during the **Phase 7 (Native Parity & Conformance)** transition and the critical gaps that remain to reach 100% completion and 90% test coverage.

## 🏗️ Current Project Status: Phase 7
We are currently synchronizing the bridge's capabilities with native MetaTrader 5 features while formalizing the API response structure. 

### **Completed Accomplishments**
1.  **Canonical Message Normalization**:
    *   Successfully migrated the entire API to the `MessageEnvelope` format. All responses (success and error) now include structured metadata: `code`, `category`, `title`, `message`, `action`, and `tracking_id`.
    *   Updated the global exception handlers in `app/main.py` to automatically wrap standard `HTTPException` and `RequestValidationError` into this format.
2.  **Safety & Parity Endpoints (US1 & US2)**:
    *   Implemented "Safe Domain" calculation endpoints: `/margin-check` and `/profit-calc`.
    *   Implemented the **Advanced Namespace** (`/mt5/raw/`): terminal-info, account-info, last-error, and market-book. These provide raw, unvalidated access to MT5 for power users.
3.  **Test Suite Stabilization**:
    *   Fixed widespread test failures caused by the transition to `MessageEnvelope` assertions.
    *   Resolved **test contamination** issues where one test would mutate the high-level API Key singleton and break all subsequent tests.
    *   Hardened the test runner to handle non-Windows environments (WSL) gracefully by skipping launcher and MT5-native contract tests that require a local Windows terminal.

---

## 🚩 Remaining Gaps

### **1. Conformance Harness (US4)**
The most significant implementation gap is the **Conformance CLI**. We need a way to verify that the bridge behaves correctly when connected to different brokers.
*   **Missing**: `app/conformance/` logic.
*   **Required Components**:
    *   `app/conformance/runner.py`: Orchestrates probe execution.
    *   **Probes**: Connection, Symbols, Pricing, and Calculations probes to verify broker-specific variances.
    *   **Reporter**: A tool to generate `conformance.json` and a Markdown recommendation report.

### **2. Governance & Matrix (US5)**
The bridge now surfaces "Raw" MT5 endpoints which are potentially dangerous. We lack the machine-readable governance required to approve them for production.
*   **Missing Files**: `config/governance-checklist.yaml` and `config/parity-coverage-matrix.yaml`.
*   **Required Actions**: 
    *   Populate the governance checklist with safety classes for every raw endpoint.
    *   Complete the parity matrix to track which MT5 features are fully implemented vs. proxied.
    *   Implement `scripts/validate_governance.py` to block CI/CD if an endpoint isn't documented.

### **3. The Coverage Gap (87% → 90%)**
Current coverage is **87.27%**. We are short of the mandatory **90% threshold**.
*   **Critical Hotspots**:
    *   `app/routes/orders.py` (76% coverage): Needs edge-case testing for complex order modifications.
    *   `app/services/readiness.py` (77% coverage): Needs deeper validation of tick-freshness logic.
    *   `app/routes/positions.py` (78% coverage): Needs tests for different `trade_mode` restrictions.

### **4. Missing Contract Documentation**
Several tests are currently **SKIPPED** because they look for specification files that haven't been generated:
*   `specs/001-mt5-bridge-dashboard/contracts/openapi.yaml`
*   `specs/006-mt5-bridge-dashboard/contracts/api-contracts.md`

---

## 🚀 Immediate Next Steps
1.  **Generate Governance YAMLs**: Create the missing config files so the governance validation can pass.
2.  **Targeted Unit Tests**: Add unit tests focusing specifically on the uncovered branches in `orders.py` and `readiness.py`.
3.  **Implement Conformance Probes**: Begin coding the connection and pricing probes in `app/conformance/`.
