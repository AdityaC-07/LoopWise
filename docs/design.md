# Design Specification — LoopWise Waste Segregation Intelligence Platform

> **Approved direction:** Material Flows (Direction 2 — refined)
> **Status:** Approved — v1.0 | **Updated:** 2026-10
> This document is the authoritative visual and UX specification.
> The IDE agent must read this completely before writing any frontend code.
> Design decisions here take precedence over any defaults or conventions.

---

## 1. Design Concept and Rationale

### Concept: Material Flows
The platform visualises waste as material in motion — items that are either successfully flowing toward recovery or being lost to contamination. The design makes that journey legible at every level: a resident learns where one bottle goes; a ward officer sees where a whole neighbourhood's materials are being lost.

### Primary users for this design
Municipal workers, ward officers, and housing society supervisors. These users:
- May not be technically confident with software
- Work under time pressure
- Need to understand the information at a glance without reading explanations
- Are using this as a job tool, not a personal app

Every design decision must be evaluated against this question: **would a ward sanitation officer understand this in under 5 seconds without training?**

### What this design is not
- It is not a "green eco app" with leaf icons and lime green buttons
- It is not a startup SaaS dashboard with card grids and generic charts
- It is not technical: no jargon, no codes, no scores without plain-language labels
- It is not cluttered: every element on screen earns its place

---

## 2. Color System

### Palette definition (CSS custom properties)

```css
:root {
  /* Page and surfaces */
  --color-bg:               #0A1F0D;   /* deep forest — page background */
  --color-surface-1:        #122115;   /* primary card surface */
  --color-surface-2:        #1A2E1D;   /* secondary surface, sidebars */
  --color-surface-3:        #1F3622;   /* elevated / hover / selected state */
  --color-surface-overlay:  #0A1F0Dcc; /* tour overlay backdrop — 80% opacity bg */

  /* Text */
  --color-text-primary:     #F0EAD6;   /* warm cream — all body text */
  --color-text-secondary:   #A8B89C;   /* muted sage — secondary labels, captions */
  --color-text-tertiary:    #6E8A72;   /* very muted — placeholders, disabled */
  --color-text-inverse:     #0A1F0D;   /* used on amber/light backgrounds */

  /* Accent — action and recovery */
  --color-amber:            #F5A623;   /* primary CTA, recovery indicators, links */
  --color-amber-dim:        #3D2A08;   /* amber tint surface (e.g. amber badge bg) */

  /* Signals */
  --color-signal-good:      #5DBF6E;   /* successful / high recovery */
  --color-signal-warn:      #F5C842;   /* medium / needs attention */
  --color-signal-bad:       #E84040;   /* contamination / wrong bin / error */
  --color-signal-bad-dim:   #3B0F0F;   /* red tint surface */

  /* Bin colours — used only for bin assignment cards */
  --color-bin-wet:          #5DBF6E;   /* green — wet/organic waste */
  --color-bin-dry:          #4A9B8E;   /* teal — dry/recyclable waste */
  --color-bin-hazardous:    #E84040;   /* red — hazardous waste */
  --color-bin-ewaste:       #9B7EC8;   /* violet — e-waste */
  --color-bin-rejected:     #6E8A72;   /* muted — cannot be accepted */

  /* Material category colours — used for badges and charts only */
  --color-mat-plastic:      #8A9BB5;
  --color-mat-paper:        #C4903A;
  --color-mat-organic:      #7CA870;
  --color-mat-glass:        #4A9B8E;
  --color-mat-metal:        #9B9B8A;
  --color-mat-ewaste:       #9B7EC8;
  --color-mat-hazardous:    #C47A4A;
  --color-mat-composite:    #7A8B6E;
  --color-mat-other:        #6E8A72;

  /* Recovery channel colours — used in analytics charts */
  --color-channel-informal:   #F5A623;
  --color-channel-municipal:  #4A9B8E;
  --color-channel-specialist: #9B7EC8;

  /* Borders and dividers */
  --color-border:           #2A4030;   /* subtle border — cards, inputs */
  --color-border-strong:    #3A5540;   /* stronger border — focused inputs */
  --color-border-accent:    #F5A623;   /* amber border — active/selected states */

  /* Interactive states */
  --color-focus-ring:       #F5A623;   /* 2px focus outline */
}
```

### Contrast requirements (WCAG AA)
- `--color-text-primary` on `--color-bg`: ≥ 14:1 — passes AAA
- `--color-text-secondary` on `--color-surface-1`: verify ≥ 4.5:1 — use only for text ≥ 16px
- `--color-text-tertiary`: only for non-essential decorative text; never for data
- `--color-amber` on `--color-bg`: ≥ 7:1 — passes AAA
- All `--color-signal-*` on `--color-surface-1`: verify ≥ 3:1 for graphical elements

