---
name: Institutional Student Portal
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#444653'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#757684'
  outline-variant: '#c4c5d5'
  surface-tint: '#3755c3'
  primary: '#00288e'
  on-primary: '#ffffff'
  primary-container: '#1e40af'
  on-primary-container: '#a8b8ff'
  inverse-primary: '#b8c4ff'
  secondary: '#585f67'
  on-secondary: '#ffffff'
  secondary-container: '#dce3ec'
  on-secondary-container: '#5e656d'
  tertiary: '#611e00'
  on-tertiary: '#ffffff'
  tertiary-container: '#872d00'
  on-tertiary-container: '#ffa583'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dde1ff'
  primary-fixed-dim: '#b8c4ff'
  on-primary-fixed: '#001453'
  on-primary-fixed-variant: '#173bab'
  secondary-fixed: '#dce3ec'
  secondary-fixed-dim: '#c0c7d0'
  on-secondary-fixed: '#151c23'
  on-secondary-fixed-variant: '#40484f'
  tertiary-fixed: '#ffdbce'
  tertiary-fixed-dim: '#ffb59a'
  on-tertiary-fixed: '#380d00'
  on-tertiary-fixed-variant: '#802a00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  data-mono:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes an intelligent, restrained, and utilitarian operational environment for higher education administration and student services. Drawing inspiration from modern institutional minimalism, the interface prioritizes administrative clarity, high legibility, and effortless cognitive processing over decorative ornament.

### Core Tenets
- **Disciplined Restraint:** Visual noise is aggressively eliminated. Interfaces avoid heavy gradients, dramatic drop-shadows, and decorative illustrations.
- **Utilitarian Clarity:** Information density is balanced by deliberate whitespace and structured tabular layouts. Data takes precedence; the frame exists only to clarify state.
- **Institutional Authority:** Built on an architectural foundation of crisp hairline borders, pure white panels, and balanced typographic weight that communicates trust, stability, and academic rigor.

### Emotional Demeanor
The user experience evokes absolute calm, precision, and efficiency. It treats the student and administrator as capable professionals navigating critical milestones—finances, degree audits, and academic schedules—with no ambiguity or friction.

## Colors

The color palette employs quiet neutral surfaces contrasted with targeted, institutional accents to guide attention without fatigue.

### Palette Architecture
- **Canvas Base:** `#F8F9FA` forms the persistent viewport background, creating a soft, glare-free backdrop.
- **Surface Panels:** `#FFFFFF` is used strictly for interactive containers, cards, tables, and modal dialogs.
- **Structural Dividing Lines:** `#E5E7EB` is the universal border and rule line token, rendering exact 1px structural separation.
- **Primary Ink:** `#0F172A` provides commanding contrast for titles, primary data values, and headers.
- **Muted Ink:** `#64748B` applies to secondary descriptions, contextual metadata, table labels, and helper text.
- **Collegiate Blue Accent:** `#1E40AF` serves as the primary actionable signal (primary buttons, active tabs, focused states).
- **Soft Accent Tint:** `#EFF6FF` provides subtle hover backgrounds and active navigation highlights.

### Functional Status Indicators
Status colors strictly pair high-contrast text against gentle, desaturated tint fields to retain institutional sobriety:
- **Success / Cleared / Paid:** Text `#15803D` over fill `#F0FDF4` (Border `#DCFCE7`).
- **Warning / Pending / Partial:** Text `#B45309` over fill `#FEF3C7` (Border `#FDE68A`).
- **Critical / Overdue / Action Required:** Text `#B91C1C` over fill `#FEF2F2` (Border `#FECACA`).

## Typography

The typographic hierarchy utilizes `Inter` across all structural, reading, and navigational elements.

### Conventions
- **Sentence Case Primacy:** All headers, field labels, tab triggers, and button microcopy are strictly formatted in sentence case. All-caps uppercase tracking is prohibited.
- **Numerical Alignment:** Tabular figures (`font-variant-numeric: tabular-nums;`) must be enabled on all numerical representations, course codes, financial balances, dates, and metric readouts.
- **Weight Calibration:** Typographic hierarchy relies strictly on `400` (Regular) for flow text, `500` (Medium) for controls and meta markers, and `600` (Semi-bold) for major landmarks. Heavy weights (`700` and above) are excluded to maintain visual lightness.

## Layout & Spacing

The layout model is anchored by an orderly 12-column fluid grid system bounded by maximum content constraints, prioritizing content scannability and structural alignment.

