# -*- coding: utf-8 -*-
"""考卷用圖形產生器：數線、一次函數、三角形角度、長條圖。
只用數字與英文字母標示，中文說明放在題幹（DOCX）裡，
本機和雲端都不會有缺字問題。
"""
import math
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


def _cjk_font():
    """找中文字型（長條圖中文標籤用），找不到就回 None 用預設字型。"""
    cands = [
        r"C:\Windows\Fonts\NotoSansTC-VF.ttf",
        r"C:\Windows\Fonts\msjh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTC-Regular.ttf",
    ]
    import os
    for p in cands:
        if os.path.exists(p):
            try:
                return font_manager.FontProperties(fname=p)
            except Exception:
                pass
    return None


def _png(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_number_line(lo, hi, mark, label="A"):
    """數線：範圍 lo~hi，標示 mark 點。回 (圖檔, 答案字串)。"""
    fig, ax = plt.subplots(figsize=(6, 1.6))
    ax.set_xlim(lo - 1, hi + 1)
    ax.set_ylim(-1, 1)
    ax.axhline(0, color="black", linewidth=1.2)
    for x in range(lo, hi + 1):
        ax.plot([x, x], [0, 0.15], color="black", linewidth=1.2)
        ax.text(x, -0.3, str(x), ha="center", va="top", fontsize=10)
    ax.plot(mark, 0, "ro", markersize=8)
    ax.text(mark, 0.4, label, ha="center", va="bottom", fontsize=12)
    ax.axis("off")
    return _png(fig), str(mark)


def make_linear(a, b, xmin=-5, xmax=5):
    """一次函數 y=ax+b 圖形。回 (圖檔, y截距, x=2時y值)。"""
    xs = np.linspace(xmin, xmax, 300)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(xs, a * xs + b, linewidth=2)
    ax.axhline(0, color="k", linewidth=0.8)
    ax.axvline(0, color="k", linewidth=0.8)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    return _png(fig), f"(0, {b})", str(2 * a + b)


def make_triangle(deg_a, deg_b):
    """三角形標兩角求第三角。回 (圖檔, 答案字串)。"""
    deg_c = 180 - deg_a - deg_b
    a, b = math.radians(deg_a), math.radians(deg_b)
    ta, tb = math.tan(a), math.tan(b)
    base = 6.0
    x = base * tb / (ta + tb)
    h = x * ta
    A, B, C = (0.0, 0.0), (base, 0.0), (x, h)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.add_patch(plt.Polygon([A, B, C], fill=False, ec="black", linewidth=1.5))
    ax.text(A[0] + 0.35, 0.3, f"{deg_a}°", fontsize=12)
    ax.text(B[0] - 0.9, 0.3, f"{deg_b}°", fontsize=12)
    ax.text(C[0], C[1] + 0.2, "?", ha="center", fontsize=14)
    ax.text(A[0] - 0.35, -0.25, "A", fontsize=12)
    ax.text(B[0] + 0.1, -0.25, "B", fontsize=12)
    ax.text(C[0], C[1] + 0.5, "C", ha="center", fontsize=12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.autoscale()
    return _png(fig), str(deg_c)


def make_bar(title, items):
    """長條圖。items 是 [(名稱, 數值)]。回 (圖檔, 最高項目, 總和)。"""
    fp = _cjk_font()
    names = [n for n, _ in items]
    vals = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(range(len(names)), vals)
    ax.set_xticks(range(len(names)))
    if fp is not None:
        ax.set_xticklabels(names, fontproperties=fp)
        ax.set_title(title, fontproperties=fp, fontsize=13)
    else:
        ax.set_xticklabels([f"({i + 1})" for i in range(len(names))])
        ax.set_title("bar chart", fontsize=13)
    ax.set_ylabel("count")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v, str(v),
                ha="center", va="bottom")
    best = max(items, key=lambda x: x[1])[0]
    total = sum(vals)
    return _png(fig), best, str(total)