---

## 3. Typography System

### Fonts

```css
/* Load in index.html — not via CSS @import for performance */
/* Google Fonts: Fraunces (variable), Inter (variable), JetBrains Mono */
```

```css
:root {
  --font-display:   'Fraunces', Georgia, serif;       /* large headings, material names */
  --font-body:      'Inter', system-ui, sans-serif;   /* all UI text */
  --font-mono:      'JetBrains Mono', monospace;      /* ward codes, event IDs only */
}
```

### Type scale

| Token | Font | Size | Weight | Line height | Usage |
|---|---|---|---|---|---|
| `--type-display` | Fraunces | 36px | 700 | 1.1 | Welcome screen, material name on result |
| `--type-h1` | Fraunces | 28px | 600 | 1.2 | Page titles |
| `--type-h2` | Inter | 22px | 600 | 1.3 | Section headings |
| `--type-h3` | Inter | 18px | 600 | 1.4 | Card headings |
| `--type-body-lg` | Inter | 17px | 400 | 1.6 | Primary body text |
| `--type-body` | Inter | 15px | 400 | 1.6 | Standard body text |
| `--type-label` | Inter | 13px | 500 | 1.4 | Labels, captions |
| `--type-label-upper` | Inter | 11px | 600 | 1.4 | Uppercase labels, status badges |
| `--type-mono` | JetBrains Mono | 13px | 400 | 1.5 | Ward codes, IDs |

### Typography rules
- Use Fraunces only for display headings and the material name on the classification result card. Everything else is Inter.
- Never use Fraunces for body text, labels, or UI controls.
- Tabular numerals always on: `font-variant-numeric: tabular-nums` on any element displaying numbers.
- Numbers in analytics: right-aligned in tables; left-aligned in cards.
- Do not center-align body text. Center only icons and very short labels.

---

## 4. Spacing and Grid

```css
:root {
  /* Spacing scale — base unit 4px */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-24: 96px;

  /* Layout */
  --layout-content-max:    1200px;
  --layout-sidebar-width:  240px;
  --layout-sidebar-collapsed: 64px;
  --layout-topbar-height:  56px;
  --layout-mobile-tabbar:  64px;

  /* Card */
  --card-radius:    12px;
  --card-padding:   var(--space-6);   /* 24px */
  --card-gap:       var(--space-4);   /* 16px between cards */

  /* Component */
  --radius-sm:   6px;
  --radius-md:   8px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-pill: 999px;
}
```

### Grid
- Desktop: 12 columns, 24px gutter, 24px margin
- Tablet (768px): 8 columns, 16px gutter, 16px margin
- Mobile (375px): 4 columns, 16px gutter, 16px margin

---

## 5. Surface, Border, and Shadow System

```css
:root {
  /* Shadows — glow-free; depth only */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.5);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.6);

  /* Card */
  --card-bg:      var(--color-surface-1);
  --card-border:  1px solid var(--color-border);
  --card-shadow:  var(--shadow-md);

  /* Input */
  --input-bg:       var(--color-surface-2);
  --input-border:   1px solid var(--color-border);
  --input-focus:    1px solid var(--color-border-accent);
  --input-radius:   var(--radius-md);
  --input-padding:  var(--space-3) var(--space-4);
}
```

### Surface hierarchy
1. `--color-bg` — page background; nothing else sits at this level
2. `--color-surface-1` — primary cards, main content areas
3. `--color-surface-2` — sidebar, secondary panels, inputs
4. `--color-surface-3` — hover states, selected rows, active list items
5. Overlays (tour, modals) — use `--color-surface-overlay` backdrop behind `--color-surface-1` content

---

## 6. Component Specifications

### 6.1 Button

```
PRIMARY button:
  background:   --color-amber
  color:        --color-text-inverse
  font:         --type-label (Inter 13px 500)... wait, use Inter 15px 600
  padding:      12px 24px
  radius:       --radius-md (8px)
  hover:        background lightens by 10% (filter: brightness(1.1))
  active:       background darkens by 10%
  focus:        2px solid --color-focus-ring, 2px offset
  disabled:     opacity 0.4, cursor not-allowed
  min-width:    120px
  height:       44px (touch target)

SECONDARY button:
  background:   transparent
  border:       1px solid --color-border-strong
  color:        --color-text-primary
  (otherwise same as primary)

GHOST button:
  background:   transparent
  border:       none
  color:        --color-amber
  (no min-width constraint)

DANGER button:
  background:   --color-signal-bad
  color:        white
```

Rules:
- Maximum 2 buttons per screen section. When more actions are needed, use a menu.
- Every button has a plain-language label (no codes, no jargon).
- Never use icon-only buttons without a visible text label except in the top bar and tab bar.
- Primary button is always the rightmost / bottommost action.

