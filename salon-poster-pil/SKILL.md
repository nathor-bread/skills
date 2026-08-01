---
name: salon-poster-pil
agent_created: true
description: Turn a real-platform salon/event poster PNG (Gaoding / Canva export) into a finished phone-vertical poster with PIL — watermark removal (inpaint), info-card redraw, geometric icons, logo + QR composite, and a pixel-level self-check. Use when the user wants a reading-club / offline-salon / event poster based on real template aesthetics rather than pure HTML/code generation. Trigger phrases: "读书会海报", "沙龙海报", "活动海报", "稿定/Canva 海报二次修改", "poster remix".
---

# 读书沙龙海报 · 真实模板 + PIL 二次修改

把真实平台（稿定 / Canva）下载的沙龙海报，用 PIL 二次修改成带准确活动信息的成品。覆盖从参考收集到成品自检的全流程。跨平台可复用：所有路径走环境变量 / 相对路径，clone 后即可替换自己的素材使用。

## 何时使用
- 用户要做读书会 / 沙龙 / 线下活动的**手机竖版海报**。
- 用户希望基于**真实设计模板的美感**（稿定 / Canva），而非用代码/HTML 从零画。
- 触发词示例：「读书会海报」「沙龙海报」「活动海报」「稿定 / Canva 海报二次修改」。

## 路线红线（MUST）
1. 默认「真实模板 + PIL 二次修改」，**否决纯代码 / HTML / Ardot 生成**（用户明确多次要求）。
2. 去水印用 `cv2.inpaint(TELEA)` + **空间约束**（只处理右上角近白连通块）；**禁止**全局颜色检测、**禁止**贴图覆盖。详见 `references/watermark_inpaint.md`。
3. 信息卡**整片铲掉重画**，禁止在旧图上叠加补丁。详见 `references/info_card_layout.md`。
4. 图标用**几何线绘**（`draw_clock/pin/yen`），禁止字体字符。
5. Logo 转黑透明合成右上角；二维码等比缩放到 130×130 + 圆角米白底衬。
6. 自检：水印残留=0、文字右缘<二维码左缘；AI 读不了图，靠用户视觉反馈 + 像素自检闭环。详见 `references/selfcheck.md`。
7. 风格**不锁死**，每期按内容定（暖沙米金 / 莫兰迪 / 森系等）。

## 工作流程
**阶段 0 ｜ 路线与风格对齐（前置）**：确认走真实模板+PIL 路线；确认本期风格方向。
**阶段 1 ｜ 明确活动信息**：收全字段——主题/副标题、书名、时间、地点、费用档位、限额、主办方、落款、Logo 路径、二维码路径。
**阶段 2 ｜ 联网搜索并下载真实模板**：搜稿定/Canva「读书会/沙龙 竖版手机海报」，下载真实渲染图（优先稿定 art 公开 CDN；Canva MCP 额度受限时转下载），收 3–5 张候选。
**阶段 3 ｜ 选候选**：展示 2–4 张，用户选定一张作底图。
**阶段 4 ｜ 调用脚本二次修改**：运行 `scripts/remix_poster.py`（见下），内部串联 去水印 → 信息卡重绘 → 图标/Logo/二维码合成 → 自检。
**阶段 5 ｜ 用户视觉反馈迭代**：用户看成品提微调 → 改 CONFIG 重跑，直到满意。
**阶段 6 ｜ 沉淀复盘**：有新踩坑/参数就更新本 skill 的 references 或脚本，并写项目 memory。

## 脚本调用
核心脚本 `scripts/remix_poster.py`。**只改顶部 CONFIG 区即可复用**，不必动函数体。
路径通过环境变量覆盖（默认读取 `assets/` 下文件，见 README「Environment overrides」）：
- `SALON_INPUT` / `SALON_OUTPUT`：底图与产出。
- `SALON_LOGO` / `SALON_QR`：素材路径。
- `SALON_FONT`：中文字体路径（Windows 默认微软雅黑，其他系统改成对应字体）。
- `REMOVE_WATERMARK` + `WATERMARK_REGION`：水印去除开关与右上角空间约束。
- `INFO_LINES`：三行文案 / 字号 / 颜色 / 图标（'clock'|'pin'|'yen'|None）。
- `CARD_*` / `ICON_*` / `BLUE_*`：版面参数（848×1200 基准，已验证值见 `references/info_card_layout.md`）。

运行（用你自己的 Python，已装 Pillow/numpy/opencv-python-headless）：
```
python scripts/remix_poster.py
```
脚本末尾 `selfcheck()` 会断言水印残留=0、文字不与二维码重叠，失败即中止。

## 参考文档
- `references/watermark_inpaint.md`：去水印标准法与红线。
- `references/info_card_layout.md`：信息卡坐标 / 字号 / 图标规范（已验证参数表）。
- `references/selfcheck.md`：自检清单与像素判据。
