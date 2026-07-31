# Design Workflow — editable decks

This reference covers the *thinking* before the *drawing*: how to scope, structure,
and tune a deck so the python-pptx build (see `technical.md` + `scaffold_modern_deck.py`)
lands cleanly. Follow the skill's Core Principles: logic before visuals, one idea per
slide, less text more structure, visual consistency, editable over pretty.

## 1. Start: restate & propose directions

For a **series / recurring** deck (e.g. a multi-session reading salon), never default
to the previous issue's style. Restate the brief in your own words, then offer
**2–3 distinct visual directions** and let the user pick:

- Warm sand-gold (gentle, quiet)
- Morandi low-saturation (literary, refined)
- Forest-natural (green + cream, growth feel)
- Ink-wash guohua (ink + cinnabar, bookish)
- Modern minimal (black/white + one accent)
- Vintage paper (aged, nostalgic)
- Modern dark (dark base + software-logo icon wall)

For a **one-off**, confirm the **audience** first — CEO / client / team each need a
different level of detail and tone. Do not write one deck for all three.

## 2. Story line & page roster

Settle the narrative (Pyramid Principle: lead with the conclusion) and the page
roster *before* building. Agile sizing by complexity:

| Pages | Good for |
|-------|----------|
| 2–3 | pure reading/share — cover + theme + resonance/takeaway |
| 4–5 | with method — cover + Why + How + practice |
| 5–6 | full arc — cover + Why + landscape/tools + How + practice + harvest |

Write the **Action Title** (the takeaway, not a topic label) for every page up front:
- Bad:  "产品介绍"
- Good: "知识库 + Agent，让学习产生复利"

## 3. Per-page build pattern

Each page = header (logo + tag pill) + one Action Title + a structured body
(cards / flow / grid) + page number. Reuse the scaffold's `add_header`, `add_card`,
`add_pill`, `add_pageno`, `add_logo_chip`, `add_text`.

- **Cover:** big title (FONT_TITLE), one-line lead (FONT_SUB), and a 3-card value
  infographic when there's a "1+1>2" story.
- **Why:** 3 pain cards (number badge + title + desc) → one synthesis line.
- **Landscape/tools:** left hero spotlight + right logo grid (real brand glyphs, see
  technical.md §5). Cap a grid at 4 columns / 8 tiles.
- **How:** a dual-engine bar + a 4-step flow with RIGHT_ARROW connectors; close the
  loop with a "↺ keeps feeding" note.
- **Practice:** left combo (today's stack) + right numbered task cards.
- **Harvest:** a hub-and-spoke (center principle → 3 share prompts) + a side "how to
  play" card; use connectors, not boxes, for relationships.

## 4. Content rules

- **Never invent data.** Company figures, market sizes, customer cases — require the
  user to supply them, or explicitly label "假设数据".
- **Do not make strategy decisions.** The deck is an expression tool; the user owns
  the substance.
- **Copyright:** prefer free商用 icon/logo sources (brand official marks, SimpleIcons
  CDN for brand SVGs). Clearbit logo API is discontinued — do not use.
- **One font system, one palette, one icon style** across the whole deck.

## 5. Reading-salon conventions (example domain)

These are the conventions that matured around the 青少年 AI 教育 / 读书沙龙 project;
adapt to your own recurring context.

- Style is **not locked** — rotate directions per session.
- Common asset paths: `logo-youdan.png` (host logo, transparent PNG), tool logos as
  `_logo_png_*.png` (Notion / Obsidian / Logseq / Roam / 语雀 / 飞书 / flomo / 印象笔记
  / ima / workbuddy / youdan_dark). Treat these as **inputs**, never temp files.
- Posters / QR codes the user drops in `视觉助手\生成产物\` (`候选N_修改稿_vN.png`) or
  `qrcode.png` / `erweima.jpg`.
- Structure that worked: cover → Why → tools landscape → How (ima + workbuddy loop)
  → hands-on practice → harvest/share.

## 6. Tuning loop

After each real build, fold improvements back:
- New safe primitive → add to `scaffold_modern_deck.py`.
- New WPS quirk or layout pattern → `technical.md` / this file.
- Keep the WPS iron law (no gradFill, no alpha, solid shadows) untouched.
