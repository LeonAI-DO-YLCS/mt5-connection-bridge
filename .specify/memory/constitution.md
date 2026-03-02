<!--
  Sync Impact Report
  Version change: 1.0.0 → 1.1.0
  Modified principles:
    - II. Educational and Research Guardrails → II. Trading Modes & Execution Safety
    - V. Modular and Extensible Architecture → V. Execution & Connection Frameworks
  Added sections:
    - VI. MT5 Connection Framework
  Removed sections: None
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ updated
    - .specify/templates/spec-template.md ✅ updated
    - .specify/templates/tasks-template.md ✅ updated
  Follow-up TODOs: None
-->

# AI Hedge Fund Constitution

## Core Principles

### I. Multi-Agent Orchestration

The system MUST utilize a diverse set of specialized agents (e.g., Valuation, Sentiment, Risk Manager) that collaborate to reach trading decisions. Each agent MUST have a clearly defined role, logic, and output format. Orchestration should leverage LangGraph to manage state and complex transition logic.

### II. Trading Modes & Execution Safety

The system supports three operational modes: Demo/Educational, Paper Trading, and Real Account Execution.

- **Demo Mode**: No external execution; strictly for UI/Logic validation.
- **Paper Trading**: Virtual execution via live market data; used for strategy validation in live conditions.
- **Real Account**: Live capital execution. This mode MUST require explicit, multi-factor confirmation or high-level environment variables to activate.
  Security and audit logs MUST be maintained for all execution modes.

### III. Data-Driven Valuation

Trading signals MUST be derived from rigorous analysis of financial data, market sentiment, and fundamental indicators. Implementation MUST prioritize data integrity and traceable decision-making. "Story" and "Numbers" (as per the Damodaran model) must be explicitly balanced in valuation agents.

### IV. Risk-Managed Decision Making

Every trading decision MUST pass through a dedicated Risk Manager agent. This agent MUST enforce position limits, diversification rules, and risk metrics (e.g., VaR) before any order is generated. The Portfolio Manager is the final authority but MUST NOT override Risk Manager vetoes without documented justification.

### V. Execution & Connection Frameworks

The architecture MUST support pluggable execution frameworks. Connectivity to brokers and exchanges MUST be isolated in dedicated adapter modules. Failure handling (e.g., disconnection, API timeouts) MUST be implemented with automatic retry or safe-halt protocols.

### VI. MT5 Connection Framework

The system MUST integrate with MetaTrader 5 (MT5) for order execution and market data retrieval.

- The MT5 adapter MUST handle connection persistence, symbol management, and real-time tick/bar data streaming.
- Order execution MUST include slippage protection and definitive confirmation of fill status before state updates.
- Technical indicators calculated within MT5 SHOULD be accessible as signals for the Technicals Agent.

## Technology Stack & Standards

Core Logic: Python 3.11+, LangChain, LangGraph.
Backend: FastAPI.
Frontend: React, Vite, Tailwind CSS.
Execution: MetaTrader 5 (MT5) Python API.
Dependency Management: Poetry.
Documentation: OpenSpec via Specify CLI.

## Development & Contribution Workflow

Contributions MUST follow a structured workflow: Specification → Implementation Plan → Tasks → Implementation. All work MUST be done on feature branches. The `main` branch MUST be backed up to `guardian-state` after every successful merge. Pull requests SHOULD be small, focused, and include unit/integration tests where applicable.

## Governance

This constitution supersedes all other development practices within the AI Hedge Fund project. Amendments require a formal change proposal and a version bump. All new features and documentation MUST be validated against these core principles during the `plan` and `tasks` phases.

**Version**: 1.1.0 | **Ratified**: 2026-03-01 | **Last Amended**: 2026-03-01
