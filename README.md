# salon-poster-pil

A reusable skill for turning a **phone-vertical salon / event poster** into a finished PIL-rendered image. Two complementary routes:

- **Route A · Real-template remix** — take a Gaoding / Canva exported PNG, remove watermark, redraw info card, draw geometric icons, composite logo + QR.
- **Route B · From-scratch full-content render (default)** — when real templates are unreachable (Gaoding/Canva anti-scrape) or you need pixel-precise, fully-editable text: use a Pexels / ImageGen base image and draw **every** text layer in PIL.

> **Route B is the default.** Real template platforms block programmatic access (Gaoding → 405, Canva → Cloudflare), and AI image text is error-prone. Route B is more reliable and gives exact control.

## What you get

- ✅ **Route B**: full-content PIL render with a base image (Pexels free CDN / ImageGen)
- ✅ **Dual-mode auto-detect**: light-base → dark text / dark-base → light text (readable on any base)
- ✅ **Ardot 28px hard floor**: every text node ≥28px (self-check assertion)
- ✅ **Artistic quote**: gradient fill + stroke + drop shadow (`_art_text_layer`)
- ✅ **Font hierarchy**: bold YaHei title / YaHei subtitle / Kaiti quote (clear differentiation)
- ✅ **Theme-driven base search**: search by theme essence (e.g. "free-flowing inspiration" → ink diffusion / watercolor / bokeh), not literal symbols
- ✅ **Pixel-level self-check**: text not overlapping QR, all fonts ≥28px
- ✅ Configurable scripts — edit the CONFIG block (or env vars), run, done
- (Route A) ✅ Watermark removal via `cv2.inpaint` + spatial constraint, info-card repaint, geometric icons, logo + QR composite

## Bundle structure

```
salon-poster-pil/
├── SKILL.md                      # Triggers, red lines, dual-route workflow
├── README.md                     # This file
├── references/
│   ├── pil_full_render.md        # Route B deep-dive + artistic-text / dual-mode / 28px code
│   ├── pitfalls.md               # Failure modes from real runs (anti-scrape, size mismatch, <28px…)
│   ├── watermark_inpaint.md      # (Route A) Watermark removal method + red lines
│   ├── info_card_layout.md       # (Route A) Info-card coordinates / sizes / icons
│   └── selfcheck.md              # Self-check checklist (incl. 28px assertion)
└── scripts/
    ├── render_full.py            # Route B: from-scratch full render (CONFIG + env overrides)
    └── remix_poster.py           # Route A: real-template remix
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
pip install pillow numpy
# Route A also needs:
pip install opencv-python-headless
```

## Quick start — Route B (default)

```bash
# 1. Prepare a base image (Pexels direct link or ImageGen export)
#    Pexels: https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&h=1600
# 2. Edit the CONFIG block in scripts/render_full.py
#    (TITLE / SUBTITLE / QUOTE / VALUES / INFO_LINES / BASE_PNG / SALON_MODE / ART_QUOTE)
# 3. Run
python scripts/render_full.py
```

Environment overrides:

| Var | Default | Meaning |
|-----|---------|---------|
| `SALON_BASE` | CONFIG | base image |
| `SALON_OUTPUT` | `output_full.png` | result |
| `SALON_LOGO` | CONFIG | logo |
| `SALON_QR` | CONFIG | QR code |
| `SALON_MODE` | `auto` | `auto` \| `light` \| `dark` |
| `SALON_TITLE` / `SALON_SUB` / `SALON_QUOTE` / `SALON_BADGE` | CONFIG | copy |

## Quick start — Route A (real-template remix)

```bash
# Edit CONFIG in scripts/remix_poster.py (INFO_LINES / WATERMARK_REGION), then:
python scripts/remix_poster.py
```

## Red lines (must keep)

- PIL route only; **no pure HTML/code generation** unless user asks.
- **Ardot 28px floor**: all text nodes ≥28px (decorative badge shrink = user-specified exception).
- Base image always `resize`d to target size (ImageGen may return 832×1216 ≠ 848×1200).
- (Route A) Watermark: inpaint + spatial constraint; **no global color detection, no patch overlay**.
- (Route A) Info card: repaint the whole band; **no patching over old text**.
- (Route A) Icons: geometric lines; **no font glyphs**.

## License

MIT.
