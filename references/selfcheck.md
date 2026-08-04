# 程序化自检清单（selfcheck）

AI 本身读不了图，因此用像素级判据 + 用户视觉反馈形成闭环。脚本的 `selfcheck()` 已实现下列自动断言。

## 自动判据（脚本断言）
1. **水印残留 = 0**：水印区内近白像素数必须为 0（路线 A 开启 REMOVE_WATERMARK 时）。
2. **文字不与二维码重叠**：信息卡最长一行文字右缘 `text_right_edge` 必须 `<` 二维码左缘 `qr_left_edge`。
3. **Ardot 28px 硬底线（路线 B）**：渲染前断言所有正文/信息类字号 ≥28px；装饰性系列徽标（用户指定缩小）为已知例外，仅告警不中止。
   ```python
   core = [TITLE_FONT.size, SUBTITLE_FONT.size, QUOTE_FONT.size, TAG_FONT.size,
           INFO_FONTS['clock'].size, INFO_FONTS['pin'].size, INFO_FONTS['yen'].size]
   assert not [s for s in core if s < 28], '存在 <28px 字号'
   ```
4. **双模式可读（路线 B）**：`detect_mode()` 按底板亮度自动选 light/dark 配色；人工确认深底用浅字、浅底用深字，无"看不清"情况。

脚本在 `main()` 末尾 `assert` 上述硬判据，不通过则报错中止，不会产出错误图。

## 人工判据（交用户视觉审查）
- 顶部水印区（仅路线 A）：纹理融合自然、无残角、无 halo。
- 信息卡：三行对齐、图标居中、无旧文字残影、无错位/被切。
- Logo：透明底、置于右上角干净区、可读性佳。
- 二维码：完整、边缘柔和、不被文字压住。
- 金句艺术字（路线 B）：渐变/描边/投影清晰，不与底板糊在一起。
- 整体：风格与本期主题协调。

## 迭代
用户反馈微调（文字/字号/配色/图标对齐）→ 改 CONFIG 重跑 → 再次自检，直到满意。
