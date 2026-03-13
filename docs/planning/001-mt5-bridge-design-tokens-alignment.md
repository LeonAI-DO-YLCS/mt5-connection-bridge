# MT5 Connection Bridge UI Design Tokens Alignment

## Document Metadata

| Property | Value |
|----------|-------|
| **Plan Title** | MT5 Connection Bridge UI Design Tokens Alignment |
| **Version** | 1.0 |
| **Date** | 2026-03-13 |
| **Status** | Implemented |
| **Target** | mt5-connection-bridge/dashboard/ |

---

## 1. Executive Summary

This plan outlines the comprehensive approach to align the MT5 Connection Bridge dashboard UI with the AI Hedge Fund's official design tokens. The bridge dashboard, currently using standalone CSS custom properties, adopts the design system defined in `docs/design-system/ai-hedge-fund-v1/tokens/tokens.source.json`.

### Key Objectives Achieved

1. Replace all hardcoded color values with design token references
2. Update typography to use Inter font family
3. Align border-radius values with the design system
4. Maintain dark-theme-only mode (matching current bridge UI)
5. Ensure zero impact on JavaScript functionality

---

## 2. Architecture Overview

### Current Stack

| Layer | Technology | Files |
|-------|------------|-------|
| Styling | Pure CSS with CSS Variables | `dashboard/css/dashboard.css` |
| Framework | Vanilla JavaScript (ES6 Modules) | `dashboard/js/*.js` |
| Shell | HTML5 | `dashboard/index.html` |

### Design Tokens Source

| Token File | Purpose |
|------------|---------|
| `docs/design-system/ai-hedge-fund-v1/tokens/tokens.source.json` | Primitive & Semantic tokens |
| `app/frontend/src/index.css` | CSS variable implementation |
| `app/frontend/tailwind.config.ts` | Tailwind configuration |

---

## 3. Color Tokens Mapping

### Primary Surface Colors

| Current Variable | Current Value | Target Token | Target Value | Semantic Name |
|-----------------|---------------|--------------|--------------|---------------|
| `--bg` | `#0a1724` | `primitive.color.neutral.0` | `#0F1724` | neutral-0 |
| `--panel` | `#102338` | `semantic.surface.panel` | `#0F1724` | neutral-0 |
| `--card` | `#17334f` | `primitive.color.neutral.100` | `#0B1220` | neutral-100 |

### Text Colors

| Current Variable | Current Value | Target Token | Target Value |
|-----------------|---------------|--------------|--------------|
| `--text` | `#eaf4ff` | `semantic.text.primary` | `#E7EDF8` |
| `--muted` | `#9eb7ce` | `semantic.text.secondary` | `#91A1BD` |

### Brand & Action Colors

| Current Variable | Current Value | Target Token | Target Value |
|-----------------|---------------|--------------|--------------|
| `--accent` | `#5ad8ff` | `semantic.action.primary` | `#4D8DFF` |
| `--primary-color` | `--accent` | `semantic.action.primary` | `#4D8DFF` |

### Status/Signal Colors

| Current Variable | Current Value | Target Token | Target Value |
|-----------------|---------------|--------------|--------------|
| `--ok` | `#58e6a9` | `semantic.status.gain` | `#16C784` |
| `--danger` | `#ff6b6b` | `semantic.status.loss` | `#FF5C7A` |
| `--warn` | `#ffcb6b` | `semantic.status.warn` | `#F5A524` |

### Border Colors

| Current Variable | Current Value | Target Token | Target Value |
|-----------------|---------------|--------------|--------------|
| `--border-color` | `rgba(255,255,255,0.16)` | `semantic.border.default` | `#1F2C40` |

---

## 4. Typography

| Aspect | Current | Target |
|--------|---------|--------|
| Primary Font | `Segoe UI, Tahoma` | `Inter, system-ui, sans-serif` |
| Fallback | System default | `Avenir, Helvetica, Arial` |

---

## 5. Spacing & Radius

| Element | Current Radius | Target Token | Target Value |
|---------|---------------|--------------|--------------|
| Panel | 12px | `primitive.radius.lg` | 14px |
| Tab | 8px | `primitive.radius.md` | 10px |
| Button | 8px | `primitive.radius.md` | 10px |

---

## 6. Implementation Summary

### Files Modified

| File | Changes |
|------|---------|
| `dashboard/css/dashboard.css` | Complete token replacement, component updates |
| `dashboard/index.html` | Added Inter font import |

### Implementation Date

- **Started**: 2026-03-13
- **Completed**: 2026-03-13

---

## 7. Verification

To verify the implementation:

```bash
# Check CSS variables are properly defined
grep -n "\-\-" mt5-connection-bridge/dashboard/css/dashboard.css | head -30

# Verify Inter font is imported
grep -n "Inter" mt5-connection-bridge/dashboard/index.html
```

---

## 8. Visual Checkpoints

- [x] Background color matches `#0F1724`
- [x] Accent/primary buttons are `#4D8DFF`
- [x] Gain/loss indicators use `#16C784` / `#FF5C7A`
- [x] Font is Inter
- [x] Panel border-radius is 14px
- [x] Tab border-radius is 10px
- [x] Border colors use `#1F2C40`

---

*This document is part of the MT5 Connection Bridge project and aligns with the AI Hedge Fund Design System v1.*
