---
name: MediSummarize AI
description: Clinical clarity for reviewing medical-document summaries against their sources.
colors:
  primary: "#087b76"
  primary-deep: "#075b59"
  rail: "#0a3d47"
  rail-active: "#11646b"
  rail-hover: "#15565f"
  rail-text: "#d3e5e8"
  ground: "#f3f7f7"
  surface: "#ffffff"
  ink: "#122e38"
  muted: "#526970"
  line: "#d1dfe3"
  banner: "#eaf2f3"
  evidence: "#f8fbfb"
  evidence-active: "#dff3ec"
  citation: "#e3f2ef"
  focus: "#1d9b91"
  ready: "#cceee4"
  ready-ink: "#125b4f"
  mock: "#fff0d0"
  mock-ink: "#87530e"
  neutral-status: "#e7edf0"
  neutral-status-ink: "#485d66"
  imported: "#e0efed"
  imported-ink: "#1b625e"
  error: "#fff0ec"
  error-ink: "#9c3528"
typography:
  display:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "clamp(38px, 3.8vw, 54px)"
    fontWeight: 650
    lineHeight: 1.1
    letterSpacing: "-.035em"
  headline:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "clamp(30px, 2.7vw, 40px)"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-.025em"
  title:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-.018em"
  subheading:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "17px"
    fontWeight: 650
    lineHeight: 1.55
  body:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  control:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
  metadata:
    fontFamily: '"Source Sans 3", ui-sans-serif, system-ui, sans-serif'
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  citation: "4px"
  compact: "6px"
  field: "7px"
  control: "8px"
  document: "9px"
  panel: "10px"
  synthetic: "30px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "24px"
  shell: "28px"
  section: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "11px 13px"
  nav-active:
    backgroundColor: "{colors.rail-active}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "13px 18px"
  status-ready:
    backgroundColor: "{colors.ready}"
    textColor: "{colors.ready-ink}"
    padding: "5px 10px"
  evidence-passage:
    backgroundColor: "{colors.evidence}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "16px"
  evidence-passage-active:
    backgroundColor: "{colors.evidence-active}"
  citation:
    backgroundColor: "{colors.citation}"
    rounded: "{rounded.citation}"
    padding: "1px 6px"
  document-selector:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.document}"
    padding: "16px 18px"
---

# Design System: MediSummarize AI

## Overview

**Creative North Star: "Clinical clarity"**

The approved world uses deep teal navigation, mist ground, white reading surfaces, humanist typography, and cool fine dividers. The interface supports careful comparison: actions are compact, source passages stay legible, and selected evidence receives a distinct tonal state.

The system is restrained and task focused. Real content determines pane height; mock output, extraction state, and imported measurements retain visible labels. The implementation is the authority for these tokens: `frontend/src/clinical.css` loads after `frontend/src/index.css` in `frontend/src/main.tsx`, preserving base structure while replacing the legacy palette and typography.

**Key Characteristics:**
- Deep teal navigation and a single teal action family.
- White reading panes on a mist ground with fine cool borders.
- Source Sans 3 throughout, with generous body leading.
- Explicit evidence selection, visible processing states, and scoped scrolling.

## Colors

The palette combines dark blue teal structure, green teal actions, and cool pale reading surfaces; the frontmatter is normative.

### Primary
- **Clinical Teal** (`primary`): primary actions, active tab strokes, and selected evidence borders.
- **Deep Clinical Teal** (`primary-deep`): primary hover state and text links.
- **Deep Teal Rail** (`rail`): persistent navigation; `rail-active`, `rail-hover`, and `rail-text` define its contrasting states.
- **Evidence Wash** (`evidence-active`): the actual selected passage fill. The root stylesheet also declares an unused selected custom property; that unused value is not a component rule.
- **Citation Wash** (`citation`): inline evidence markers connecting claims to passages.

