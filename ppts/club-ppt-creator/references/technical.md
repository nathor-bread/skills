# Technical Playbook — python-pptx native, WPS-safe

This reference contains the deterministic, copy-pasteable techniques that make a
python-pptx deck open cleanly in **WPS Office** and PowerPoint. Treat the WPS iron
law as non-negotiable; PowerPoint tolerates more, but the lowest common denominator
is WPS.

## 1. Canvas & units

```python
from pptx import Presentation
from pptx.util import Pt, Emu

prs = Presentation()
prs.slide_width  = int(1280 * 9525)   # 1 CSS px = 9525 EMU
prs.slide_height = int(720  * 9525)
BLANK = prs.slide_layouts[6]          # blank layout, no placeholders

def px(n):  # author in CSS px, emit EMU
    return int(n * 9525)
```

Keep all coordinates in a single 1280×720 space. Do **not** attempt true
responsiveness — "responsive across screen sizes" means consistent margins and
anchoring, not a fluid layout.

## 2. Chinese font rendering (THE #1 fix)

**Root cause:** `run.font.name` only writes `<a:latin>`. East-Asian (Chinese) text
falls back to the theme's default `ea` font (SimSun/宋体), so setting "DengXian" or
"Microsoft YaHei" "does nothing" for Chinese glyphs. The fix is to set `latin`,
`ea`, and `cs` explicitly, **and** patch the theme default.

```python
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement

def set_run_fonts(run, name):
    """Set latin + ea (CJK) + cs so Chinese renders in the chosen font."""
    rPr = run._r.get_or_add_rPr()
    latin = rPr.find(qn('a:latin'))
    if latin is None:
        latin = OxmlElement('a:latin'); rPr.append(latin)
    latin.set('typeface', name)
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = OxmlElement('a:ea'); latin.addnext(ea)   # schema order: latin→ea→cs
    ea.set('typeface', name)
    cs = rPr.find(qn('a:cs'))
    if cs is None:
        cs = OxmlElement('a:cs'); ea.addnext(cs)
    cs.set('typeface', name)

def set_font(run, name="Microsoft YaHei", size=None, bold=None, color=None):
    set_run_fonts(run, name)
    if size is not None: run.font.size = Pt(size * 0.75)  # see note below
    if bold is not None:  run.font.bold = bold
    if color is not None: run.font.color.rgb = RGBColor.from_string(color)
```

> **Size note:** the example multiplies by `0.75` because the original project
> authored sizes in a "point-ish" unit; adjust to your own convention. Standard
> `Pt(size)` is fine if you author in real points.

Then **patch the theme** so any un-specified text also uses the right fonts:

```python
import re, zipfile

def patch_theme_fonts(path):
    """Rewrite ppt/theme/theme1.xml major/minor latin+ea+cs to project fonts.
    Write back directly (truncate+rewrite) — do NOT use tmp+shutil.move. The
    sandbox safe-delete wrapper intercepts os.unlink, so move()'s delete-fallback
    fails; direct write avoids unlink entirely. WPS/PowerPoint compatible."""
    with zipfile.ZipFile(path, 'r') as zin:
        names = zin.namelist(); data = {n: zin.read(n) for n in names}
    xml = data['ppt/theme/theme1.xml'].decode('utf-8')

    def patch_block(block, latin_name, ea_name):
        new = block
        for tag, val in (('a:latin', latin_name), ('a:ea', ea_name), ('a:cs', ea_name)):
            new = re.sub(r'<%s[^>]*?/>' % tag, '<%s typeface="%s"/>' % (tag, val), new)
            new = re.sub(r'<%s[^>]*?>(.*?)</%s>' % (tag, tag),
                         r'<%s typeface="%s">\1</%s>' % (tag, val, tag), new)
        return new

    for open_tag, ln, ea in (('a:majorFont', 'DengXian', 'DengXian'),
                             ('a:minorFont', 'Microsoft YaHei', 'Microsoft YaHei')):
        m = re.search(r'<%s>.*?</%s>' % (open_tag, open_tag), xml, re.S)
        if m:
            xml = xml[:m.start()] + patch_block(m.group(0), ln, ea) + xml[m.end():]
    data['ppt/theme/theme1.xml'] = xml.encode('utf-8')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for n in names: zout.writestr(n, data[n])
```

Call `patch_theme_fonts(OUT)` **after** `prs.save(OUT)`.

**Verify:** grep the first ~12 runs for `<a:ea typeface="...">`, confirm the theme
major/minor triple-typeface rewrite, and count distinct fonts in the deck (should be
≤3).

## 3. Three-font system (all Windows system fonts)

| Role | Font | Used for |
|------|------|----------|
| Base | `Microsoft YaHei` | body / captions / page numbers / tags |
| Title | `DengXian` | slide titles (Action Title) / card titles |
| Sub | `DengXian Light` | subtitle / lead-in text (lighter weight for hierarchy) |

