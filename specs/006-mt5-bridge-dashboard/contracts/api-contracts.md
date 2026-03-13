# API Contracts: MT5 Bridge Dashboard

This document records the operator-facing bridge surface currently exercised by
the dashboard and contract tests.

## Read Endpoints

- `GET /account`
- `GET /positions`
- `GET /orders`
- `GET /tick/{ticker}`
- `GET /terminal`
- `GET /history/deals`
- `GET /history/orders`
- `GET /broker-symbols`

## Write Endpoints

- `POST /close-position`
- `DELETE /orders/{ticket}`
- `PUT /positions/{ticket}/sltp`
- `PUT /orders/{ticket}`
- `POST /pending-order`
- `POST /order-check`