### 6.2 Card

```
background:   --color-surface-1
border:       1px solid --color-border
border-radius: --card-radius (12px)
padding:      --card-padding (24px)
shadow:       --shadow-md

Hover (interactive cards only):
  background: --color-surface-3
  border-color: --color-border-strong
  transition: all 150ms ease
```

### 6.3 Badge — Material Category

```
border-radius: --radius-pill
padding:       3px 10px
font:          --type-label-upper (Inter 11px 600 uppercase)
background:    category colour at 20% opacity (e.g. rgba(138,155,181,0.2))
color:         category colour (e.g. --color-mat-plastic)
```

One badge per material. Never stack more than 2 badges in a row.

### 6.4 ConfidenceBar — "How sure we are"

Plain-language label replaces all technical confidence terminology.

```
Container:
  width: 100%
  height: 8px
  background: --color-surface-2
  border-radius: --radius-pill

Fill:
  border-radius: --radius-pill
  transition: width 400ms ease-out
  
  high (≥0.80):   width 100%;  background: --color-signal-good
  medium (0.55–0.79): width 60%; background: --color-signal-warn
  low (<0.55):    width 30%;  background: --color-signal-bad

Label above bar (left-aligned):
  font: --type-label
  color: --color-text-secondary
  text: "How sure we are" with value "Very sure / Fairly sure / Not very sure"
```

Do not display the numeric confidence score. Display only the plain-language label and the visual bar.

### 6.5 BinCard — "Where it goes"

This is the most important piece of information on the classification result. It must be visually dominant.

```
Container:
  background:   bin colour at 15% opacity
  border:       2px solid bin colour
  border-radius: --card-radius
  padding:      --space-6
  
Bin icon:
  size: 48px × 48px
  color: bin colour

Bin label (large):
  font: --type-h2 (Inter 22px 600)
  color: bin colour
  text: "Green Wet Waste Bin" / "Blue Dry Waste Bin" / "Red Hazardous Bin" / "E-Waste Drop-off" / "Cannot be accepted"

Sub-label:
  font: --type-body
  color: --color-text-secondary
  text: brief plain-language action (e.g. "Rinse it, then place it in this bin")
```

Bin names are always friendly and clear — never "dry_waste" or enum values.

### 6.6 DemoModeIndicator (renamed: "Practice Mode" in UI)

```
Position: fixed top-right corner; z-index above all content
Appearance:
  background: --color-amber-dim
  border: 1px solid --color-amber
  border-radius: --radius-pill
  padding: 4px 12px
  font: --type-label (Inter 13px 500)
  color: --color-amber
  text: "Practice Mode — not live data"
  
Click behaviour: opens a small tooltip explaining "This is a training version using test data."
```

### 6.7 StatusLight — ward health at a glance

Used in the analytics overview for quick triage.

```
Circle: 12px diameter
  Good   (contamination_rate < 0.10):  --color-signal-good
  Warn   (0.10–0.20):                  --color-signal-warn
  Bad    (> 0.20):                     --color-signal-bad

Pulsing animation on "Bad" only:
  animation: pulse 2s ease-in-out infinite
  @keyframes pulse: opacity 1.0 → 0.5 → 1.0
```

### 6.8 RecoveryBar — "Can this be recycled?"

```
Label: "Can this be recycled?"
  high:    "Yes — high value material"       colour: --color-signal-good
  medium:  "Possibly — if sorted correctly"  colour: --color-signal-warn
  low:     "Unlikely"                        colour: --color-signal-bad (dimmed)
  none:    "No — cannot be recovered"        colour: --color-text-tertiary
```

Visual: same filled bar structure as ConfidenceBar. No numeric scores.

### 6.9 Tour Spotlight (Onboarding)

See Section 10 for full specification.

---

## 7. Navigation Architecture

### Desktop (≥ 1024px)

```
┌─────────────────────────────────────────────────────────┐
│ TopBar [56px]                                            │
│  Logo  |  (breadcrumb)             | PracticeMode | Role│
├──────────────┬──────────────────────────────────────────┤
│ Sidebar      │  Main content area                       │
│ [240px]      │                                          │
│              │                                          │
│  ▸ Classify  │                                          │
│  ▸ Overview  │                                          │
│  ▸ My Ward   │                                          │
│  ▸ All Wards │                                          │
│  ▸ Help      │                                          │
│              │                                          │
│ [collapse ◀] │                                          │
└──────────────┴──────────────────────────────────────────┘
```

Sidebar items — plain-language labels only:
- **Classify Waste** (icon: camera) — classification entry screen
- **Overview** (icon: grid) — platform-wide summary
- **My Ward** (icon: map-pin) — ward detail for user's assigned ward
- **All Wards** (icon: list) — ward comparison table (municipal role only)
- **Help** (icon: ?) — materials guide and tour replay

