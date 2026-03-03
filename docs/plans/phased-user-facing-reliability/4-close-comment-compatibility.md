# Phase 4: Close-Order Comment Compatibility

> Objective: Eliminate close-order failures caused by broker/terminal rejection of the MT5 `comment` field.

---

## 1. Confirmed Failure

Observed operational failure:

- `order_send returned None: (-2, 'Invalid "comment" argument')`

Current close request includes a static comment string and fails before broker execution in affected environments.

---

## 2. Scope

Primary:

- `POST /close-position`

Secondary (same failure class risk):

- `POST /pending-order` (`comment` field already user-provided)
- future raw MT5 order surfaces.

---

## 3. Decision Matrix

| Option | Behavior | Pros | Cons | Recommendation |
|---|---|---|---|---|
| A | Keep static comment | Zero effort | Known breakage persists | No |
| B | Sanitize only | Better compatibility | Does not guarantee success | Partial |
| C | Sanitize + adaptive retry without comment when invalid-comment detected | Highest practical reliability | Slight extra logic | **Recommended** |
| D | Remove comments globally | Maximum compatibility | Loses helpful annotations | Backup-only |

---

## 4. Compatibility Policy

### 4.1 Comment normalization

Normalize comment values with:

1. allowed character policy
2. maximum length policy
3. whitespace cleanup policy
4. empty-value handling policy

### 4.2 Adaptive fallback

For close operation:

1. Attempt A: send normalized comment.
2. If `order_send is None` and `last_error` matches invalid-comment signature:
   - Attempt B: resend once without comment.
3. Preserve same `tracking_id` across attempts.
4. Emit sub-state outcomes:
   - `comment_rejected_recovered`
   - `comment_rejected_unrecoverable`

---

## 5. User-Facing Behavior

### 5.1 Recovered path

Message category: warning + success context.

- Title: `Broker rejected note format; close completed with compatibility fallback`
- Code: `MT5_REQUEST_COMMENT_INVALID_RECOVERED`
- Action: none required.

### 5.2 Unrecovered path

Message category: error.

- Title: `Could not close position due to broker request-format restrictions`
- Code: `MT5_REQUEST_COMMENT_INVALID`
- Action: show concrete next steps and support reference.

---

## 6. Observability and Audit

For every affected operation store:

- `tracking_id`
- `operation`
- `code`
- `attempt_variant` (`with_comment`, `without_comment`)
- `mt5_last_error_code`
- `mt5_last_error_message`
- `final_outcome`

---

## 7. Testing Strategy

1. Unit tests:
   - comment normalizer and signature matcher.
2. Integration tests:
   - invalid-comment then recover.
   - invalid-comment then fail.
3. UI tests:
   - never show raw tuple as primary message.

---

## 8. Exit Criteria

1. Close-order invalid-comment failures are either recovered or clearly explained.
2. Dashboard messaging is user-readable and traceable.
3. Operational logs differentiate recovered vs unrecovered compatibility paths.

