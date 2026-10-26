---
version: alpha
name: SupportFlow
description: A banking-support triage workbench organized around a routing slip.
colors:
  primary: "#3159C9"
  background: "#F5F7FB"
  surface: "#FFFFFF"
  text: "#192B46"
  muted: "#53647B"
  border: "#D8E0ED"
  success: "#167459"
  warning: "#946015"
  danger: "#B53445"
  rail: "#EAF0FA"
typography:
  display:
    fontFamily: "Bahnschrift, Arial Narrow, sans-serif"
  body:
    fontFamily: "Segoe UI, Arial, sans-serif"
  mono:
    fontFamily: "Cascadia Code, Consolas, monospace"
rounded:
  DEFAULT: "12px"
spacing:
  page-max: "1160px"
  section-gap: "24px"
components:
  route-card:
    rounded: "12px"
  button:
    height: "40px"
---

# SupportFlow design system

## Overview

This is a product workbench for a student portfolio and interview demonstrations.
Its primary job is to turn one banking-support message into an inspectable routing
suggestion. The physical reference is a dispatch desk's routing slip: message,
classification, and destination. The white result slip with a blue edge and dashed
handoff line is the single visual signature. The remaining interface stays quiet.

English UI and English model inputs. No geographic market or real banking deployment
is claimed. Desktop-first, with stacked panels on narrow screens. No Japan-market
flows, money movement, authentication, or customer-system integration.

**Token ownership:** `assets/tokens.json` is the canonical runtime source; this file
mirrors its accepted values. `supportflow/ui.py` turns colors into `--sf-*` CSS variables,
font roles into `--sf-display`, `--sf-body`, `--sf-mono`, and geometry into `--sf-radius`
and `--sf-max`. `assets/app.css` consumes those variables. `.streamlit/config.toml`
adapts primary, background, rail, and text tokens to Streamlit's native controls.
`tests/test_project.py::test_theme_tokens_do_not_drift` checks the mirrored colors.

## Colors

Blue primary actions, cool light-gray canvas, white results, dark blue text.
Success and warning colors label readiness alongside words; color never carries
status alone. Muted text remains dark enough for readable instructions. Light mode
is the supported product theme. Forced-colors uses system scrollbar and border colors.

## Typography

Bahnschrift gives titles and result destinations a practical, directional voice.
Segoe UI handles descriptions and fields; Cascadia Code handles compact routing
labels. All fonts use local fallbacks to avoid remote requests and font-swap shifts.
Headings scale from 32px to 46px. Paragraph measure is capped near 680px.

## Layout

Persistent sidebar navigation with four views. Triage uses a message panel beside
the destination slip, collapsing naturally on mobile. Main width is capped at 1160px.
Long forms scroll with the document; only data tables have bounded internal scroll.
The report uses two columns on desktop and stacks on narrow screens. No global
viewport-height constraints or decorative KPI rows on the triage landing screen.

## Elevation & Depth

Use borders and tonal surfaces, not floating shadows or glass effects. Result cards
stand out through their blue edge. Native Streamlit popovers own overlay elevation.

## Shapes

12px result/metric corners, a 5px routing-card edge, and simple separators.
The dashed route footer encodes the handoff rather than a decorative pattern.

## Components

All buttons, inputs, selectboxes, radios, sliders, alerts, uploaders, and downloads
use Streamlit's maintained controls. `supportflow/ui.py` owns non-interactive headings
and routing cards. No custom clickable HTML. Readiness uses text and semantic tone.

Primary action is Classify ticket or Classify batch. Export actions are secondary.
Loading uses a spinner; empty screens describe the next action. Invalid input keeps
the entered message and shows a corrective error. Changes to input or threshold
invalidate the visible result until classification runs again. Disabled controls
retain native semantics; focus is visible. Native Streamlit hover/pressed states are
preserved. CSS adds a token-based focus outline and pointer treatment.

Select/listbox ownership is authored by Streamlit's built-in selectbox. No native
date widgets, destructive dialogs, remote search, or custom toast system are needed.
Textareas have a 200px initial height and internal scrolling, with resize disabled.
Global scrollbar tokens apply to new scroll containers automatically.

Copy describes suggestions, never successful real-world dispatch. Review records
are explicitly session-only. Tables show a bounded maximum of 250 user-uploaded
tickets; dataset tables use internal scrolling. Charts include numeric alternatives.
Motion is minimal and disabled when reduced motion is requested. The arrow in the
wordmark is non-interactive; all actions have text labels.

## Do's and Don'ts

- Do keep the ticket and routing explanation adjacent on desktop.
- Do label uncertainty, data scope, and evaluation conditions honestly.
- Do use shared model and presentation helpers across workflows.
- Don't imitate a marketing landing page, neon AI dashboard, or financial trading screen.
- Don't imply that a model score is the probability the prediction is correct.
- Don't send customer text to an external model or silently store it on disk.
