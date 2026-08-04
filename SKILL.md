---
name: salon-poster-pil
agent_created: true
description: 手机竖版沙龙/活动海报的 PIL 工作流。两条路线：(A) 真实模板(稿定/Canva)下载 + PIL 二次修改；(B) 从零 PIL 全内容渲染——当模板平台不可达或需像素级精确文字时，用 Pexels/ImageGen 底板 + PIL 绘制全部文字层。含 Ardot 28px 硬底线、双模式(浅底深字/深底浅字)自动切换、艺术字(渐变+描边+投影)、主题驱动底板搜索、selfcheck 防重叠。触发词：读书会海报、沙龙海报、活动海报、稿定/Canva 海报二次修改、poster remix、PIL 海报。
---

# 读书沙龙海报 · PIL 工作流（路线 A + 路线 B）

把沙龙/活动海报用 PIL 做成手机竖版成品。提供两条互补路线：

- **路线 A · 真实模板 remix**：用户已有稿定/Canva 导出的真实模板 PNG → 去水印 + 信息卡重绘 + 图标/Logo/二维码合成。
- **路线 B · 从零全内容渲染（默认主路线）**：真实模板平台对程序化访问**反爬**（稿定返回 405、Canva 触发 Cloudflare），多数情况实际不可达；且 AI 生图文字易错字。→ 改用 **Pexels 免费可商用直链图 / ImageGen 生成图作底板**，用 PIL 绘制**全部**结构化文字层，文字像素级精确、完全可编辑。

> 实战结论：路线 B 更稳、更可控、成品更"贵气"。优先走 B；仅在确有真实模板 PNG 时走 A。

## 路线选择（MUST 先定）
- 有真实模板 PNG（稿定/Canva 导出，可能带水印）→ **路线 A**（`scripts/remix_poster.py`）。
- 模板不可达 / 需要精确文字控制 / 从零做 → **路线 B**（`scripts/render_full.py`）。

## 路线红线
1. 默认「PIL 路线」，否决纯 HTML/代码生成（除非用户明确要）。
2. **Ardot 28px 硬底线**：所有文字节点（主副标题/金句/价值点/信息卡/费用/序号）默认 ≥28px（短边 ≥720px 时不降）。唯一例外：用户**明确指定**缩小的装饰性系列徽标（微标签）。
3. 底板一律 `resize` 到目标尺寸——ImageGen 实际出图可能是 832×1216，而非请求的 848×1200。
4. 搜底板基于**主题内核意象**，不限于字面符号。例：《AI创作魔法 让灵感自由流动》→ 墨水扩散 / 水彩晕染 / 暖色光斑，而非"书本/书桌"。
5. 艺术字：金句用 **渐变填充 + 描边 + 投影阴影**（见 `references/pil_full_render.md` 的 `_art_text_layer`）；字体与主副标题**差异化**（雅黑 vs 楷体）。
6. 双模式：按底板亮度自动选 **浅底深字 / 深底浅字**（`detect_mode`），保证可读性。
7. selfcheck：文字右缘 < 二维码左缘；路线 B 额外断言全文字 ≥28px。

## 工作流程（路线 B 为主，实战验证）
- **阶段 0 ｜ 对齐**：确认走 PIL 路线；定本期风格 / 主题内核（避免字面化）。
- **阶段 1 ｜ 收信息**：主题/副标题、时间、地点、费用档位、限额、主办方、Logo 路径、二维码路径。
- **阶段 2 ｜ 搜底板（主题驱动）**：Pexels 直链 `https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg?auto=compress&cs=tinysrgb&h=1600` 用 curl 下载；或 ImageGen 生成。按意象线并行搜（流动/晕染/光感），每线 5–6 张。
- **阶段 3 ｜ 选底板**：生成联系图，展示 2–4 张供用户选定。
- **阶段 4 ｜ 渲染**：改 `scripts/render_full.py` 顶部 CONFIG（文案/路径/MODE/ART_QUOTE），运行。
- **阶段 5 ｜ 反馈迭代**：用户提微调 → 改 CONFIG 重跑，直到满意。
- **阶段 6 ｜ 沉淀**：新踩坑/参数写 `references/pitfalls.md` 或脚本，并写项目 memory。

## 脚本
| 脚本 | 路线 | 用法 |
|------|------|------|
| `scripts/remix_poster.py` | A 真实模板 remix | 改 CONFIG（INFO_LINES / WATERMARK_REGION），运行 |
| `scripts/render_full.py` | B 从零全内容 | 改 CONFIG（文案/路径/MODE/ART_QUOTE），运行 |

`render_full.py` 环境变量覆盖：`SALON_BASE`(底板) / `SALON_OUTPUT` / `SALON_LOGO` / `SALON_QR` / `SALON_MODE`(auto\|light\|dark) / `SALON_TITLE` / `SALON_SUB` / `SALON_QUOTE` / `SALON_BADGE`。

## 参考文档
- `references/pil_full_render.md`：路线 B 详解 + 艺术字/双模式/28px 代码。
- `references/pitfalls.md`：今日踩坑全集（反爬 / 尺寸不符 / <28px / 重叠 / 主题偏差）。
- `references/watermark_inpaint.md`：路线 A 去水印法。
- `references/info_card_layout.md`：路线 A 信息卡坐标。
- `references/selfcheck.md`：自检清单（含 28px 断言）。

## 版本历史
### v2.0.0
- 新增**路线 B（从零 PIL 全内容渲染）**为默认主路线：真实模板反爬不可达时兜底 + 文字像素级精确。
- 新增 **Ardot 28px 硬底线**（selfcheck 断言 + 装饰徽标例外）。
- 新增**主题驱动底板搜索**（不限于字面符号）。
- 新增**艺术字渲染**（渐变+描边+投影）+ 字体差异化层级（雅黑/楷体）。
- 新增**双模式自动检测**（浅底深字 / 深底浅字）。
- 新增 `scripts/render_full.py`、`references/pil_full_render.md`、`references/pitfalls.md`。
### v1.0.0
- 路线 A：真实模板 remix（去水印 / 信息卡重绘 / 几何图标 / Logo+QR / selfcheck）。
