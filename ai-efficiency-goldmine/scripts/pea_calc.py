#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 效率金矿 · 计算脚本（零依赖，仅用标准库；Python 3.6+ 可跑）

可选组件：本脚本只是提速与校验用的辅助工具，不是必经步骤。
不 import 任何第三方包，不读写本 skill 之外的任何路径，不联网。
命令按环境取 python 或 python3；遇编码问题先设 PYTHONIOENCODING=utf-8。

用法:
    python pea_calc.py --demo                # 跑内置示例（原文公开案例），验证脚本可用
    python pea_calc.py --input data.json     # 计算真实数据
    python pea_calc.py --input data.json --out report.md

本脚本是可选的。执行不了时改用手算，公式见 references/method-cards.md：
    TGA 每周可省 = 每周耗时 × 替代率
    PEA 总分     = (P1+P2+P3+P4) × (V1+V2+V3+V4)              # 满分 400
    AIFE 综合分  = 技术×0.25 + 数据×0.20 + 经济×0.30 + 组织×0.15 + 合规×0.10
    ROI          = (年收益 − 年成本) ÷ 年成本 × 100%

输入 JSON 结构（四段任选，缺哪段跳过哪段）:
{
  "tga": [
    {"name": "回日常邮件", "level": "L2", "weekly_hours": 2, "replace_rate": 0.8}
  ],
  "pea": [
    {"name": "做数据报表", "P": [5,4,4,3], "V": [5,4,5,5]}
  ],
  "aife": [
    {"name": "做数据报表", "scores": {"技术":5, "数据":4, "经济":5, "组织":4, "合规":5}}
  ],
  "roi": [
    {"name": "个人AI写作", "annual_cost": 2400, "annual_gain": 48000}
  ]
}

字段说明:
  tga.replace_rate   替代率，0-1 或 0-100 均可（>1 自动视为百分数）
  pea.P / pea.V      各 4 个整数，1-5 分，顺序固定
                     P = [频率, 耗时, 厌烦度, 瓶颈度]
                     V = [时间价值, 质量价值, 释放价值, 规模化价值]
  aife.scores        五个维度 1-5 分，键名可用中文或拼音首字母
                     权重：技术25% 数据20% 经济30% 组织15% 合规10%
  roi                年成本与年收益，单位元