Sidebar collapsed (64px): icon only with tooltip on hover.
Active item: amber left border + `--color-surface-3` background.

### Mobile (< 768px)

```
┌─────────────────────────────────┐
│ TopBar [56px]                   │
│  Logo              PracticeMode │
├─────────────────────────────────┤
│                                 │
│  Main content (scrollable)      │
│                                 │
│                                 │
├─────────────────────────────────┤
│ Bottom tab bar [64px]           │
│  📷        📊       📍      ❓  │
│ Classify Overview My Ward Help  │
└─────────────────────────────────┘
```

Tab bar: 4 items maximum. Active tab: amber icon + amber label. Inactive: `--color-text-tertiary`.

### Information architecture

```
LoopWise
├── Classify Waste
│   ├── Entry (camera / description)
│   └── Result
│       ├── High confidence
│       ├── Medium confidence (with confirmation)
│       ├── Low confidence (with top-3 picker)
│       └── Correction submitted
├── Overview (analytics overview)
├── My Ward (ward detail — user's ward)
├── All Wards (ward list + status — municipal)
└── Help
    ├── Replay tour
    └── Material guide
```

---

## 8. Onboarding Tour — Full Specification

### Behaviour
- Triggered automatically on first visit (key: `loopwise_tour_complete` in `localStorage`).
- If the key is absent or `false`: launch tour on page load after a 500 ms delay.
- Can be replayed at any time from the Help page or Help tab.
- "Skip tour" link is always visible on every step.
- Tour does not auto-advance — the user taps/clicks "Next" each time.
- On the final step: set `localStorage.loopwise_tour_complete = true`.

### Visual design

```
Backdrop: fixed overlay covering 100vw × 100vh
  background: rgba(10, 31, 13, 0.85)    /* --color-surface-overlay */
  z-index: 1000

Spotlight (highlighted element):
  The target element is NOT overlaid.
  Its surrounding area IS dimmed.
  Implementation: a clip-path or box-shadow cutout around the target bounding box.
  border: 2px solid --color-amber
  border-radius: matches the element's own border-radius + 4px
  
Tooltip:
  background: --color-surface-1
  border: 1px solid --color-border-accent
  border-radius: --card-radius (12px)
  padding: --space-6 (24px)
  max-width: 320px
  shadow: --shadow-lg
  
  Positioned: below the target on desktop; above the target on mobile.
  Arrow: a 10px triangle pointing at the target element.

Step counter:
  font: --type-label
  color: --color-text-secondary
  text: "Step 3 of 8"

Step heading:
  font: --type-h3 (Inter 18px 600)
  color: --color-text-primary

Step body:
  font: --type-body (Inter 15px 400)
  color: --color-text-secondary
  max 2 sentences. Plain language. No jargon.

Buttons row:
  Left:  "Skip tour" — ghost button, --color-text-tertiary
  Right: "Next →" or "Got it ✓" on last step — primary amber button
```

### Tour steps — content

| Step | Target element | Heading | Body text |
|---|---|---|---|
| 1 | None — centred welcome card | Welcome to LoopWise | LoopWise helps you sort waste correctly and track how your ward is doing. We'll walk you through how it works. It only takes a minute. |
| 2 | Camera/upload button on Classify page | Take a photo to identify waste | Point your camera at an item or upload a photo. LoopWise will tell you exactly which bin it belongs in. |
| 3 | Description text input | Or describe it in words | If you don't have a photo, just type what the item is — like "plastic water bottle" or "old newspaper." |
| 4 | Result card — BinCard component | See where it goes | LoopWise will show you the correct bin with clear instructions. The bigger the colour, the more confident the answer. |
| 5 | Result card — ConfidenceBar | Check how sure we are | The bar shows how confident LoopWise is. If it says "Not very sure," you'll see other options to choose from. |
| 6 | Correction/feedback button | Tell us if we got it wrong | If the answer doesn't look right, tap here to correct it. This helps the system get better for everyone. |
| 7 | Analytics overview / Overview tab | See how your ward is doing | The Overview tab shows how waste sorting is going across your area — which items are often sorted incorrectly and where there's room to improve. |
| 8 | Help tab / Help icon | Replay this tour any time | If you ever need a reminder of how things work, tap the Help tab to replay this tour. You're all set! |

### Tour implementation notes for IDE agent

