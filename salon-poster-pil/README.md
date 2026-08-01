# salon-poster-pil

A reusable skill for turning a **real-platform salon/event poster PNG** (Gaoding / Canva export) into a finished phone-vertical poster with PIL — watermark removal, info-card redraw, geometric icons, logo + QR composite, and a pixel-level self-check.

> "Real template aesthetics + accurate event info, without hand-drawing from scratch in HTML."

## Why this skill

Most poster workflows either (a) generate from zero in code/HTML — losing the polish of real design platforms, or (b) leave platform watermarks and mismatched copy on the export. This skill takes a **real template PNG** as the base and does **PIL 二次修改** so you keep the design's look while fixing the content: remove watermark, redraw the info card, draw clean geometric icons, and composite your logo + QR code.

## What you get

- ✅ **Watermark removal** via `cv2.inpaint` with spatial constraint (no global color detection, no patch overlay)
- ✅ **Info-card redraw** — whole bottom band repainted, no residue from old text
- ✅ **Geometric icons** (clock / pin / yen) drawn with lines, never font glyphs
- ✅ **Logo recolor** to black-transparent, composited top-right
- ✅ **QR composite** at 130×130 with rounded cream backing
- ✅ **Pixel-level self-check** (watermark residual = 0, text not overlapping QR)
- ✅ A configurable **script** (`scripts/remix_poster.py`) — edit the CONFIG block, run, done

## Bundle structure

```
salon-poster-pil/
├── SKILL.md                      # Trigger, red lines, workflow
├── README.md                     # This file
├── references/
│   ├── watermark_inpaint.md      # Watermark removal method + red lines
│   ├── info_card_layout.md       # Info-card coordinates / sizes / icons (verified)
│   └── selfcheck.md              # Self-check checklist + pixel criteria
└── scripts/
    └── remix_poster.py           # Configurable poster remix script
```

## Install (cross-platform)

Drop the `salon-poster-pil/` folder into your agent's skills directory:

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/salon-poster-pil/` |
| WorkBuddy | `~/.workbuddy/skills/salon-poster-pil/` |
| Codex / OpenClaw / QClaw / Hermes | consult your platform's skill docs; usually `~/.{agent}/skills/` |

Dependencies (Python):

```bash
pip install pillow numpy opencv-python-headless
```

## Quick start

```bash
# 1. Put your assets next to the skill (or set env vars)
#    assets/input.png   - the real-platform poster export (may have watermark)
#    assets/logo.png    - your transparent logo
#    assets/qrcode.png  - your sign-up QR

# 2. Edit the CONFIG block in scripts/remix_poster.py
#    (INFO_LINES = your time / place / fee; WATERMARK_REGION if needed)

# 3. Run
python scripts/remix_poster.py
```

The script writes `assets/output.png` (override with `SALON_OUTPUT`).

### Environment overrides

All paths can be set via env vars so the skill works on any machine:

| Var | Default | Meaning |
|-----|---------|---------|
| `SALON_INPUT` | `assets/input.png` | base poster |
| `SALON_OUTPUT` | `assets/output.png` | result |
| `SALON_LOGO` | `assets/logo.png` | logo |
| `SALON_QR` | `assets/qrcode.png` | QR code |
| `SALON_FONT` | `C:/Windows/Fonts/msyh.ttc` | CJK font (set to your system font) |

## Red lines (must keep)

- Real-template + PIL remix only; **no pure HTML/code generation**.
- Watermark: inpaint + spatial constraint; **no global color detection, no patch overlay**.
- Info card: repaint the whole band; **no patching over old text**.
- Icons: geometric lines; **no font glyphs**.

## License

MIT.