"""

import argparse
import json
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------- 常量

TGA_LEVELS = {
    "L1": ("<2分钟", 0.90),
    "L2": ("2-15分钟", 0.80),
    "L3": ("15-60分钟", 0.60),
    "L4": ("1-4小时", 0.40),
    "L5": (">4小时", 0.20),
}

AIFE_WEIGHTS = {
    "技术": 0.25, "数据": 0.20, "经济": 0.30, "组织": 0.15, "合规": 0.10,
}
AIFE_ALIAS = {
    "jishu": "技术", "shuju": "数据", "jingji": "经济",
    "zuzhi": "组织", "hegui": "合规",
}

PEA_LABELS_P = ["频率", "耗时", "厌烦度", "瓶颈度"]
PEA_LABELS_V = ["时间价值", "质量价值", "释放价值", "规模价值"]


def tier(score: float) -> str:
    if score >= 300:
        return "第一梯队 优先做"
    if score >= 200:
        return "第二梯队 本季度"
    if score >= 150:
        return "观察"
    return "暂缓"


def light(score: float) -> str:
    if score >= 4.0:
        return "✅ 绿灯 立即启动"
    if score >= 3.0:
        return "🟡 黄灯 先补短板"
    return "🔴 红灯 先别干"


def fnum(x: float) -> str:
    """去掉多余小数，让表格干净。"""
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.1f}"


# ---------------------------------------------------------------- 各段计算

def calc_tga(items):
    rows, total_h, total_save = [], 0.0, 0.0
    for it in items:
        name = it.get("name", "未命名")
        level = str(it.get("level", "")).upper()
        hours = float(it.get("weekly_hours", 0) or 0)

        rate = it.get("replace_rate")
        if rate is None:
            rate = TGA_LEVELS.get(level, ("", 0.0))[1]
        else:
            rate = float(rate)
            if rate > 1:
                rate = rate / 100.0

        save = hours * rate
        total_h += hours
        total_save += save
        rows.append({
            "name": name, "level": level, "hours": hours,
            "rate": rate, "save": save,
            "keep": level in ("L1", "L2", "L3"),
        })

    rows.sort(key=lambda r: -r["save"])
    out = ["### TGA 任务颗粒度分级\n",
           "| 任务 | 级别 | 每周耗时(h) | 替代率 | 每周可省(h) | 是否进PEA |",
           "|---|---|---:|---:|---:|---|"]
    for r in rows:
        out.append(
            f"| {r['name']} | {r['level']} | {fnum(r['hours'])} | "
            f"{int(round(r['rate'] * 100))}% | {fnum(r['save'])} | "
            f"{'是' if r['keep'] else '否(仅辅助)'} |"
        )
    avg = (total_save / total_h * 100) if total_h else 0
    out.append(
        f"| **合计** | | **{fnum(total_h)}** | 平均 {int(round(avg))}% | "
        f"**{fnum(total_save)}** | |"
    )
    out.append(
        f"\n> 每周可省 **{fnum(total_save)} 小时**，"
        f"相当于多出 {fnum(total_save / 8)} 个完整工作日。"
    )
    keep = [r["name"] for r in rows if r["keep"]]
    if keep:
        out.append("> 进入 PEA 打分：" + "、".join(keep))
    return "\n".join(out), keep


def calc_pea(items):
    rows = []
    for it in items:
        P = [float(x) for x in it.get("P", [0, 0, 0, 0])]
        V = [float(x) for x in it.get("V", [0, 0, 0, 0])]
        if len(P) != 4 or len(V) != 4:
            raise ValueError(f"场景「{it.get('name')}」的 P/V 必须各 4 个分数")
        ps, vs = sum(P), sum(V)
        rows.append({"name": it.get("name", "未命名"), "P": P, "V": V,
                     "ps": ps, "vs": vs, "total": ps * vs})

    rows.sort(key=lambda r: -r["total"])
    out = ["### PEA 痛点价值排名\n",
           "| 排名 | 场景 | " + " | ".join("P" + str(i + 1) for i in range(4)) +
           " | P小计 | " + " | ".join("V" + str(i + 1) for i in range(4)) +
           " | V小计 | **总分** | 判定 |",
           "|---|---|" + "---:|" * 4 + "---:|" + "---:|" * 4 + "---:|---:|---|"]
    for i, r in enumerate(rows, 1):
        out.append(
            f"| {i} | {r['name']} | " +
            " | ".join(fnum(x) for x in r["P"]) + f" | {fnum(r['ps'])} | " +
            " | ".join(fnum(x) for x in r["V"]) + f" | {fnum(r['vs'])} | " +
            f"**{fnum(r['total'])}** | {tier(r['total'])} |"
        )
    out.append("\n> P1 频率｜P2 耗时｜P3 厌烦度｜P4 瓶颈度　"
               "V1 时间｜V2 质量｜V3 释放｜V4 规模　"
               "总分 = (P1+P2+P3+P4) × (V1+V2+V3+V4)，满分 400")
    return "\n".join(out), [r["name"] for r in rows]


def calc_aife(items, top_names=None):
    if top_names:
        selected = [it for it in items if it.get("name") in top_names]
        # 保持 PEA 排名顺序
        selected.sort(key=lambda it: top_names.index(it.get("name")))
    else:
        selected = list(items)

    out = ["### AIFE 落地可行性判定\n",
           "| 场景 | 技术25% | 数据20% | 经济30% | 组织15% | 合规10% | 综合分 | 判定 |",
           "|---|---:|---:|---:|---:|---:|---:|---|"]
    results = []
    for it in selected:
        raw = it.get("scores", {})
        s = {}
        for k, v in raw.items():
            key = AIFE_ALIAS.get(str(k).lower().strip(), k)
            s[key] = float(v)
        score = sum(s.get(k, 0) * w for k, w in AIFE_WEIGHTS.items())
        results.append((it.get("name", "未命名"), s, score))
        out.append(
            f"| {it.get('name', '未命名')} | " +
            " | ".join(fnum(s.get(k, 0)) for k in ["技术", "数据", "经济", "组织", "合规"]) +
            f" | **{score:.2f}** | {light(score)} |"
        )

    out.append("\n> ⚠️ 合规维度涉及客户信息/个人信息/涉密内容时直接记 ≤2 分，需先做合规确认。")
    for name, s, sc in results:
        if s.get("合规", 5) <= 2:
            out.append(f"> 🛑 「{name}」合规维度 ≤2 分 —— 建议先走合规确认，暂不给技术方案。")
    return "\n".join(out)


def calc_roi(items):
    out = ["### ROI 投资回报\n",
           "| 场景 | 年成本(元) | 年收益(元) | ROI | 回本(月) |",
           "|---|---:|---:|---:|---:|"]
    for it in items:
        cost = float(it.get("annual_cost", 0) or 0)
        gain = float(it.get("annual_gain", 0) or 0)
        if cost <= 0:
            out.append(f"| {it.get('name','未命名')} | {fnum(cost)} | {fnum(gain)} | — | — |")
            continue
        roi = (gain - cost) / cost * 100
        months = (cost / (gain / 12)) if gain > 0 else None
        out.append(
            f"| {it.get('name','未命名')} | {fnum(cost)} | {fnum(gain)} | "
            f"**{int(round(roi))}%** | {fnum(months) if months else '—'} |"
        )
    out.append("\n> ⚠️ 数字来源必须标注："
               "`[他人案例]` 公开案例非实测 ｜ `[估算]` 按你的工时推算 ｜ `[实测]` 自己跑过")
    return "\n".join(out)


# ---------------------------------------------------------------- 内置示例

DEMO = {
    "tga": [
        {"name": "回日常邮件", "level": "L2", "weekly_hours": 2, "replace_rate": 0.80},
        {"name": "写会议纪要", "level": "L2", "weekly_hours": 1.5, "replace_rate": 0.85},
        {"name": "整理用户反馈", "level": "L3", "weekly_hours": 3, "replace_rate": 0.70},
        {"name": "写周报", "level": "L3", "weekly_hours": 1, "replace_rate": 0.60},
        {"name": "画产品原型", "level": "L3", "weekly_hours": 5, "replace_rate": 0.50},
        {"name": "做竞品分析", "level": "L4", "weekly_hours": 4, "replace_rate": 0.40},
        {"name": "写PRD文档", "level": "L4", "weekly_hours": 6, "replace_rate": 0.30},
        {"name": "团队沟通会议", "level": "L5", "weekly_hours": 4, "replace_rate": 0.10},
    ],
    "pea": [
        {"name": "做数据报表", "P": [5, 4, 4, 3], "V": [5, 4, 5, 5]},
        {"name": "审合同条款", "P": [3, 5, 4, 4], "V": [4, 4, 3, 4]},
        {"name": "做PPT", "P": [3, 4, 4, 3], "V": [5, 3, 4, 4]},
        {"name": "回客户咨询", "P": [5, 2, 3, 3], "V": [4, 3, 4, 5]},
        {"name": "写战略规划", "P": [1, 5, 2, 2], "V": [3, 2, 3, 2]},
    ],
    "aife": [
        {"name": "做数据报表", "scores": {"技术": 5, "数据": 4, "经济": 5, "组织": 4, "合规": 5}},
        {"name": "审合同条款", "scores": {"技术": 4, "数据": 3, "经济": 4, "组织": 3, "合规": 2}},
        {"name": "做PPT", "scores": {"技术": 5, "数据": 4, "经济": 4, "组织": 4, "合规": 5}},
    ],
    "roi": [
        {"name": "个人AI写作", "annual_cost": 2400, "annual_gain": 48000},
        {"name": "企业AI客服", "annual_cost": 200000, "annual_gain": 450000},
    ],
}


# ---------------------------------------------------------------- 主流程

def render(data):
    blocks = []
    keep_names = None

    if data.get("tga"):
        txt, keep_names = calc_tga(data["tga"])
        blocks.append(txt)

    if data.get("pea"):
        txt, ranked = calc_pea(data["pea"])
        blocks.append(txt)
        # AIFE 未显式给出时，自动取 PEA 前三
        if data.get("aife") is None:
            keep_names = ranked[:3]
        elif keep_names:
            keep_names = [n for n in ranked if n in keep_names][:3]
        else:
            keep_names = ranked[:3]

    if data.get("aife"):
        blocks.append(calc_aife(data["aife"], keep_names))

    if data.get("roi"):
        blocks.append(calc_roi(data["roi"]))

    if not blocks:
        return "输入里没有可计算的数据段（tga / pea / aife / roi）。"
    return "\n\n".join(blocks)


def main():
    ap = argparse.ArgumentParser(description="AI 效率金矿计算脚本")
    ap.add_argument("--input", help="输入 JSON 文件路径")
    ap.add_argument("--demo", action="store_true", help="跑内置示例")
    ap.add_argument("--out", help="输出 Markdown 文件路径（默认打印到屏幕）")
    args = ap.parse_args()

    if args.demo:
        data = DEMO
        header = "# AI 效率金矿 · 示例计算（原文公开案例，仅供验证脚本）\n"
    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        header = ""
    else:
        ap.error("需要 --input <file.json> 或 --demo")
        return

    body = render(data)
    text = header + "\n" + body if header else body

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已写入 {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