### Secondary
- **Ready Mint** (`ready`, `ready-ink`): extracted/research-ready state and synthetic-demo chips.
- **Mock Amber** (`mock`, `mock-ink`): mock-output tags; larger mock disclosures use a lighter amber surface.
- **Imported Teal** (`imported`, `imported-ink`): imported validation/test measurements.
- **Error Coral** (`error`, `error-ink`): processing and form failures.

### Neutral
- **Mist Ground** (`ground`), **Reading White** (`surface`), and **Evidence Paper** (`evidence`): workspace, panels, and nested source passages.
- **Clinical Ink** (`ink`) and **Slate Teal** (`muted`): primary text and supporting metadata.
- **Cool Divider** (`line`) and **Banner Mist** (`banner`): boundaries and global mode disclosures.
- **Pending Slate** (`neutral-status`, `neutral-status-ink`): unrun experiment state.
- **Focus Teal** (`focus`): keyboard outline.

**The Evidence State Rule.** Keep the selected passage fill and teal border together; preserve text labels for mock, ready, imported, and unrun states.

## Typography

**Display Font:** Source Sans 3, with UI sans-serif and system fallbacks.
**Body Font:** Source Sans 3, with the same fallback stack.

The variable font is self hosted at `frontend/public/fonts/source-sans-3.ttf` with its OFL license alongside it. It serves headings, controls, source excerpts, and guide numerals; there is no separate serif or monospaced reading face.

### Hierarchy
- **Display:** authentication story heading; the display token becomes a fixed size (38px) on mobile.
- **Headline:** page heading; the responsive clamp remains active across devices.
- **Title:** section heading; split-pane titles use their own responsive clamp (`clamp(24px, 2vw, 30px)`) and become (25px) on mobile.
- **Subheading:** summary subsection; reduces to (16px) at the compact desktop breakpoint.
- **Body:** workspace copy. Evidence passages use more open leading (1.7); extracted source text uses (15px / 1.8), wraps, and has a maximum measure (85ch).
- **Control:** standard action buttons; mobile uses (14px), and small actions use (14px) with a smaller height.
- **Metadata:** generation/source details; supporting labels also use observed (13px–15px) steps. Numeric experiment values use tabular figures.

**The Reading First Rule.** Preserve body leading and wrapping when content grows; shorten layout through reflow rather than shrinking source text.

## Layout

The desktop shell is a grid with a sticky full-height navigation rail (`clamp(220px, 18.1vw, 280px)`) and a flexible content column. The white workspace bar is (62px) high. The centered workspace is capped at (1600px) with default padding (32px 28px 46px).

The record review uses equal flexible summary/evidence columns separated by (18px). White reading panes have (23px) padding, a (315px) minimum height, and natural content height. Document selectors scroll horizontally in their own strip. The evidence list may scroll vertically at a maximum height (700px) on wide screens. Experiment tables scroll inside their bordered container; below (1200px), tables retain a minimum width (720px).

- At (1200px), workspace side padding becomes (24px), review gap becomes (15px), and pane padding becomes (20px).
- At (900px), the review becomes one column, the evidence-list height cap is removed, metric notes stack, and header account text is hidden.
- At (760px), the rail becomes a top navigation strip, the workspace bar becomes (45px), and workspace padding becomes (25px 20px 36px). Document selectors retain a minimum width (310px) within their scrolling strip. Authentication columns stack vertically.

The spacing tokens collect recurrent values, not a mandatory arithmetic scale. Keep table and document overflow scoped to their containers.

## Elevation & Depth

The shipped system uses no decorative box shadows. Depth comes from the dark rail, mist workspace, white panes, nested evidence fills, and fine borders. Reading panels use a slightly stronger cool stroke than inner content. Focus is a crisp outline (3px) offset (3px), not a shadow.

**The Flat Reading Rule.** Use tonal layering and borders to separate reading surfaces; preserve clear keyboard outlines.

## Shapes