```typescript
// Tour state interface
interface TourStep {
  targetSelector: string | null;  // CSS selector; null for centered card (step 1)
  heading: string;
  body: string;
  position: 'below' | 'above' | 'left' | 'right' | 'center';
}

// Spotlight implementation:
// Use CSS clip-path with CSS custom properties on the backdrop
// Update the clip-path rect on window resize
// Animate spotlight position change with 250ms transition

// Accessibility:
// aria-live="polite" on the tooltip
// Focus trap within the tooltip while tour is open
// Escape key = skip tour
// Tab key cycles within tooltip buttons only

// Mobile:
// On mobile viewport, always position tooltip above the target
// If target is in bottom half of screen, position tooltip above
// Never let tooltip overflow viewport
```

---

## 9. Screen Specifications

### 9.1 Classification Entry Screen (`/`)

**Purpose:** Let the user identify a waste item as quickly as possible.

**Layout (mobile — 375px):**
```
┌────────────────────────┐
│ TopBar                 │
├────────────────────────┤
│                        │
│  [large camera button] │  ← primary action; 160px × 160px circle
│  "Take a photo"        │
│                        │
│  ─── or ───            │
│                        │
│  [text input]          │
│  "Describe the item"   │
│                        │
│  [optional] Ward       │
│  [dropdown]            │
│                        │
│  □ Save photo to help  │
│    improve LoopWise    │  ← consent checkbox; unchecked default
│                        │
│  [Identify this item →]│  ← primary amber button; full width
│                        │
└────────────────────────┘
```

**Layout (desktop — 1280px):**
```
Sidebar + content area
Content: centred single column, max 520px
Same elements as mobile; camera button becomes a drag-and-drop zone (240px × 160px)
```

**Interaction rules:**
- Camera button opens native file picker (image capture on mobile, file browser on desktop).
- Selecting an image immediately shows a thumbnail preview with a "Remove" link.
- The "Identify this item" button is disabled until at least one input (photo or text) is provided.
- Consent checkbox label is plain language: "Save photo to help improve LoopWise." A small "?" icon next to it opens a one-line tooltip: "Your photo will only be saved if you check this box."
- Ward dropdown label: "Which ward? (optional)" — shows friendly ward names, not IDs.
- All field labels are above the field, never placeholder-only.

**Loading state (after submit):**
- Buttons disabled immediately on submit.
- Full-content overlay on the main area (not full screen): animated 3-dot pulse in amber.
- Text: "Checking the item…" — no progress percentage, no technical messages.
- Never show partial results while loading.

---

### 9.2 Classification Result Screen (`/result/:eventId`)

**Header:**
```
← Back to classify                    [amber — ghost button, top left]
```

**High confidence result (≥ 0.80):**
```
┌─────────────────────────────────────┐
│  MATERIAL NAME (Fraunces 28px)      │
│  [Category badge]                   │
│                                     │
│  ┌── WHERE IT GOES ─────────────┐   │
│  │  [Bin colour block]          │   │  ← BinCard; visually dominant
│  │  Blue Dry Waste Bin          │   │
│  │  Rinse it, then place here   │   │
│  └─────────────────────────────┘   │
│                                     │
│  HOW SURE WE ARE                    │
│  [ConfidenceBar — "Very sure"]      │
│                                     │
│  CAN THIS BE RECYCLED?              │
│  [RecoveryBar — "Yes — high value"] │
│                                     │
│  ── WHAT HAPPENS NEXT ──            │
│  "This bottle will be recycled into │
│   polyester fibre or new bottles."  │
│                                     │
│  ── HOW TO SORT IT ─────────────── │
│  ✓ Rinse out any liquid             │
│  ✓ Remove the cap                   │
│  ✓ Crush it to save space           │
│  ✗ Do not leave food inside         │
│  ✗ Do not mix with food waste       │
│                                     │
│  ── RECOVERY CHANNEL ──             │
│  "Collected by informal sector      │
│   (kabadiwala)"                     │
│                                     │
│  [This doesn't look right]          │  ← ghost button; small; below the fold
│                                     │
│  [Practice mode indicator]          │
└─────────────────────────────────────┘
```

**Medium confidence result (0.55 – 0.79):**
Same layout, with these additions:
```
Below the ConfidenceBar:
┌──────────────────────────────────────┐
│ ⚠  We're not completely sure.        │
│    Does this match what you have?    │
│                                      │
│  [Yes, that's right]  [No, it's different] │
└──────────────────────────────────────┘
```
- "Yes, that's right" → calls `/feedback` with `confirmation`, then dismisses the card.
- "No, it's different" → expands the low-confidence alternative picker below.

**Low confidence result (< 0.55):**
```
Below the material name:
┌──────────────────────────────────────┐
│  ⚠  We're not sure about this one.  │
│  Please pick the closest match:      │
│                                      │
│  ○  [Option 1 name + bin colour dot] │
│  ○  [Option 2 name + bin colour dot] │
│  ○  [Option 3 name + bin colour dot] │
│  ○  None of these / I don't know    │
│                                      │
│  [Confirm my choice →]               │
└──────────────────────────────────────┘
```
- Each option shows: material name, category badge, bin colour dot.
- On confirm: calls `/feedback` with the selected class.
- "None of these / I don't know" is always an option; calls `/feedback` with no corrected class.

