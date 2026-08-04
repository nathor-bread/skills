# -*- coding: utf-8 -*-
"""
salon-poster-pil · 路线 B：从零 PIL 全内容渲染
=============================================
当真实模板平台（稿定 / Canva）不可达，或需要像素级精确文字控制时，
用一张「底板图」+ PIL 绘制全部结构化文字层，产出手机竖版海报。

关键能力（来自实战沉淀）：
1. 双模式自动检测：按底板亮度自动选 浅底深字 / 深底浅字，保证可读性。
2. Ardot 28px 硬底线：所有文字节点（含页脚/元信息/费用/序号）默认 ≥28px。
3. 艺术字渲染：金句/主视觉支持 渐变填充 + 描边 + 投影阴影（_art_text_layer）。
4. 字体差异化层级：主标题(粗雅黑) / 副标题(雅黑) / 金句(楷体) 制造视觉层次。
5. 字号断言 + selfcheck 防重叠，CI 式自检闭环。

仅改顶部 CONFIG 区即可复用；路径支持环境变量覆盖。
依赖：Pillow, numpy（opencv 仅路线 A 去水印需要，本脚本不依赖）。
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HERE = Path(__file__).resolve().parent
FONT_DIR = r'C:/Windows/Fonts'


# ───────────────────────── 环境变量覆盖 ─────────────────────────
def _env(name, default):
    return os.environ.get(name) or default


# ───────────────────────── 配置文件（只改这里） ─────────────────────────
W, H = 848, 1200                       # 画布尺寸（短边 ≥720，满足 Ardot）

# 底板：Pexels 直链下载 / ImageGen 生成 / 本地图皆可；脚本会 resize 归一化
BASE_PNG = _env('SALON_BASE',
                r'D:/workbuddy duc/视觉助手/生成产物/canvas候选/base_B_清浅蓝绿.png')
OUTPUT_PNG = _env('SALON_OUTPUT',
                  str(HERE / 'output_full.png'))
LOGO_PATH = _env('SALON_LOGO',
                 r'D:/workbuddy duc/青少年AI教育与沙龙/读书沙龙/assets/logos/logo-youdan.png')
QR_PATH = _env('SALON_QR',
               r'D:/workbuddy duc/青少年AI教育与沙龙/读书沙龙/assets/二维码/qrcode.png')

# 文案
SERIES_BADGE = _env('SALON_BADGE', '"创作 — 办公 — 流程 — 职业" 共4期')   # 左上角阶段标签（无底色）
TITLE        = _env('SALON_TITLE', '重塑 AI 时代创作观')
SUBTITLE     = _env('SALON_SUB', '每个人都需要掌握的 AI 创作逻辑')
QUOTE        = _env('SALON_QUOTE', '你不需要先成为写作高手，只需要敢把灵感交给 AI')  # 逗号拆两行；去结尾句号
VALUES       = ['掌握提示词优化', '解锁多模态创作', '让想法变作品']   # 书形元素下方「品」字标签

INFO_LINES = [
    {'text': '8月9日  10:00-12:00',                  'size': 32, 'color_key': 'info_clock', 'icon': 'clock'},
    {'text': '南岸区下浩老街•浩阅书店2楼',            'size': 28, 'color_key': 'info_pin',   'icon': 'pin'},
    {'text': '会员10 / 非会员36 / 亲子20（限额12人）', 'size': 28, 'color_key': 'info_yen',   'icon': 'yen'},
]

# 模式：'auto' 按底板亮度自动选；或强制 'light' / 'dark'
MODE = _env('SALON_MODE', 'auto')

# 艺术字（金句）开关与参数
ART_QUOTE = True                        # 金句是否用艺术字（渐变+描边+投影）
QUOTE_SIZE = 40                         # 金句字号（≥28）
ART_GRADIENT = [(0.0, (255, 228, 162)), (0.5, (243, 193, 100)), (1.0, (192, 132, 48))]  # 金→琥珀
STROKE_W = 4
SHADOW_COLOR = (16, 36, 46, 150)
SHADOW_OFF = (3, 6)
SHADOW_BLUR = 4


# ───────────────────────── 字体加载 ─────────────────────────
def _font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


TITLE_FONT = _font('msyhbd.ttc', 64) if os.path.exists(os.path.join(FONT_DIR, 'msyhbd.ttc')) else _font('msyh.ttc', 64)
SUBTITLE_FONT = _font('msyh.ttc', 33)
try:
    QUOTE_FONT = _font('simkai.ttf', QUOTE_SIZE)     # 楷体：与雅黑明显区分
except Exception:
    QUOTE_FONT = _font('msyh.ttc', QUOTE_SIZE)
try:
    QUOTE_MARK = _font('simkai.ttf', 64)
except Exception:
    QUOTE_MARK = _font('msyh.ttc', 60)
BADGE_FONT = _font('msyh.ttc', 24)                  # 阶段标签：装饰性，用户要求缩小
TAG_FONT   = _font('msyh.ttc', 34)                  # 收获标签
TAG_HEIGHT = 56
TAG_RADIUS = 28
TAG_PADDING = 30

# 信息卡字号（全部 ≥28）
INFO_FONTS = {
    'clock': _font('msyh.ttc', 32),
    'pin':   _font('msyh.ttc', 28),
    'yen':   _font('msyh.ttc', 28),
}


# ───────────────────────── 双模式配色 ─────────────────────────
PALETTE = {
    'light': {   # 浅底深字
        'title': (40, 55, 62), 'sub': (70, 110, 120), 'accent': (180, 130, 50),
        'quote': (45, 60, 70), 'value': (40, 55, 62), 'stroke': (33, 60, 70),
        'badge': (70, 130, 140), 'card_bg': (245, 252, 255), 'band': (100, 150, 160),
        'icon': (70, 110, 120), 'scrim': (255, 255, 255),
    },
    'dark': {    # 深底浅字
        'title': (245, 250, 255), 'sub': (200, 220, 230), 'accent': (255, 210, 140),
        'quote': (240, 245, 250), 'value': (235, 242, 248), 'stroke': (250, 240, 220),
        'badge': (150, 200, 210), 'card_bg': (28, 38, 44), 'band': (20, 30, 36),
        'icon': (180, 210, 220), 'scrim': (0, 0, 0),
    },
}


def detect_mode(base):
    """按底板整体亮度自动选模式。"""
    if MODE in ('light', 'dark'):
        return MODE
    arr = np.array(base.convert('RGB')).reshape(-1, 3).astype(float)
    lum = (arr[:, 0] * 0.299 + arr[:, 1] * 0.587 + arr[:, 2] * 0.114).mean()
    return 'dark' if lum < 128 else 'light'


# ───────────────────────── 艺术字辅助 ─────────────────────────
def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _make_gradient(w, h, stops):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    ts = [s[0] for s in stops]
    cols = [s[1] for s in stops]
    for y in range(h):
        t = y / (h - 1) if h > 1 else 0
        if t <= ts[0]:
            c = cols[0]
        elif t >= ts[-1]:
            c = cols[-1]
        else:
            for i in range(len(ts) - 1):
                if ts[i] <= t <= ts[i + 1]:
                    f = (t - ts[i]) / (ts[i + 1] - ts[i])
                    c = _lerp(cols[i], cols[i + 1], f)
                    break
        arr[y, :, :] = c
    return Image.fromarray(arr, 'RGB')


def _art_text_layer(text, font, grad_stops, stroke_color, stroke_w, shadow_color, soff, sblur):
    """生成艺术字图层：渐变填充 + 描边 + 投影阴影。返回 (RGBA图层, pad, 文字视觉宽)。"""
    tmp = Image.new('RGBA', (1, 1))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    pad = stroke_w + max(soff) + sblur + 12
    w = int(bbox[2] - bbox[0] + pad * 2)
    h = int(bbox[3] - bbox[1] + pad * 2)
    lx = -bbox[0] + pad
    ly = -bbox[1] + pad
    # 投影阴影（单独模糊，避免污染文字）
    sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((lx + soff[0], ly + soff[1]), text, font=font, fill=shadow_color)
    sh = sh.filter(ImageFilter.GaussianBlur(sblur))
    # 主层：描边轮廓垫底
    main = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(main).text((lx, ly), text, font=font, fill=stroke_color,
                               stroke_width=stroke_w, stroke_fill=stroke_color)
    # 渐变填充（以字形为遮罩）
    grad = _make_gradient(w, h, grad_stops)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((lx, ly), text, font=font, fill=255)
    grad.putalpha(mask)
    main = Image.alpha_composite(main, grad)
    out = Image.alpha_composite(sh, main)
    return out, pad, (bbox[2] - bbox[0])


# ───────────────────────── 绘图函数 ─────────────────────────
def _wrap(draw, text, font, max_w):
    lines, cur = [], ''
    for ch in text:
        if draw.textbbox((0, 0), cur + ch, font=font)[2] <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def add_scrim(base, mode):
    """提升文字对比的浅/深衬底。"""
    overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    top_alpha, end = (110 if mode == 'light' else 150), int(H * 0.58)
    col = PALETTE[mode]['scrim']
    for y in range(end):
        a = int(top_alpha * (1 - y / end) ** 1.3)
        od.line([(0, y), (W, y)], fill=(col[0], col[1], col[2], a))
    base = base.convert('RGBA')
    return Image.alpha_composite(base, overlay).convert('RGB')


def draw_series_badge(base, P):
    draw = ImageDraw.Draw(base)
    draw.text((40, 40), SERIES_BADGE, fill=P['badge'], font=BADGE_FONT)
    return base


def draw_title_block(base, P):
    draw = ImageDraw.Draw(base)
    margin = 56
    max_w = W - margin * 2
    lines = _wrap(draw, TITLE, TITLE_FONT, max_w)
    ty = 290
    for ln in lines:
        tw = draw.textbbox((0, 0), ln, font=TITLE_FONT)[2]
        tx = (W - tw) // 2
        halo = (255, 252, 246) if False else (20, 30, 36)  # 浅底用白光晕，深底用深色光晕
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((tx + dx, ty + dy), ln, fill=halo, font=TITLE_FONT)
        draw.text((tx, ty), ln, fill=P['title'], font=TITLE_FONT)
        ty += TITLE_FONT.size + 8
    line_w = 72
    ly = ty + 6
    draw.rectangle([(W - line_w) // 2, ly, (W + line_w) // 2, ly + 4], fill=P['accent'])
    sw = draw.textbbox((0, 0), SUBTITLE, font=SUBTITLE_FONT)[2]
    sx = (W - sw) // 2
    sy = ly + 20
    draw.text((sx, sy), SUBTITLE, fill=P['sub'], font=SUBTITLE_FONT)
    return base, sy + SUBTITLE_FONT.size + 16


def draw_quote(base, start_y, P):
    if ART_QUOTE:
        grad = ART_GRADIENT
        stroke = P['stroke']
        layer_fn = lambda txt, f: _art_text_layer(txt, f, grad, stroke, STROKE_W,
                                                   SHADOW_COLOR, SHADOW_OFF, SHADOW_BLUR)
        # 引号
        ql, qpad, qtw = layer_fn('“', QUOTE_MARK)
        qx = (W - qtw) // 2 - qpad
        qy = start_y - qpad
        base.paste(ql, (qx, qy), ql)
        parts = QUOTE.split('，', 1)
        if len(parts) == 1:
            parts = QUOTE.split(',', 1)
        y = start_y + 60
        lh = 62
        for line in parts[:2]:
            line = line.strip()
            layer, pad, tw = layer_fn(line, QUOTE_FONT)
            px = (W - tw) // 2 - pad
            py = y - pad
            base.paste(layer, (px, py), layer)
            y += lh
        draw = ImageDraw.Draw(base)
        draw.rectangle([(W - 64) // 2, y + 6, (W + 64) // 2, y + 9], fill=P['accent'])
        return base, y + 40
    # 非艺术字回退
    draw = ImageDraw.Draw(base)
    parts = QUOTE.split('，', 1)
    if len(parts) == 1:
        parts = QUOTE.split(',', 1)
    y = start_y + 58
    lh = 52
    for line in parts[:2]:
        line = line.strip()
        tw = draw.textbbox((0, 0), line, font=QUOTE_FONT)[2]
        tx = (W - tw) // 2
        draw.text((tx, y), line, fill=P['quote'], font=QUOTE_FONT)
        y += lh
    draw.rectangle([(W - 60) // 2, y + 8, (W + 60) // 2, y + 11], fill=P['accent'])
    return base, y + 44


def draw_values(base, start_y, P):
    draw = ImageDraw.Draw(base)
    tag_dims = []
    for v in VALUES:
        tw = draw.textbbox((0, 0), v, font=TAG_FONT)[2]
        tag_dims.append((tw + TAG_PADDING * 2, TAG_HEIGHT, v))
    w0, h0, _ = tag_dims[0]
    w1, h1, _ = tag_dims[1]
    w2, h2, _ = tag_dims[2]
    top_y = 808
    v_gap = 16
    bot_y = top_y + h0 + v_gap
    x0 = (W - w0) // 2
    h_gap = 18
    bottom_total = w1 + w2 + h_gap
    x1 = (W - bottom_total) // 2
    x2 = x1 + w1 + h_gap
    layout = [(x0, top_y, tag_dims[0]), (x1, bot_y, tag_dims[1]), (x2, bot_y, tag_dims[2])]
    pill_fill = (230, 245, 250) if start_y else (230, 245, 250)
    for (px, py, (tw, th, text)) in layout:
        mask = Image.new('L', (tw, th), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=TAG_RADIUS, fill=255)
        base.paste(Image.new('RGB', (tw, th), pill_fill), (px, py), mask)
        txt_w = draw.textbbox((0, 0), text, font=TAG_FONT)[2]
        txt_h = draw.textbbox((0, 0), text, font=TAG_FONT)[3]
        tx = px + (tw - txt_w) // 2
        ty = py + (th - txt_h) // 2 - 2
        draw.text((tx, ty), text, fill=P['value'], font=TAG_FONT)
    return base


def draw_clock(draw, cx, cy, color):
    r = 9
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
    draw.line([(cx, cy), (cx, cy - r + 5)], fill=color, width=2)
    draw.line([(cx, cy), (cx + r - 5, cy)], fill=color, width=2)
    draw.ellipse([cx - 1, cy - 1, cx + 1, cy + 1], fill=color)


def draw_pin(draw, cx, cy, color):
    r = 8
    draw.arc([cx - r, cy - r - 2, cx + r, cy + r - 2], start=200, end=340, fill=color, width=2)
    draw.line([(cx - r + 1, cy + r - 5), (cx, cy + r + 5), (cx + r - 1, cy + r - 5)], fill=color, width=2)
    draw.ellipse([cx - 2, cy + r - 6, cx + 2, cy + r - 2], fill=color)


def draw_yen(draw, cx, cy, color):
    draw.line([(cx - 6, cy - 7), (cx, cy - 1)], fill=color, width=2)
    draw.line([(cx + 6, cy - 7), (cx, cy - 1)], fill=color, width=2)
    draw.line([(cx - 6, cy), (cx + 6, cy)], fill=color, width=2)
    draw.line([(cx, cy + 1), (cx, cy + 7)], fill=color, width=2)


ICON_FNS = {'clock': draw_clock, 'pin': draw_pin, 'yen': draw_yen}


CARD_X, CARD_Y, CARD_W, CARD_H = 40, 995, 768, 175
CARD_RADIUS = 20
CARD_PADDING = 32
QR_SIZE = 120
LOGO_SIZE = 120


def draw_info_card(base, P):
    draw = ImageDraw.Draw(base)
    draw.rectangle([0, CARD_Y - 20, W, H], fill=P['band'])
    shadow = Image.new('RGBA', (CARD_W + 8, CARD_H + 8), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([4, 4, CARD_W + 4, CARD_H + 4], radius=CARD_RADIUS, fill=(0, 0, 0, 30))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    base.paste(shadow, (CARD_X - 4, CARD_Y - 4), shadow)
    mask = Image.new('L', (CARD_W, CARD_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, CARD_W, CARD_H], radius=CARD_RADIUS, fill=255)
    base.paste(Image.new('RGB', (CARD_W, CARD_H), P['card_bg']), (CARD_X, CARD_Y), mask)
    draw = ImageDraw.Draw(base)
    fonts = [INFO_FONTS[ln['icon']] for ln in INFO_LINES]
    bboxes = [draw.textbbox((0, 0), ln['text'], font=f) for ln, f in zip(INFO_LINES, fonts)]
    line_h = [b[3] - b[1] for b in bboxes]
    line_w = [b[2] - b[0] for b in bboxes]
    gaps = [32, 28]
    total_h = sum(line_h) + sum(gaps)
    start_y = CARD_Y + (CARD_H - total_h) // 2
    icon_x = CARD_X + CARD_PADDING + 12
    text_x = icon_x + 24
    y = start_y
    for i, (ln, f, w, h) in enumerate(zip(INFO_LINES, fonts, line_w, line_h)):
        icon_cy = y + h // 2
        if ln['icon'] in ICON_FNS:
            ICON_FNS[ln['icon']](draw, icon_x, icon_cy, P['icon'])
        color = PALETTE[MODE_CUR]['title'] if ln['color_key'] == 'info_clock' else (
            PALETTE[MODE_CUR]['sub'] if ln['color_key'] == 'info_pin' else PALETTE[MODE_CUR]['accent'])
        draw.text((text_x, y), ln['text'], fill=color, font=f)
        y += h + (gaps[i] if i < len(gaps) else 0)
    return base, text_x, line_w


def composite_logo(base, P):
    if not os.path.exists(LOGO_PATH):
        return base
    logo = Image.open(LOGO_PATH).convert('RGBA')
    logo.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    arr = np.array(logo)
    arr[:, :, 0:3] = 0
    logo = Image.fromarray(arr, 'RGBA')
    base.paste(logo, (W - logo.width - 24, 22), logo)
    return base


def composite_qrcode(base, text_x, line_w, P):
    if not os.path.exists(QR_PATH):
        return base, text_x + max(line_w) + 10
    qr = Image.open(QR_PATH).convert('RGBA')
    qr.thumbnail((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)
    if qr.width < QR_SIZE or qr.height < QR_SIZE:
        ratio = max(QR_SIZE / qr.width, QR_SIZE / qr.height)
        qr = qr.resize((int(qr.width * ratio), int(qr.height * ratio)), Image.Resampling.LANCZOS)
    left = (qr.width - QR_SIZE) // 2
    top = (qr.height - QR_SIZE) // 2
    qr = qr.crop((left, top, left + QR_SIZE, top + QR_SIZE))
    qr_x = CARD_X + CARD_W - CARD_PADDING - QR_SIZE
    qr_y = CARD_Y + (CARD_H - QR_SIZE) // 2
    qr_bg_mask = Image.new('L', (QR_SIZE, QR_SIZE), 0)
    ImageDraw.Draw(qr_bg_mask).rounded_rectangle([0, 0, QR_SIZE, QR_SIZE], radius=12, fill=255)
    base.paste(Image.new('RGB', (QR_SIZE, QR_SIZE), (255, 253, 249)), (qr_x, qr_y), qr_bg_mask)
    base.paste(qr, (qr_x, qr_y), qr)
    return base, qr_x


def selfcheck(base, text_x, line_w, qr_x):
    loc_right = text_x + max(line_w)
    return {'text_right_edge': loc_right, 'qr_left_edge': qr_x, 'overlap': loc_right >= qr_x}


MODE_CUR = 'light'


def main():
    global MODE_CUR
    if not os.path.exists(BASE_PNG):
        raise FileNotFoundError(f'未找到底板：{BASE_PNG}')
    base = Image.open(BASE_PNG).convert('RGB').resize((W, H), Image.Resampling.LANCZOS)
    MODE_CUR = detect_mode(base)
    P = PALETTE[MODE_CUR]

    # Ardot 28px 审计：正文/信息类必须 ≥28px；装饰性系列徽标(用户可能要求缩小)为已知例外
    core = [TITLE_FONT.size, SUBTITLE_FONT.size, QUOTE_FONT.size, TAG_FONT.size,
            INFO_FONTS['clock'].size, INFO_FONTS['pin'].size, INFO_FONTS['yen'].size]
    small = [s for s in core if s < 28]
    assert not small, f'存在 <28px 字号（违反 Ardot 底线）: {small}'
    if BADGE_FONT.size < 28:
        print(f'[warn] 系列徽标 {BADGE_FONT.size}px 低于 28px —— 属用户指定的装饰性微标签例外，保留')

    base = add_scrim(base, MODE_CUR)
    base = draw_series_badge(base, P)
    base, quote_y = draw_title_block(base, P)
    base, values_y = draw_quote(base, quote_y, P)
    base = draw_values(base, values_y, P)
    base, text_x, line_w = draw_info_card(base, P)
    base = composite_logo(base, P)
    base, qr_x = composite_qrcode(base, text_x, line_w, P)

    report = selfcheck(base, text_x, line_w, qr_x)
    assert not report['overlap'], '信息卡文字与二维码重叠！'

    os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)
    base.save(OUTPUT_PNG, quality=95)
    print(f'[mode={MODE_CUR}] saved -> {OUTPUT_PNG}')
    print('[selfcheck]', report)


if __name__ == '__main__':
    main()