Corners are restrained and role specific: small citations, compact disclosures, softly curved fields and buttons, and slightly broader reading panels. Most content boundaries are one-pixel strokes. Synthetic-demo labels use a pill (30px), ordinary status tags use (5px), and the account avatar is circular. The upload area uses a dashed border to identify the drop target.

## Components

### Buttons
Compact and clearly weighted. Primary and secondary controls share the control radius and padding in the frontmatter, a minimum height (44px), and an icon/text gap (9px). Primary hover deepens the teal; secondary hover uses a pale teal wash (`#e9f3f3`) and a stronger border (`#87adae`). Color and border transitions last (150ms ease-out). Small actions have a minimum height (36px); mobile standard controls have (43px). Disabled controls use reduced opacity (.5) and a not-allowed cursor. Text actions use the deep primary, gaining an underline on hover.

### Chips
Status tags use readable text, compact padding, and semantic fills. Ready, mock, imported, neutral/unrun, and synthetic labels remain explicit. Synthetic pills have wider inline padding (14px); ordinary tags use (10px). Tags are informational rather than interactive controls.

### Cards / Containers
Reading panes and document-list cards use white surfaces, cool borders, and the panel radius. Nested evidence passages use the control radius, a fine divider border, and padding (16px). The active passage uses `evidence-active` plus a primary border. The experiment preview uses a pale teal grouping surface (`#e5f0f1`) and its own internal padding (22px; 18px on mobile).

### Inputs / Fields
Authentication and creation inputs use white fills, the field radius, a cool stroke (`#b9cfd3`), and a minimum height (46px). Search is a white bordered compound field, with an internal borderless input and descriptive placeholder. Selects retain native behavior, a fine cool stroke, and compact padding. Keyboard focus uses the shared outline; inline error blocks use the error pair.

### Navigation
Desktop links combine SVG line icons with text, the control radius, and a contrasting selected teal surface. Default text uses the rail text color; hover brightens it to white. Compact desktop links reduce horizontal padding; mobile links arrange icon above label in equally distributed tabs with rounded top corners. Content tabs use a primary bottom stroke (3px) for selection.

### Evidence Navigation
Inline citation buttons use the citation radius and padding, a fine teal border (`#8abdb8`), deep teal text (`#075e58`), and a mint hover (`#b9e5dc`). Selecting one marks the matching passage active and scrolls it into view. Opening the full source remains a separate text action. Passage background and border transitions last (220ms ease-out), with a scroll margin (24px).

Reduced motion disables CSS animation/transitions and sets scrolling to automatic. `frontend/src/utils/sourceNavigation.ts` also checks the preference before selecting smooth or automatic JavaScript scrolling.

### Documents and Results
Document selectors are white outlined buttons with file icons, wrapping filenames, and extraction tags. Experiment tables have a pale teal header (`#d8e9ec`), generous cell padding (14px 16px), cool row dividers, and tabular numeric columns. Their keyboard-focusable scroll container retains the shared outline.

## Do's and Don'ts

### Do:
- **Do** keep the self-hosted Source Sans 3 family across headings, body, and source excerpts.
- **Do** pair evidence selection with both a tinted fill and a teal border.
- **Do** stack reading panes at the established breakpoint and keep document/table scrolling local.
- **Do** preserve keyboard outlines and the reduced-motion preference in CSS and JavaScript navigation.
- **Do** retain visible mock, imported, ready, and unrun labels alongside semantic colors.

### Don't:
- **Don't** copy legacy green or serif overrides from the earlier stylesheet as current system tokens.
- **Don't** add decorative shadows to reading surfaces whose hierarchy is already expressed by tone and stroke.
- **Don't** shrink source text to fit the synthetic mockup's shorter content.
- **Don't** conflate an inline citation selection with the separate action to open the source page.

Evidence checked: the final style cascade, route and shell components, summary review, results table, source-navigation helper, font assets, and desktop/mobile review captures in `.impeccable/review/`. The approved code-led direction supersedes exact mockup matching gates. No craft-floor defect or known implementation drift is canonized here; the direction contract supplies the confirmed qualitative language.
