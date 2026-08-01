# -*- coding: utf-8 -*-
"""
salon-poster-pil / remix_poster.py
===================================
读书沙龙/活动手机海报「真实平台模板 + PIL 二次修改」参数化主脚本。

复用方式：只改下方 CONFIG 区（输入图、文案、素材路径、版面参数），无需改动函数体。
典型流程：去水印(inpaint+空间约束) -> 信息卡整片重绘 -> 图标/Logo/二维码合成 -> 自检。

路径可移植：所有路径走环境变量覆盖（SALON_INPUT / SALON_OUTPUT / SALON_LOGO /
SALON_QR / SALON_FONT），默认值相对仓库根目录下的 assets/，clone 后放入自己的素材即可。

红线（务必遵守，详见 skill references/）：
- 去水印只用 cv2.inpaint + 空间约束（只处理右上角近白连通块），禁止全局颜色检测、禁止贴图覆盖。
- 信息卡必须整片铲掉重画，禁止在旧图上叠加补丁。
- 图标用几何线绘（draw_clock/pin/yen），禁止字体字符。
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import cv2

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent                      # salon-poster/
ASSETS = REPO_ROOT / 'assets'

def _env_or(name: str, default: str) -> str:
    return os.environ.get(name) or default

# ======================================================================
# CONFIG —— 所有可变项集中在此，改这里即可复用，不必动下面的函数
# 路径默认读取仓库 assets/ 下文件，可用环境变量覆盖（见 README）。
# ======================================================================
FONT_PATH   = _env_or('SALON_FONT', r'C:/Windows/Fonts/msyh.ttc')

INPUT_PNG   = _env_or('SALON_INPUT', str(ASSETS / 'input.png'))        # 真实平台下载的海报（可含水印）
OUTPUT_PNG  = _env_or('SALON_OUTPUT', str(ASSETS / 'output.png'))      # 产出

# --- 去水印（仅当底图带平台水印时开启）---
REMOVE_WATERMARK = True
# 空间约束：只处理右上角小范围（Canva 水印常见位置）。坐标按 848x1200 基准。
WATERMARK_REGION = {'x0': 620, 'y0': 30, 'x1': 808, 'y1': 90}

# --- 画布与底部蓝带 ---
W, H        = 848, 1200
BLUE_Y      = 1035
BLUE        = (139, 211, 221)

# --- 信息卡几何（米白圆角卡）---
CARD_X, CARD_Y, CARD_W, CARD_H = 40, 985, 768, 185
CARD_RADIUS = 20
CARD_BG     = (248, 244, 236)
CARD_PADDING= 32
QR_SIZE     = 130          # 卡片右侧二维码边长

# --- 图标 ---
ICON_SIZE   = 24
ICON_COLOR  = (139, 105, 20)   # 金棕

# --- 三行信息：text / 字号 / 颜色 / 图标('clock'|'pin'|'yen'|None) ---
# 这是 848x1200 基准下的示例文案，使用时替换为你的活动信息。
INFO_LINES = [
    {'text': '8月2日  10:00-12:00',               'size': 30, 'color': (26, 26, 26),  'icon': 'clock'},
    {'text': '南岸区下浩老街•浩阅书店2楼',         'size': 26, 'color': (51, 51, 51),  'icon': 'pin'},
    {'text': '会员20 / 非会员50 / 亲子套餐65（限额12人）', 'size': 22, 'color': (139, 105, 20), 'icon': 'yen'},
]

# --- Logo（转黑透明，合成右上角）---
LOGO_PATH   = _env_or('SALON_LOGO', str(ASSETS / 'logo.png'))
LOGO_SIZE   = 150
LOGO_POS    = 'top-right'   # 合成到右上角干净区

# --- 二维码（等比缩放 + 圆角米白底衬，合成到卡片右侧）---
QR_PATH     = _env_or('SALON_QR', str(ASSETS / 'qrcode.png'))

# ======================================================================
# 函数
# ======================================================================
def remove_watermark_inpaint(img: Image.Image, region: dict) -> Image.Image:
    """用 cv2.inpaint(TELEA) 从底层补全水印像素。
    关键：先按 region 裁出右上角小范围，再在范围内取近白像素做遮罩——
    绝不做全局颜色检测，避免误伤书页/白色背景（v14 事故）。"""
    arr = np.array(img.convert('RGB'))
    x0, y0, x1, y1 = region['x0'], region['y0'], region['x1'], region['y1']
    mask = np.zeros((arr.shape[0], arr.shape[1]), dtype=np.uint8)  # 必须与整图同尺寸
    sub = arr[y0:y1, x0:x1]
    r = sub[:, :, 0].astype(int); g = sub[:, :, 1].astype(int); b = sub[:, :, 2].astype(int)
    submask = ((r >= 245) & (g >= 245) & (b >= 245)).astype(np.uint8) * 255
    if submask.sum() == 0:
        return img  # 无水印残留，直接返回
    kernel = np.ones((3, 3), np.uint8)
    submask = cv2.dilate(submask, kernel, iterations=2)
    mask[y0:y1, x0:x1] = submask  # 只在该区域内填水印像素
    inpainted = cv2.inpaint(arr, mask, 3, cv2.INPAINT_TELEA)
    return Image.fromarray(inpainted)


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


def draw_info_card(base: Image.Image):
    """铲掉底部整片蓝带重画 + 米白圆角信息卡 + 三行左对齐 + 几何图标 + 右侧二维码位。"""
    draw = ImageDraw.Draw(base)
    draw.rectangle([0, BLUE_Y, W, H], fill=BLUE)

    # 阴影
    shadow = Image.new('RGBA', (CARD_W + 8, CARD_H + 8), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([4, 4, CARD_W + 4, CARD_H + 4], radius=CARD_RADIUS, fill=(0, 0, 0, 25))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=4))
    base.paste(shadow, (CARD_X - 4, CARD_Y - 4), shadow)

    # 卡片
    mask = Image.new('L', (CARD_W, CARD_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, CARD_W, CARD_H], radius=CARD_RADIUS, fill=255)
    card = Image.new('RGB', (CARD_W, CARD_H), CARD_BG)
    base.paste(card, (CARD_X, CARD_Y), mask)

    draw = ImageDraw.Draw(base)

    fonts = [ImageFont.truetype(FONT_PATH, ln['size']) for ln in INFO_LINES]
    bboxes = [draw.textbbox((0, 0), ln['text'], font=f) for ln, f in zip(INFO_LINES, fonts)]
    line_h = [b[3] - b[1] for b in bboxes]
    line_w = [b[2] - b[0] for b in bboxes]

    gaps = [36, 32]  # 行间距（逐级略减）
    total_h = sum(line_h) + sum(gaps)
    start_y = CARD_Y + (CARD_H - total_h) // 2

    icon_x = CARD_X + CARD_PADDING + ICON_SIZE // 2
    text_x = icon_x + ICON_SIZE // 2 + 14

    y = start_y
    for i, (ln, f, w, h) in enumerate(zip(INFO_LINES, fonts, line_w, line_h)):
        icon_cy = y + h // 2
        if ln['icon'] in ICON_FNS:
            ICON_FNS[ln['icon']](draw, icon_x, icon_cy, ICON_COLOR)
        draw.text((text_x, y), ln['text'], fill=ln['color'], font=f)
        y += h + (gaps[i] if i < len(gaps) else 0)

    return base, text_x, line_w


def composite_logo(base: Image.Image) -> Image.Image:
    """Logo 转黑透明后合成到右上角干净区。"""
    logo = Image.open(LOGO_PATH).convert('RGBA')
    logo.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    # 转黑：保留 alpha，RGB 置黑
    arr = np.array(logo)
    arr[:, :, 0:3] = 0
    logo = Image.fromarray(arr, 'RGBA')
    if LOGO_POS == 'top-right':
        x = W - logo.width - 24
        y = 24
    else:
        x, y = 24, 24
    base.paste(logo, (x, y), logo)
    return base


def composite_qrcode(base: Image.Image, text_x: int, line_w: list):
    """二维码等比缩放到 QR_SIZE + 圆角米白底衬，合成到卡片右侧。"""
    qr = Image.open(QR_PATH).convert('RGBA')
    qr.thumbnail((QR_SIZE, QR_SIZE), Image.Resampling.LANCZOS)
    if qr.width < QR_SIZE or qr.height < QR_SIZE:
        ratio = max(QR_SIZE / qr.width, QR_SIZE / qr.height)
        qr = qr.resize((int(qr.width * ratio), int(qr.height * ratio)), Image.Resampling.LANCZOS)
    left = (qr.width - QR_SIZE) // 2; top = (qr.height - QR_SIZE) // 2
    qr = qr.crop((left, top, left + QR_SIZE, top + QR_SIZE))

    qr_x = CARD_X + CARD_W - CARD_PADDING - QR_SIZE
    qr_y = CARD_Y + (CARD_H - QR_SIZE) // 2

    qr_bg_mask = Image.new('L', (QR_SIZE, QR_SIZE), 0)
    ImageDraw.Draw(qr_bg_mask).rounded_rectangle([0, 0, QR_SIZE, QR_SIZE], radius=12, fill=255)
    qr_bg = Image.new('RGB', (QR_SIZE, QR_SIZE), (252, 250, 246))
    base.paste(qr_bg, (qr_x, qr_y), qr_bg_mask)
    base.paste(qr, (qr_x, qr_y), qr)
    return base, qr_x


def selfcheck(base: Image.Image, text_x: int, line_w: list, qr_x: int) -> dict:
    """程序化自检：水印近白残留、文字与二维码是否重叠。"""
    report = {}
    arr = np.array(base.convert('RGB'))
    # 水印区近白残留（仅检查右上角 region）
    if REMOVE_WATERMARK:
        rg = arr[WATERMARK_REGION['y0']:WATERMARK_REGION['y1'], WATERMARK_REGION['x0']:WATERMARK_REGION['x1']]
        rr = rg[:, :, 0].astype(int); gg = rg[:, :, 1].astype(int); bb = rg[:, :, 2].astype(int)
        residual = int(((rr >= 245) & (gg >= 245) & (bb >= 245)).sum())
        report['watermark_residual'] = residual
    # 文字右缘 vs 二维码左缘
    loc_right = text_x + max(line_w)
    report['text_right_edge'] = loc_right
    report['qr_left_edge'] = qr_x
    report['overlap'] = loc_right >= qr_x
    return report


# ======================================================================
# 主流程
# ======================================================================
def main():
    if not os.path.exists(INPUT_PNG):
        raise FileNotFoundError(
            f'未找到底图：{INPUT_PNG}\n'
            f'请把真实平台海报放到 assets/input.png，或用环境变量 SALON_INPUT 指定路径。'
        )
    base = Image.open(INPUT_PNG).convert('RGB')

    if REMOVE_WATERMARK:
        base = remove_watermark_inpaint(base, WATERMARK_REGION)

    base, text_x, line_w = draw_info_card(base)
    base = composite_logo(base)
    base, qr_x = composite_qrcode(base, text_x, line_w)

    report = selfcheck(base, text_x, line_w, qr_x)
    print('[selfcheck]', report)
    assert report.get('watermark_residual', 0) == 0, '水印近白残留未清零！'
    assert not report['overlap'], '信息卡文字与二维码重叠！'

    os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)
    base.save(OUTPUT_PNG, quality=95)
    print('saved ->', OUTPUT_PNG)


if __name__ == '__main__':
    main()
