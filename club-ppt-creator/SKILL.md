---
name: club-ppt-creator
agent_created: true
description: This skill should be used when producing presentation decks (PPT/PPTX) that must remain fully editable in WPS Office and Microsoft PowerPoint. It covers the python-pptx native generation workflow with no HTML-to-image conversion, hard-won WPS compatibility rules (no handwritten gradients, no alpha/transparency hacks), correct Chinese font rendering (the latin/ea/cs pitfall), a 3-font Windows system-font system, solid-color soft shadows, logo recoloring, and a no-render self-check. Trigger phrases include "做一份 PPT", "生成 pptx", "可编辑幻灯片", "WPS 兼容的幻灯片", "用 python-pptx 做 deck", or any request to build a business report, pitch deck, training material, or salon presentation as an editable file.
---

# Python-PPTX Editable Deck

## Overview

Build professional, **print-grade, fully editable** slide decks with `python-pptx`
at a fixed 1280×720 canvas. The deck is generated **natively** as `.pptx` — text
and shapes stay editable (no baking content into images) so the user can fine-tune
later. Every technique in this skill is hardened for **WPS Office + PowerPoint**
compatibility, which is stricter than PowerPoint alone.

This skill is the "native editable" alternative to HTML-based deck skills
(e.g. `ppt-implement`, `guizang-ppt-skill-png`). Use it whenever the user needs
an editable file rather than a pixel-perfect web render.

## When To Use

- User asks for a PPT/deck and **editable output** matters (business report, pitch
  deck, training material, conference talk, reading-salon share).
- User explicitly mentions WPS compatibility, or the target reader opens files in WPS.
- Rebuilding or extending an existing python-pptx generator.
- Diagnosing "fonts not showing", "broken gradients", or "shadow/transparency lost
  in WPS" in a generated deck.

Do **not** use this skill for one-off pixel-perfect web slides where editability is
unwanted — that is the HTML-route skill's job.

## Core Principles

1. **Logic before visuals** — settle the story line (Pyramid Principle) and page
   roster before drawing anything.
2. **One slide, one idea** — the title IS the conclusion (Action Title); body
   supports it.
3. **Less text, more structure** — if a slide exceeds ~50 Chinese characters of body
   copy, switch to a diagram / card grid / flow.
4. **Visual consistency** — one font system, one palette, one icon style, generous
   whitespace; never mix aesthetics.
5. **Editable over pretty** — text in text boxes, charts/shapes as native objects;
   only use raster images for logos/photos.
6. **WPS iron law** (non-negotiable):
   - ✅ Solid fills, official shapes (rectangle / rounded-rect / oval / connector).
   - ✅ Soft shadow via standard `a:outerShdw` with a **solid** `a:srgbClr`.
   - ❌ **Never** hand-write `a:gradFill` (manual gradient).
   - ❌ **Never** hand-write `a:alpha` (transparency) on a shape's fill.
   - ❌ **Never** use character-spacing / ea-cs font hacks to fake effects.
   - Use a bright Tailwind-600-level solid color instead of a "gradient".

## Workflow

### Step 1 — Understand & propose style directions
For a series/recurring deck (e.g. multi-session salon), do **not** reuse the last
style by default. Restate the brief, then offer **2–3 distinct visual directions**
(e.g. warm sand-gold / Morandi low-saturation / forest-natural / ink-wash / modern
minimal / vintage-paper / modern-dark logo wall) and let the user pick. For a
one-off, confirm the audience (CEO / client / team) — tone and detail differ.

### Step 2 — Confirm story line & page roster
Agile structure (2–6 pages):
- 2–3 pages → pure reading/share (cover + theme + takeaway)
- 4–6 pages → with method/operation (cover + Why + How + practice + harvest)

Write the Action Title for each page up front.

### Step 3 — Build with the scaffold
Start from `scripts/scaffold_modern_deck.py` (a clean, project-agnostic version of
the proven 6-page generator). It already provides the safe primitives:
`add_text`, `set_font`, `set_run_fonts`, `patch_theme_fonts`, `add_card`,
`add_soft_shadow`, `add_pill`, `add_pageno`, `add_logo_chip`, `add_bg`. Copy it into
the working project, then replace the placeholder copy/colors with the real content.

### Step 4 — Apply WPS-safe techniques
Follow `references/technical.md` precisely for:
- Chinese font rendering fix (`set_run_fonts` + `patch_theme_fonts`) — **the #1
  cause of "fonts didn't show"**.
- 3-font Windows system-font system (Microsoft YaHei / DengXian / DengXian Light).
- Solid-color soft shadow (`add_soft_shadow`).
- Logo recoloring with PIL (white→transparent, rest→solid target color).
- Bright-only palette (no gradients).

### Step 5 — Self-check (no render environment)
This environment has **no LibreOffice/Playwright**. Verify correctness by geometry +
XML assertions instead of visual inspection (see `references/technical.md` →
"Self-check without a renderer"). Assert: all shape bounds inside 1280×720, global
0 `gradFill`, 0 `alpha`, every page has its expected `outerShdw` count, and the
theme's `ea`/`latin`/`cs` are set.

### Step 6 — Deliver
Save the final `.pptx`. Because some preview tools error on Chinese/space paths, also
copy an **ASCII-named** preview (e.g. `_preview_deck.pptx`) for in-app preview, and
tell the user to open the real file from its folder. Keep all brand/tool logo assets
(`_logo_png_*.png`) — they are inputs, not temp files.

## Bundled Resources

- **`scripts/scaffold_modern_deck.py`** — ready-to-fork generator with all safe
  primitives and a 6-page example layout. Read/patch it per project.
- **`references/technical.md`** — the WPS-safe technical playbook: font fix,
  shadows, logo recolor, palette, self-check assertions, environment gotchas.
- **`references/workflow.md`** — design-process guidance: style directions, story
  line, page structures, audience tuning, salon-style conventions.

## Notes / Tuning

This skill is meant to be **continuously tuned**. After each real deck build, fold
new lessons back into `references/technical.md` or `references/workflow.md` (and the
scaffold if a primitive improved). Keep the WPS iron law intact.
