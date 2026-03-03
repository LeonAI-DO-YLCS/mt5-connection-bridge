# Phase 6: Dashboard Operator Experience

> Objective: Make the dashboard behave like an operational control plane instead of a raw API demo surface.

---

## 1. Problem This Phase Solves

The dashboard currently provides many capabilities but still relies on generic browser prompts and raw error strings.  
This phase aligns UX with operations:

1. clear state
2. clear blockers
3. clear next actions
4. fast support escalation with tracking IDs

---

## 2. UX Model

### 2.1 Message center

Introduce a centralized message system replacing direct `alert/confirm/prompt` reliance for critical flows.

Required traits:

1. consistent visual semantics by category and severity
2. concise primary copy
3. expandable technical details
4. tracking ID copy shortcut

### 2.2 Readiness panel

Per-action readiness panel in relevant tabs:

- Execute
- Positions (close/modify)
- Orders (cancel/modify)

### 2.3 Operator timeline

Recent operation timeline with:

- action
- outcome
- code
- tracking ID
- timestamp

---

## 3. Decision Matrix: UX Transformation Depth

| Option | Description | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Minimal text polish only | Fast | Does not fix supportability | No |
| B | Full app redesign | Potentially cleaner | Unnecessary risk and effort | No |
| C | Targeted operational UX refactor in existing dashboard architecture | High impact, low architecture risk | Requires disciplined incremental work | **Recommended** |

---

## 4. Required UX Enhancements

1. Standardized confirmation modals with contextual risk copy.
2. Inline validation and remediation hints before submit.
3. Sticky connection/readiness banner with blocker summaries.
4. “Copy support package” action containing:
   - tracking ID
   - operation metadata
   - key readiness statuses.
5. Friendly fallback copy for all known MT5 failure classes.

---

## 5. Accessibility and Operator Efficiency

1. Keyboard-navigable dialogs and forms.
2. Clear color and icon semantics with text fallback.
3. No critical information conveyed by color alone.
4. Copyable references in one click for support handoff.

---

## 6. Exit Criteria

1. Critical operations can be completed without reading raw JSON.
2. Operator can understand “why failed” and “what next” immediately.
3. Support can resolve incidents from tracking IDs and message codes.