**Correction submitted state:**
```
┌──────────────────────────────────────┐
│  ✓  Thanks for the correction.       │
│                                      │
│  Your feedback helps LoopWise get    │
│  better for everyone in your ward.  │
│                                      │
│  [Classify another item →]           │
└──────────────────────────────────────┘
```

Rules:
- No points, stars, streaks, or rewards language.
- One action only: classify another item.
- Do not say "model" or "AI." Say "LoopWise."

---

### 9.3 Analytics Overview Screen (`/analytics`)

**Purpose:** Give a ward officer or supervisor a one-look status of how waste sorting is going.

**Layout (desktop):**
```
┌──────────────────────────────────────────────────────────────────┐
│ Overview                          [Practice Mode] [Date range ▼] │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Total    │ │ Wrongly  │ │Recycling │ │Uncertain │           │
│  │ sorted   │ │ sorted   │ │opportunity│ │ answers  │           │
│  │ 1,423    │ │ 18%      │ │  High    │ │    9%    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                    │
│  ── WARD STATUS ───────────────────────────────────────────────  │
│  [Ward status table — see below]                                  │
│                                                                    │
│  ── WHAT'S BEING SORTED ──────────────────────────────────────  │
│  [Horizontal stacked bar — material breakdown]                    │
│                                                                    │
│  ── COMMONLY CONFUSED ITEMS ──────────────────────────────────  │
│  [Top misclassifications — simple table]                          │
│                                                                    │
│  ─────────────────────────────────────────────────────────────  │
│  ℹ These figures show what was sorted through this app.          │
│    They do not represent the entire waste stream.                 │
└──────────────────────────────────────────────────────────────────┘
```

**Summary card labels (plain language replacements):**

| Technical name | Plain label | Sub-label |
|---|---|---|
| `total_events` | "Items sorted" | "Total items classified this period" |
| `contamination_rate` | "Wrongly sorted" | "Items put in the wrong bin" |
| `recovery_potential_avg` | "Recycling opportunity" | "How recyclable the sorted items are" |
| `low_confidence_rate` | "Uncertain answers" | "Items we weren't confident about" |

**Ward Status Table:**

```
Ward Name          Status          Wrongly sorted    Items sorted
─────────────────────────────────────────────────────────────────
Ward A             ● Good          8%                312
Ward B             ● Needs work    22%               198
Ward C             ● Excellent     5%                411
```

- "Status" column uses `StatusLight` component.
- Status labels: "Excellent" (<10%), "Good" (10–15%), "Needs attention" (15–20%), "Needs work" (>20%).
- Clicking a row navigates to that ward's detail page.
- No action buttons — navigation only.

**Material breakdown chart:**
- Horizontal stacked bar (Recharts `BarChart` horizontal mode or custom SVG).
- Each segment is a material category, coloured with `--color-mat-*` tokens.
- Legend below the bar, left-aligned.
- No percentages on the bar itself — tooltip on hover.

**Commonly confused items table:**

```
Item we guessed      →    Item it actually was     Times reported
───────────────────────────────────────────────────────────────────
Juice carton         →    Plastic bottle            23
Newspaper            →    Mixed paper               17
```

- "Times reported" is `count` from `top_misclassifications`.
- No action buttons. Read-only.
- Max 5 rows visible; "See all" expands to 10.

**Data honesty footer (required, non-removable):**
```
ℹ  These figures show items classified through LoopWise. They do not represent 
   every item sorted across the ward — only what was scanned or described 
   using this app.
```

---

### 9.4 Ward Detail Screen (`/analytics/ward/:wardId`)

**Layout (desktop):**
```
┌──────────────────────────────────────────────────────────────────┐
│ ← Overview > Ward A              [Practice Mode] [Last 30 days ▼]│
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 1,423    │ │ 18%      │ │  High    │ │  12%     │           │
│  │ Items    │ │ Wrongly  │ │Recycling │ │ Uncertain│           │
│  │ sorted   │ │ sorted   │ │opportun. │ │ answers  │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                    │
│  ── HOW SORTING IS CHANGING OVER TIME ─────────────────────────  │
│  [Recharts LineChart — contamination + recovery over date range]  │
│   Y-axis label: "Proportion of items sorted"                      │
│   Two lines: "Wrongly sorted" (red) / "Recycling opportunity" (green)
│                                                                    │
│  ── WHAT'S BEING SORTED ──────────────────────────────────────  │
│  [Donut or horizontal bar — material breakdown]                   │
│                                                                    │
│  ── COMMONLY CONFUSED ITEMS ──────────────────────────────────  │
│  [Same table as overview]                                         │
│                                                                    │
│  ℹ  [Data honesty footer — same as overview]                      │
└──────────────────────────────────────────────────────────────────┘
```

