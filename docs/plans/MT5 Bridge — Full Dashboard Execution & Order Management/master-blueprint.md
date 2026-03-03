# Master Blueprint: MT5 Bridge — Full Dashboard Execution & Order Management

> **Status**: Phased Roadmap — Derived from monolithic blueprint
> **Goal**: Provide a sequentially executable roadmap for full bridge and dashboard operability.
> **Original Document**: [dashboard-full-execution-blueprint.md](../dashboard-full-execution-blueprint.md)
> **Date**: 2026-03-02

---

## 1. High-Level Roadmap

This blueprint has been split into 5 phases, each building the foundation for the next.

| Phase | Resource                                           | Goal                                                      | Risk     |
| :---- | :------------------------------------------------- | :-------------------------------------------------------- | :------- |
| **0** | [0-foundations.md](./0-foundations.md)             | Shared models, mappers, documentation & safety layers.    | Low      |
| **1** | [1-visibility.md](./1-visibility.md)               | Read-only visibility: positions, orders, account status.  | Low      |
| **2** | [2-management.md](./2-management.md)               | Lifecycle control: close positions, cancel/modify orders. | Medium   |
| **3** | [3-execution.md](./3-execution.md)                 | Full placement: pending orders & pre-validation.          | Med-High |
| **4** | [4-history-discovery.md](./4-history-discovery.md) | Analytics: MT5 history & broker symbol discovery.         | Low      |

---

## 2. Current State & Gap Analysis

_Extracted from monolithic blueprint Section 1 & 2._

### What the Bridge Can Do (API)

| Endpoint   | Method | Purpose                                       |
| :--------- | :----- | :-------------------------------------------- |
| `/health`  | GET    | Terminal status, broker, latency              |
| `/prices`  | GET    | Historical OHLCV candles                      |
| `/execute` | POST   | **Market orders only** (buy/sell/short/cover) |

### Gaps Summary (🔴 Critical)

| #   | Gap                       | Impact                                                  |
| :-- | :------------------------ | :------------------------------------------------------ |
| G1  | No positions endpoint     | Can't see what's currently open                         |
| G2  | No close position         | Can't exit trades from dashboard                        |
| G3  | No pending order creation | Can't place limit/stop orders                           |
| G4  | No pending orders list    | Can't see or manage pending orders                      |
| G5  | No order cancellation     | Can't cancel pending orders                             |
| G6  | No SL/TP on market orders | Can't set risk management on execution                  |
| G7  | No position modification  | Can't update SL/TP after position is open               |
| G8  | Execute tab is minimal    | Missing lots dropdown, price limit, order type selector |
| G9  | No account balance panel  | Dashboard can't show equity/margin/free margin          |

---

## 3. Project Summary

The bridge currently operates at **~30% of MT5's capabilities**. After completing all phases, it will reach **~98%** coverage.

### By the Numbers

- **15 new API endpoints**
- **3 new dashboard tabs** (Positions, Orders, Trade History)
- **1 rebuilt dashboard tab** (Execute)
- **7-layer safety architecture**
