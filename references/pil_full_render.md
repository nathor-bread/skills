# 路线 B · 从零 PIL 全内容渲染（详解 + 代码）

> 配套脚本：`scripts/render_full.py`（已实测：light/dark 双模式均通过 selfcheck）。
> 适用：真实模板平台不可达，或需要像素级精确文字、完全可编辑的成品。

## 一、整体思路

```
底板图(Pexels/ImageGen, resize→848×1200)
   └─ add_scrim()            浅/深衬底提升对比
   └─ draw_series_badge()    左上角阶段标签（无底色）
   └─ draw_title_block()     主标题(粗雅黑) + 装饰线 + 副标题
   └─ draw_quote()           金句（艺术字：渐变+描边+投影，逗号拆两行居中）
   └─ draw_values()          书形元素下方「品」字标签
   └─ draw_info_card()       底部信息卡（时间/地点/费用 + 几何图标）
   └─ composite_logo/qrcode() Logo 转黑透明 + 二维码圆角衬底
   └─ selfcheck()            文字不压二维码 + 全文字≥28px
```

## 二、双模式自动检测（保证可读性）

按底板整体亮度选配色，避免"深底用深字看不清"：

```python
def detect_mode(base):
    arr = np.array(base.convert('RGB')).reshape(-1, 3).astype(float)
    lum = (arr[:,0]*0.299 + arr[:,1]*0.587 + arr[:,2]*0.114).mean()
    return 'dark' if lum < 128 else 'light'

PALETTE = {
    'light': {'title':(40,55,62), 'sub':(70,110,120), 'accent':(180,130,50),
              'quote':(45,60,70), 'value':(40,55,62), 'stroke':(33,60,70),
              'badge':(70,130,140), 'card_bg':(245,252,255), 'band':(100,150,160),
              'icon':(70,110,120), 'scrim':(255,255,255)},
    'dark':  {'title':(245,250,255), 'sub':(200,220,230), 'accent':(255,210,140),
              'quote':(240,245,250), 'value':(235,242,248), 'stroke':(250,240,220),
              'badge':(150,200,210), 'card_bg':(28,38,44), 'band':(20,30,36),
              'icon':(180,210,220), 'scrim':(0,0,0)},
}
```

## 三、艺术字：渐变填充 + 描边 + 投影阴影

金句/主视觉用此法，制造海报级层次。核心 `_art_text_layer` 分步合成：

```python
def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i]-a[i])*t)) for i in range(3))

def _make_gradient(w, h, stops):
    # stops: [(pos 0..1, (r,g,b)), ...] 纵向线性渐变
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    ts = [s[0] for s in stops]; cols = [s[1] for s in stops]
    for y in range(h):
        t = y/(h-1) if h>1 else 0
        if t <= ts[0]: c = cols[0]
        elif t >= ts[-1]: c = cols[-1]
        else:
            for i in range(len(ts)-1):
                if ts[i] <= t <= ts[i+1]:
                    c = _lerp(cols[i], cols[i+1], (t-ts[i])/(ts[i+1]-ts[i])); break
        arr[y,:,:] = c
    return Image.fromarray(arr, 'RGB')

def _art_text_layer(text, font, grad_stops, stroke_color, stroke_w,
                    shadow_color, soff, sblur):
    tmp = Image.new('RGBA', (1,1))
    bbox = ImageDraw.Draw(tmp).textbbox((0,0), text, font=font)
    pad = stroke_w + max(soff) + sblur + 12
    w = int(bbox[2]-bbox[0] + pad*2); h = int(bbox[3]-bbox[1] + pad*2)
    lx = -bbox[0]+pad; ly = -bbox[1]+pad
    # 1) 投影阴影（单独模糊，不污染文字）
    sh = Image.new('RGBA', (w,h), (0,0,0,0))
    ImageDraw.Draw(sh).text((lx+soff[0], ly+soff[1]), text, font=font, fill=shadow_color)
    sh = sh.filter(ImageFilter.GaussianBlur(sblur))
    # 2) 主层：描边轮廓垫底
    main = Image.new('RGBA', (w,h), (0,0,0,0))
    ImageDraw.Draw(main).text((lx,ly), text, font=font, fill=stroke_color,
                               stroke_width=stroke_w, stroke_fill=stroke_color)
    # 3) 渐变填充（以字形为遮罩合成到主层）
    grad = _make_gradient(w, h, grad_stops)
    mask = Image.new('L', (w,h), 0)
    ImageDraw.Draw(mask).text((lx,ly), text, font=font, fill=255)
    grad.putalpha(mask)
    main = Image.alpha_composite(main, grad)
    return Image.alpha_composite(sh, main), pad, (bbox[2]-bbox[0])
```

典型参数（金色渐变 + 深蓝绿描边 + 半透明投影）：

```python
ART_GRADIENT = [(0.0,(255,228,162)), (0.5,(243,193,100)), (1.0,(192,132,48))]
STROKE_W = 4
SHADOW_COLOR = (16,36,46,150)
SHADOW_OFF = (3,6)
SHADOW_BLUR = 4
```

## 四、字体差异化层级

| 层级 | 字体 | 作用 |
|------|------|------|
| 主标题 | 微软雅黑 粗 (msyhbd) 64px | 最强视觉锚点 |
| 副标题 | 微软雅黑 (msyh) 33px | 支撑级，明显更小更淡 |
| 金句 | 楷体 (simkai) 40px 艺术字 | 与主副标题明显区分，制造记忆点 |

> Windows 仅 `simkai.ttf`（楷体）为明显的毛笔衬线字体；若缺则回退雅黑。Linux/macOS 换对应楷体/行楷字体路径。

## 五、Ardot 28px 硬底线（selfcheck 断言）

```python
core = [TITLE_FONT.size, SUBTITLE_FONT.size, QUOTE_FONT.size, TAG_FONT.size,
        INFO_FONTS['clock'].size, INFO_FONTS['pin'].size, INFO_FONTS['yen'].size]
small = [s for s in core if s < 28]
assert not small, f'存在 <28px 字号（违反 Ardot 底线）: {small}'
# 装饰性系列徽标（用户指定缩小）为已知例外，仅告警不中止
```

## 六、防重叠 selfcheck

```python
def selfcheck(base, text_x, line_w, qr_x):
    loc_right = text_x + max(line_w)
    return {'text_right_edge': loc_right, 'qr_left_edge': qr_x, 'overlap': loc_right >= qr_x}
# assert not report['overlap']
```

## 七、使用

```bash
# 改 scripts/render_full.py 顶部 CONFIG（文案 / 路径 / MODE / ART_QUOTE）
# 或用环境变量覆盖：
SALON_BASE=/path/base.png SALON_OUTPUT=/path/out.png \
SALON_MODE=auto SALON_TITLE="重塑 AI 时代创作观" \
python scripts/render_full.py
```

依赖：`pip install pillow numpy`（路线 A 的 `remix_poster.py` 额外需 `opencv-python-headless`）。
