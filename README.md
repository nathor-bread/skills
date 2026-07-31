# club-ppt-creator

A reusable skill for building **fully editable, print-grade PowerPoint decks** with `python-pptx` — hardened for **WPS Office + Microsoft PowerPoint** compatibility.

> "A good deck is clear logic + consistent visuals, not fancy animations."

## Why this skill

Most PPT skills bake content into images (HTML → PNG) for pixel-perfect looks. This one goes the **native, editable** route: every text box, card, and shape stays a real Office object so the user can fine-tune afterwards. It is the editable alternative to HTML-render deck skills.

## What you get

- ✅ **python-pptx native generation** at a fixed 1280×720 canvas
- ✅ **WPS iron law** — no handwritten gradients, no alpha/transparency hacks
- ✅ **Correct Chinese font rendering** (the latin/ea/cs pitfall, fixed)
- ✅ **3-font Windows system-font system** (YaHei / DengXian / DengXian Light)
- ✅ **Solid-color soft shadows** that survive WPS
- ✅ **Logo recoloring** with PIL (white → transparent, rest → solid)
- ✅ **No-render self-check** (geometry + XML assertions)
- ✅ A ready-to-fork **scaffold** (`scripts/scaffold_modern_deck.py`)

## Bundle structure

```
club-ppt-creator/
├── SKILL.md                      # Trigger, principles, workflow
├── README.md                     # This file
├── references/
│   ├── technical.md              # WPS-safe playbook: fonts, shadows, logos, palette, self-check
│   └── workflow.md               # Design process: style directions, story line, page structure
└── scripts/
    └── scaffold_modern_deck.py   # Forkable generator with all safe primitives
```

## Install (cross-platform)

Drop the `club-ppt-creator/` folder into your agent's skills directory:

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/club-ppt-creator/` |
| WorkBuddy | `~/.workbuddy/skills/club-ppt-creator/` |
| Codex / OpenClaw / QClaw / Hermes | consult your platform's skill docs; usually `~/.{agent}/skills/` |

No dependencies beyond `python-pptx` (and `Pillow` if you recolor logos):

```bash
pip install python-pptx pillow
```

## Quick start

```bash
# 1. Fork the scaffold into your project
cp scripts/scaffold_modern_deck.py my_deck.py

# 2. Edit the placeholder copy / colors / pages
# 3. Run
python my_deck.py
```

The scaffold writes a WPS-safe, fully editable `.pptx`.

## WPS iron law (non-negotiable)

- ✅ Solid fills, official shapes (rectangle / rounded-rect / oval / connector)
- ✅ Soft shadow via standard `a:outerShdw` with a **solid** `a:srgbClr`
- ❌ Never hand-write `a:gradFill` (manual gradient)
- ❌ Never hand-write `a:alpha` (transparency) on a shape's fill
- ❌ Never use character-spacing / ea-cs font hacks
- Use a bright Tailwind-600-level solid color instead of a "gradient"

## License

MIT — do whatever you want, just keep the WPS iron law.