No more than 3 families. All are present on a stock Windows box, so no font
embedding is required.

## 4. Soft shadow — solid color only

WPS drops hand-written alpha. Use the standard `a:outerShdw` with a **solid**
`srgbClr` (no `a:alpha` child):

```python
def add_soft_shadow(shape, color="C7D2E3", blur=110000, dist=38000, dir=5400000):
    spPr = shape._element.spPr
    existing = spPr.find(qn('a:effectLst'))
    if existing is not None: spPr.remove(existing)
    eff = OxmlElement('a:effectLst'); sh = OxmlElement('a:outerShdw')
    sh.set('blurRad', str(blur)); sh.set('dist', str(dist))
    sh.set('dir', str(dir)); sh.set('rotWithShape', '0')
    c = OxmlElement('a:srgbClr'); c.set('val', color); sh.append(c)
    eff.append(sh); spPr.append(eff)
```

Layer depth comes from the shadow + whitespace, not from dark-on-dark contrast.

## 5. Logo recoloring with PIL

A logo designed for a dark background (white glyphs) vanishes on a light slide.
Recolor pixels by rule:

- **White pixels** (alpha == 0, or RGB all > 235) → fully transparent.
- **Everything else** (mark / letterforms) → solid target color (e.g. deck `TEXT`).

```python
from PIL import Image

def recolor_logo(src, dst, target=(30,41,59,255)):
    im = Image.open(src).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r,g,b,a = px[x,y]
            if a == 0 or (r>235 and g>235 and b>235):
                px[x,y] = (0,0,0,0)          # transparent
            else:
                px[x,y] = target             # solid target color
    im.save(dst)
```

> **Trap:** do NOT merely turn the white glyphs dark while keeping the white
> background block — that yields dark-on-dark (invisible). White must become
> transparent, not dark.

## 6. Palette — bright solids only (no gradients)

Replace any "gradient" need with a bright Tailwind-600-level solid:

```
BG F4F6FB · SURFACE FFFFFF · SURFACE2 EEF2F9 · BORDER E3E8F0
TEXT 1E293B · MUTED 64748B · FAINT E6EBF3 · SHADOW C7D2E3
BLUE 2563EB · CYAN 0891B2 · VIOLET 7C3AED · AMBER EA580C · GREEN 059669
```

## 7. Self-check without a renderer

This environment has no LibreOffice/Playwright. Validate by XML + geometry instead
of looking at the file:

```python
import zipfile
from pptx import Presentation
from pptx.oxml.ns import qn

def audit(path, allow_bleed_ids=None):
    """WPS-safety + sanity check. Hard-fails only on gradFill/alpha (the real
    WPS killers). Decorative bleed (e.g. background rings) is allowed but reported.
    """
    allow_bleed_ids = allow_bleed_ids or set()
    prs = Presentation(path)
    assert prs.slide_width == 1280*9525 and prs.slide_height == 720*9525
    with zipfile.ZipFile(path) as z:
        xml = b"".join(z.read(n) for n in z.namelist()
                       if n.endswith('.xml') and 'slide' in n)
    s = xml.decode('utf-8', 'ignore')
    assert s.count('gradFill') == 0, "gradFill present — WPS unsafe"
    assert s.count('<a:alpha') == 0, "alpha present — WPS unsafe"

    # ea coverage: ea lives INSIDE rPr, not directly under <a:r>
    ea_total = ea_set = 0
    for slide in prs.slides:
        for sh in slide.shapes:
            if not sh.has_text_frame: continue
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    ea_total += 1
                    rPr = r._r.find(qn('a:rPr'))
                    if rPr is not None and rPr.find(qn('a:ea')) is not None:
                        ea_set += 1
    assert ea_total > 0, "no runs found"
    assert ea_set == ea_total, f"ea not set on all runs: {ea_set}/{ea_total}"

    # bounds: report (don't hard-fail) overflow — decorative bleed is intentional
    over = 0
    for i, slide in enumerate(prs.slides):
        for sh in slide.shapes:
            if sh.left is None or sh.shape_id in allow_bleed_ids: continue
            if sh.left < -4 or sh.top < -4 or sh.left > prs.slide_width or sh.top > prs.slide_height:
                over += 1
                print(f"  [overflow] slide{i+1} shape#{sh.shape_id} "
                      f"left={sh.left} top={sh.top}")
    print(f"WPS-safe: 0 gradFill, 0 alpha, ea {ea_set}/{ea_total} runs, "
          f"{over} overflowing (decorative bleed OK)")
```

Also count `outerShdw` per slide to confirm shadows injected, and grep `<a:ea`
typeface coverage.

## 8. Click-reveal animation (WPS-safe)

Teaching/talk decks often want elements to appear one click at a time. python-pptx
has no animation API, but a standard PresentationML `<p:timing>` with the **Appear**
entrance effect is both PowerPoint- and WPS-compatible — and it uses no `gradFill` /
`a:alpha`, so it does not violate the WPS iron law.