### Grid & Breakpoints
- **Desktop (>= 1280px):** 12-column layout, `margin: 2rem` (max-width `1440px`), `gutter: 1.5rem`.
- **Tablet (768px – 1279px):** 8-column layout, `margin: 1.5rem`, `gutter: 1rem`.
- **Mobile (< 768px):** 4-column layout, `margin: 1rem`, `gutter: 1rem`. Single-column stack for all card modules.

### Structural Rhythm
Whitespace serves as the primary organizational tool. Structural layout components depend on `space-lg` and `space-xl` to segment disparate task zones (e.g., separating outstanding holds from term schedules), while micro-alignments inside data cards and list groups adhere strictly to `space-xs`, `space-sm`, and `space-md`.

## Elevation & Depth

This design system deliberately rejects heavy, layered drop shadows and floating multi-tier elevations in favor of clean architectural planes.

### Plane Separation
- **Hairline Boundaries:** Surface hierarchy is produced via 1px solid `#E5E7EB` borders separating panels from the `#F8F9FA` canvas background.
- **Zero-Shadow Base:** Standard cards, tables, search toolbars, and containers carry `box-shadow: none`.
- **Transient Elevation:** Temporary context surfaces (dropdown menus, popovers, flyout drawers) use an ultra-subtle, ambient shadow to lift above content without visual heaviness:
  `box-shadow: 0 4px 12px 0 rgba(15, 23, 42, 0.05), 0 1px 2px 0 rgba(15, 23, 42, 0.04);`
- **Modal Overlays:** Modal dialogues feature a muted backdrop scrim of `rgba(15, 23, 42, 0.3)` paired with a single 1px `#E5E7EB` outline around the elevated `#FFFFFF` container.

## Shapes

The shape system employs deliberate, soft geometry (`roundedness: 1`) to preserve an authoritative, institutional appearance while softening industrial corners.

### Radius Rules
- **Base Components (0.25rem / 4px):** Applied to form inputs, checkboxes, small buttons, status tags, and chips.
- **Card Panels & Tables (0.5rem / 8px - `rounded-lg`):** Applied to primary content cards, data tables, and modal dialogs.
- **Full Radius (9999px):** Restricted solely to circular user avatars and numeric indicator badges. Interactive buttons and card surfaces must never be pill-shaped.

## Components

### Buttons
- **Primary:** Background `#1E40AF`, text `#FFFFFF`, border `1px solid transparent`, corner radius `0.25rem`. Hover: `#1D4ED8`. Active: `#1E3A8A`.
- **Secondary / Outlined:** Background `#FFFFFF`, text `#0F172A`, border `1px solid #E5E7EB`. Hover: `#F8F9FA`. Active: `#F1F5F9`.
- **Ghost / Tertiary:** Background transparent, text `#1E40AF`, border none. Hover: `#EFF6FF`.
- **Padding:** 8px 16px for standard sizes; 6px 12px for compact table action rows. Typography uses `label-md`.

### Status Chips & Badges
- **Height & Padding:** 22px height, 4px 8px padding, 4px border radius. Typography uses `label-sm` with tabular numerals.
- **Success:** Text `#15803D`, background `#F0FDF4`, border `1px solid #DCFCE7`.
- **Warning:** Text `#B45309`, background `#FEF3C7`, border `1px solid #FDE68A`.
- **Critical:** Text `#B91C1C`, background `#FEF2F2`, border `1px solid #FECACA`.
- **Neutral:** Text `#64748B`, background `#F1F5F9`, border `1px solid #E2E8F0`.

### Form Controls & Inputs
- **Input Fields:** Background `#FFFFFF`, text `#0F172A`, border `1px solid #E5E7EB`, padding `8px 12px`, radius `0.25rem`.
- **Placeholder:** `#94A3B8`.
- **Focus State:** Border `1px solid #1E40AF`, box shadow `0 0 0 1px #1E40AF` (hairline focus ring, no blurry glow).
- **Checkboxes & Radios:** 16px size. Border `1px solid #CBD5E1`. Checked background `#1E40AF` with crisp white indicator check.

### Cards & Data Panels
- **Container Styling:** Background `#FFFFFF`, border `1px solid #E5E7EB`, radius `0.5rem`, padding `1.5rem`.
- **Card Header:** Border-bottom `1px solid #E5E7EB` with `1rem` vertical padding, separating controls and section titles from content.
- **Row Division:** Sequential items in list cards and balance summaries are separated by `1px solid #F1F5F9` lines with zero margins.

### Tables & Academic Lists
- **Header Row:** Background `#F8F9FA`, text `#64748B`, weight `500`, border-bottom `1px solid #E5E7EB`. Sentence case column titles.
- **Body Rows:** Background `#FFFFFF`, border-bottom `1px solid #E5E7EB`, hover background `#F8F9FA`. Numerical columns strictly right-aligned with tabular figures enabled.