**Date range picker:**
- Label: "Time period"
- Options: Last 7 days / Last 30 days / Last 90 days / Custom range
- Default: Last 30 days
- Custom range: calendar picker; max 90 days enforced; error message if exceeded.
- Applying a new date range fires the API request — no separate "Apply" button needed for preset options. Custom range requires a confirm button.

**Timeseries chart:**
- Two lines: "Wrongly sorted" and "Recycling opportunity."
- Y-axis: 0% to 100%, labeled in percentages.
- X-axis: dates at sensible intervals (don't show every day if range > 14 days).
- Tooltip on hover: shows both values for that date in plain language.
- No axis grid lines — only horizontal reference line at 20% (contamination threshold).
- Reference line label: "20% threshold — needs attention."
- Responsive: on mobile, X-axis shows only month+day for every 5th date.

**Empty state:**
```
[Gentle illustration — circles in motion, amber]
No data for this ward in the selected period.
Try a different date range, or check that this ward has been active.
[← Back to Overview]
```

---

### 9.5 Help Screen (`/help`)

```
┌──────────────────────────────────────────────────────────────────┐
│ Help                                                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────┐                         │
│  │  🗺  Replay the app tour            │  ← card; tap to launch  │
│  │  Walk through how LoopWise works    │                         │
│  └─────────────────────────────────────┘                         │
│                                                                    │
│  ── MATERIAL GUIDE ─────────────────────────────────────────── │
│  Quick reference for common items.                                │
│                                                                    │
│  [Category filter: All / Plastic / Paper / Organic / ...]         │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ [Badge] Plastic   PET Bottle      Blue dry bin    High ♻ │   │
│  │ [Badge] Plastic   HDPE Container  Blue dry bin    High ♻ │   │
│  │ [Badge] Paper     Newspaper       Blue dry bin    High ♻ │   │
│  │ [Badge] Organic   Food waste      Green wet bin   None ♻ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ── ABOUT PRACTICE MODE ────────────────────────────────────── │
│  LoopWise is currently running in Practice Mode. The              │
│  classifications and data shown are for demonstration — not       │
│  real live data. This will be updated when the live system        │
│  goes active.                                                     │
└──────────────────────────────────────────────────────────────────┘
```

Material guide row: tap to expand a drawer showing full disposal instructions for that material.

---

## 10. Chart and Data Visualisation Conventions

**Colour usage in charts:**
- Use `--color-mat-*` tokens for material category data.
- Use `--color-signal-*` for performance metrics (red = contamination, green = good, amber = warning).
- Never use more than 6 distinct colours in a single chart.
- Always provide a legend. Never rely on colour alone to convey meaning (use labels too).

**Axes:**
- Always label axes with a plain-language description plus units.
- Y-axis for contamination rate: "Wrongly sorted items (%)"
- Y-axis for recovery potential: "Recycling opportunity (%)"
- Never label axes with code names or variable names.

**Tooltips:**
- Always show the plain-language metric name in tooltips, not the code name.
- Format percentages as "18%" not "0.18".
- Include the date in timeseries tooltips.

**Loading state for charts:**
- Show a skeleton shimmer in `--color-surface-2` while data loads.
- Shimmer animation: `opacity 0.4 → 0.7 → 0.4`, 1.5s cycle.
- Never show a chart with fake/empty data that looks real.

---

## 11. Language and Copy Style Guide

### Core principle
Write for someone who has never used analytics software before. If a word could be misunderstood by a sanitation worker with no tech background, replace it.

### Terminology replacements (mandatory)

| Technical term | Plain language version |
|---|---|
| Confidence score | "How sure we are" |
| Contamination rate | "Items wrongly sorted" or "Wrong bin rate" |
| Recovery potential | "Can this be recycled?" / "Recycling opportunity" |
| Classification | "Identifying the item" |
| Correction | "Tell us if we got it wrong" |
| Demo mode / Mock mode | "Practice Mode" |
| Model | "WasteIQ" |
| Material category | "Type of material" |
| Event | Never shown to users |
| Session | Never shown to users |
| Ward ID | "Your ward" (with friendly name, not code) |
| Rollup | Never shown to users |
| API error | Plain error message (see below) |

### Error messages (plain language)

| Error code | User-facing message |
|---|---|
| `INVALID_INPUT` | "Please add a photo or describe the item before submitting." |
| `IMAGE_TOO_LARGE` | "That photo is too large. Please try a smaller photo." |
| `UNSUPPORTED_FORMAT` | "We couldn't read that file. Please use a JPEG or PNG photo." |
| `INFERENCE_FAILED` | "We couldn't identify this item. Try a clearer photo or describe it instead." |
| `WARD_UNKNOWN` | "We don't recognise that ward. Please choose a ward from the list." |
| `RATE_LIMITED` | "You've submitted several corrections recently. Please wait a few minutes." |
| Network error | "We couldn't connect. Please check your internet and try again." |

### Tone
- Direct and practical — no enthusiastic UX copy ("Amazing! Great job!")
- Never talk down to the user
- Use second person ("you", "your ward")
- Sentences max 20 words
- Avoid passive voice

---

## 12. Motion and Microinteractions

### Principles
- Motion must have a functional purpose: revealing information, confirming an action, or directing attention.
- No decorative animations. No parallax. No entrance animations on page load.
- All animations must respect `prefers-reduced-motion: reduce`.

### Transitions

| Element | Property | Duration | Easing |
|---|---|---|---|
| Page navigation | opacity + translateY(8px) | 200ms | ease-out |
| Card hover | background-color, border-color | 150ms | ease |
| Button press | scale(0.98) | 100ms | ease |
| ConfidenceBar fill | width | 400ms | ease-out |
| Tour spotlight position | clip-path / box-shadow | 250ms | ease-in-out |
| Sidebar collapse | width | 200ms | ease |
| Chart lines | stroke-dashoffset draw | 600ms | ease-out |
| Toast / notification | opacity + translateY | 200ms | ease-out |

### Reduced motion
When `prefers-reduced-motion: reduce`:
- Remove all transitions and animations.
- Chart lines appear instantly.
- Tour spotlight appears instantly.
- Keep only opacity transitions (≤ 200ms).

---

## 13. Accessibility Requirements

- All interactive elements: minimum 44 × 44px touch target.
- Focus ring: `2px solid --color-focus-ring` with `2px offset` — visible on all backgrounds.
- Keyboard navigation: all flows completeable without a mouse.
- Screen reader: all charts have `<title>` and `<desc>` elements.
- Tour: focus trapped within tooltip while open; `aria-live="polite"` on tooltip content.
- Icons: decorative icons use `aria-hidden="true"`; functional icons have `aria-label`.
- Form inputs: all inputs have associated `<label>` elements (not just placeholder text).
- Error messages: associated with their input via `aria-describedby`.
- Colour is never the only indicator of meaning (always pair with text label).
- The `DemoModeIndicator` / "Practice Mode" label persists in the DOM at all times when active — it must be readable by screen readers.

---

## 14. Responsive Behaviour

### Breakpoints
```css
/* mobile-first */
@media (min-width: 768px)  { /* tablet  */ }
@media (min-width: 1024px) { /* desktop */ }
@media (min-width: 1280px) { /* wide desktop */ }
```

### Behaviour by breakpoint

| Element | Mobile | Tablet | Desktop |
|---|---|---|---|
| Navigation | Bottom tab bar | Bottom tab bar | Left sidebar |
| Sidebar | Hidden | Hidden | 240px (collapsible) |
| Classification entry | Full-screen single column | Centred 480px | Centred 520px in sidebar layout |
| Result card | Full-width card, stacked sections | Same | Two-column: bin left, details right |
| Analytics overview | Stacked cards | 2-column card grid | 4-column summary + table |
| Timeseries chart | 100% width, condensed X-axis | 100% width | 100% of content area |
| Ward status table | Card per ward (no table) | Table | Table |

---

## 15. What to Avoid — Anti-Patterns

The following patterns are explicitly prohibited. If found during visual QA, they must be corrected before the prompt is considered complete.

| Anti-pattern | Why prohibited |
|---|---|
| Any gradient (linear, radial, mesh) on backgrounds | Creates a generic "tech startup" feel |
| Glowing effects, bloom, neon borders | Wrong aesthetic for the product |
| Cards with purple-to-blue gradients | Ubiquitous generic AI dashboard pattern |
| Placeholder copy ("Coming soon", "Lorem ipsum", "TODO") | Makes a demo look unfinished |
| Percentage rings / donut progress indicators | Overused in dashboards; replaced by horizontal bars here |
| Emoji as primary communication icons | Replace with consistent icon set |
| Technical terms in the UI | See copy style guide — replace all |
| Generic hero sections with taglines | This is a tool, not a marketing page |
| Auto-advancing carousels | Inaccessible and disorienting |
| Animation on every element | Distracting; violates motion principles |
| Buttons with vague labels ("Submit", "Confirm", "OK") | Every button must say what it does |
| Tables without row hover states | Hard to read on dark backgrounds |
| Charts without legends or axis labels | Inaccessible and untrustworthy |
| Plain color-only status indicators | Always pair with text label |
