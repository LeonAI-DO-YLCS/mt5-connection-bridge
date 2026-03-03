# Document Contracts: Phase 0 — Baseline and Constraints

**Branch**: `009-phase0-baseline-and-constraints`
**Date**: 2026-03-03
**Purpose**: Define the required structure and validation rules for each Phase 0 deliverable.

---

## 1. Glossary Contract (`docs/baseline/glossary.md`)

### Required Sections

1. **Header**: Title, snapshot date, last-reviewed date
2. **Core Terms Table**: columns — Term, Definition, Example Trigger, Dashboard Treatment
3. **Severity Scale Table**: columns — Level, Criteria, Action Required, Example
4. **Usage Notes**: How to apply the glossary when categorizing new events

### Validation Rules

- Must define exactly 6 core terms: `error`, `warning`, `status`, `advice`, `blocker`, `recovery`
- Must define exactly 4 severity levels: `low`, `medium`, `high`, `critical`
- Every cell must be non-empty (no TBD or N/A allowed)
- Examples must reference real codebase scenarios

---

## 2. Tracking ID Policy Contract (`docs/baseline/tracking-id-policy.md`)

### Required Sections

1. **Format Specification**: Pattern, character constraints, length
2. **Generation Rules**: When IDs are generated, by which component
3. **Propagation Path**: Backend log → response header → dashboard display (with header name)
4. **Log Correlation Guide**: Step-by-step: given a tracking ID from a screenshot, how to find the log entry

### Validation Rules

- Format must produce IDs ≤ 30 characters
- Must specify the exact response header name for propagation
- Must include a worked example with a real log lookup

---

## 3. Error-Code Namespace Contract (`docs/baseline/error-code-namespace.md`)

### Required Sections

1. **Naming Convention**: Pattern, allowed domain prefixes
2. **Initial Code Registry**: Table with — Code, Domain, Description, HTTP Status, Severity, Phase Introduced
3. **Governance Rules**: How to add new codes, collision prevention, deprecation process
4. **Minimum Required Codes**: Must cover 5 failure categories (validation, connectivity, policy, compatibility, fallback)

### Validation Rules

- No two codes may have the same semantic meaning
- All 10 existing codes from `_infer_error_code()` must be included
- Domain prefixes must be from the allowed set: `VALIDATION_`, `MT5_`, `EXECUTION_`, `WORKER_`, `SYMBOL_`, `REQUEST_`, `INTERNAL_`

---

## 4. Compatibility Pledge Contract (`docs/baseline/compatibility-pledge.md`)

### Required Sections

1. **Pledge Summary**: Overall policy statement
2. **Endpoint Pledge Table**: columns — Endpoint Family, Stability Level, Phases That May Change It, Compatibility Window, Migration Notes
3. **Legacy Support Window**: Explicit statement of when `detail`-shaped responses will be retired
4. **Consumer Migration Guide**: What consumers must do to adopt the canonical envelope when it arrives

### Validation Rules

- Must cover 100% of endpoints listed in `endpoint-snapshot.md`
- Every endpoint must have one of: `frozen`, `evolving`, `migrating`
- Legacy support window end must be tied to a specific phase milestone

---

## 5. Launcher Invariants Contract (`docs/baseline/launcher-invariants.md`)

### Required Sections

1. **Invariant Registry**: Table with — ID, Category, Description, Current Behavior, Verification Method
2. **Review Gate Instructions**: How to use this checklist in PR reviews for `scripts/` changes
3. **Exception Process**: How to request a variance from an invariant

### Validation Rules

- Must cover all 8 scripts in `scripts/`
- Must cover: script names, invocation patterns, restart policy, log bundle structure, smoke-test procedure
- Each invariant must have a concrete verification method

---

## 6. Parity Gap Register Contract (`docs/baseline/parity-gap-register.md`)

### Required Sections

1. **Coverage Matrix**: Table with — Category, MT5 Function, Bridge Coverage, Coverage Notes, Constraints, Known Broker Variance, Fallback Behavior, Test Coverage, Operator Readiness Impact
2. **Summary Statistics**: Number of functions per coverage level (full/partial/none)
3. **Priority Guidance**: Which gaps are most impactful for Phase 7

### Validation Rules

- Must cover all 7 MT5 capability categories from research.md §6.5
- Every category must have at least one function entry
- `bridge_coverage` must be one of `full`, `partial`, `none`
- `test_coverage` must be one of `automated`, `manual`, `none`

---

## 7. Endpoint Snapshot Contract (`docs/baseline/endpoint-snapshot.md`)

### Required Sections

1. **Endpoint Inventory**: Table grouped by family — Path, Method, Module, Purpose, Response Shape, Auth Required
2. **Scripts Inventory**: Table — Script Name, Purpose, Invocation, Phase 5 Relevance
3. **Snapshot Metadata**: Date, bridge version, and instructions for re-taking the snapshot

### Validation Rules

- Must match all routes registered in `app/main.py`
- Must match all scripts in `scripts/`
- Snapshot date must be recorded