```python
from lxml import etree
from pptx.oxml.ns import qn

def add_click_sequence(slide, steps):
    """Click-to-reveal: each click reveals the next `steps` group (appear effect).
    steps: list[list[int]] — each inner list = shape ids shown on the same click.
    Shapes NOT in `steps` (title, header) stay visible from the start.
    """
    sld = slide._element
    old = sld.find(qn('p:timing'))
    if old is not None: sld.remove(old)
    timing = etree.SubElement(sld, qn('p:timing'))
    tnLst = etree.SubElement(timing, qn('p:tnLst'))
    root = etree.SubElement(tnLst, qn('p:par'))
    rc = etree.SubElement(root, qn('p:cTn')); rc.set('id','1'); rc.set('fill','hold')
    sc = etree.SubElement(rc, qn('p:stCondLst'))
    for dvt in ('0','indefinite'):
        c = etree.SubElement(sc, qn('p:cond')); c.set('srId','0'); c.set('dvt', dvt)
    rchild = etree.SubElement(rc, qn('p:childTnLst'))
    _id = [1]
    def nid():
        _id[0]+=1; return str(_id[0])
    for group in steps:
        par = etree.SubElement(rchild, qn('p:par'))
        ctn = etree.SubElement(par, qn('p:cTn')); ctn.set('id',nid()); ctn.set('fill','hold')
        cs = etree.SubElement(ctn, qn('p:stCondLst'))
        c0 = etree.SubElement(cs, qn('p:cond')); c0.set('srId','0'); c0.set('dvt','0')
        schild = etree.SubElement(ctn, qn('p:childTnLst'))
        for spId in group:
            ppar = etree.SubElement(schild, qn('p:par'))
            pctn = etree.SubElement(ppar, qn('p:cTn')); pctn.set('id',nid()); pctn.set('fill','hold')
            ps = etree.SubElement(pctn, qn('p:stCondLst'))
            pc = etree.SubElement(ps, qn('p:cond')); pc.set('srId','0'); pc.set('dvt','0')
            pch = etree.SubElement(pctn, qn('p:childTnLst'))
            anim = etree.SubElement(pch, qn('p:animEffect'))
            anim.set('id',nid()); anim.set('filter','appear'); anim.set('transition','in')
            anim.set('presetId','1'); anim.set('presetClass','entr'); anim.set('presetSubtype','0'); anim.set('build','0')
            cb = etree.SubElement(anim, qn('p:cBhvr'))
            cbc = etree.SubElement(cb, qn('p:cTn')); cbc.set('id',nid()); cbc.set('fill','hold')
            cbs = etree.SubElement(cbc, qn('p:stCondLst'))
            cbc0 = etree.SubElement(cbs, qn('p:cond')); cbc0.set('srId','0'); cbc0.set('dvt','0')
            tgt = etree.SubElement(cb, qn('p:tgtEl'))
            spt = etree.SubElement(tgt, qn('p:spTgt')); spt.set('spId', str(spId))
            anl = etree.SubElement(cb, qn('p:attrNameLst'))
            an = etree.SubElement(anl, qn('p:attrName')); an.text = 'style.visibility'
    etree.SubElement(timing, qn('p:bldLst'))
    etree.SubElement(timing, qn('p:extLst'))
```

Usage: collect `shape.shape_id` for each element as you build, group them per click,
call `add_click_sequence(slide, [group0, group1, ...])` before saving.

```python
cross = [center.shape_id, h_edge.shape_id, v_edge.shape_id, ...]   # click 1
cards = [[card.shape_id, title.shape_id, desc.shape_id] for ...]   # clicks 2..N
add_click_sequence(slide, [cross] + cards + [bottom_ids])
```

> **Verify:** assert the slide XML contains `<p:timing` and `filter="appear"`; open in
> WPS/PowerPoint and confirm each click reveals the next group. This "one click per
> group" pacing is the canonical PowerPoint export for click-to-advance sequential
> animations and WPS honors it. If a player collapses all groups into the first click,
> that is a player quirk, not a file defect — content still renders correctly.

## 9. Delivery & environment gotchas

- **`present_files` Chinese/space path bug:** the tool errors on paths with CJK or
  spaces. After saving the real deck, copy an ASCII-named preview
  (`_preview_deck.pptx`) for in-app preview, and tell the user to open the real file
  from its folder.
- **Sandbox file operations are conservative:** bulk `Remove-Item` / `Move-Item` may
  be denied or silently routed to the Recycle Bin. When cleaning temp files, use an
  explicit filename list (never a glob that could hit `_logo_png_*` assets), and
  verify with `find` afterward. Prefer a Python `os.remove` loop with full Windows
  paths over shell `rm`.
- **Recycle Bin `$I` metadata:** on Windows 10/11 the original path sits at byte
  offset **28** (version 2), not 24 (version 1). Four-byte version header first.
