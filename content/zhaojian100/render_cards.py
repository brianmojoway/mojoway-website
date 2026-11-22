#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
照鉴·一百则 —— 中式文案卡片渲染器

输入：stories_100.jsonl（每行一篇，字段见 README_INLINE）
输出：每篇 5 张 1080x1440 PNG（cover / p1 典故 / p2 共情 / p3 洞察 / p4 落点）

设计取向：宣纸底 + 宋体 + 竖向标题 + 朱印。
不使用任何 AI 写实图，全部程序化绘制（合规、可批量、风格稳定）。
"""
import argparse
import json
import math
import os
import random
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1440

PAPER_TOP = (247, 242, 232)
PAPER_BOT = (240, 233, 219)
INK = (43, 39, 36)
INK_SOFT = (86, 79, 71)
INK_FAINT = (150, 140, 126)
CINNABAR = (166, 58, 45)
CINNABAR_SOFT = (196, 108, 94)

FONT_SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
FONT_KAI = r"C:\Windows\Fonts\simkai.ttf"
FONT_SONG = r"C:\Windows\Fonts\simsun.ttc"

_cache = {}


def font(path, size, weight=None):
    key = (path, size, weight)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(path, size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            try:
                f.set_variation_by_name(weight)
            except Exception:
                pass
    _cache[key] = f
    return f


def paper_bg(seed=0):
    """宣纸底：竖向渐变 + 纤维噪点 + 一角淡墨。"""
    rnd = random.Random(seed)
    base = Image.new("RGB", (W, H), PAPER_TOP)
    d = ImageDraw.Draw(base)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(PAPER_TOP[i] + (PAPER_BOT[i] - PAPER_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)

    # 淡墨两团（程序化，非图片）
    wash = Image.new("L", (W, H), 0)
    wd = ImageDraw.Draw(wash)
    for cx, cy, rx, ry, a in ((W * 0.18, H * 0.12, W * 0.42, H * 0.22, 26),
                              (W * 0.86, H * 0.92, W * 0.38, H * 0.20, 20)):
        wd.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=a)
    wash = wash.filter(ImageFilter.GaussianBlur(90))
    base = Image.composite(Image.new("RGB", (W, H), (214, 203, 183)), base, wash)

    # 纤维噪点
    px = base.load()
    for _ in range(int(W * H * 0.05)):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b = px[x, y]
        k = rnd.randint(-7, 5)
        px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)))
    return base


def frame(img, margin=54):
    d = ImageDraw.Draw(img)
    d.rectangle([margin, margin, W - margin, H - margin], outline=INK_FAINT, width=1)
    d.rectangle([margin + 7, margin + 7, W - margin - 7, H - margin - 7], outline=(200, 190, 174), width=1)
    # 四角短线
    L = 34
    for x, y, dx, dy in ((margin, margin, 1, 1), (W - margin, margin, -1, 1),
                         (margin, H - margin, 1, -1), (W - margin, H - margin, -1, -1)):
        d.line([(x, y), (x + dx * L, y)], fill=INK_SOFT, width=2)
        d.line([(x, y), (x, y + dy * L)], fill=INK_SOFT, width=2)
    return img


def seal(img, cx, cy, text=u"照鉴", size=96):
    """朱红印章：圆角方 + 竖排白字。"""
    d = ImageDraw.Draw(img)
    s = size
    box = [cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2]
    d.rounded_rectangle(box, radius=10, fill=CINNABAR)
    f = font(FONT_SERIF, int(s * 0.40), 700)
    chars = list(text)
    n = len(chars)
    total = n * int(s * 0.44)
    y = cy - total // 2 + int(s * 0.06)
    for ch in chars:
        w = d.textlength(ch, font=f)
        d.text((cx - w / 2, y), ch, font=f, fill=(250, 246, 238))
        y += int(s * 0.44)
    return img


NO_HEAD = u"，。、；：！？）」』】…·%”’,.!?:;)]}>"


def wrap(text, f, max_w):
    """中文断行：避头（标点不出现在行首）+ 避尾（前引号不留在行尾）。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if f.getlength(cur + ch) <= max_w:
            cur += ch
        else:
            if ch in NO_HEAD and cur:
                # 标点挤进本行：把本行最后一字挪到下行
                lines.append(cur[:-1])
                cur = cur[-1] + ch
            else:
                lines.append(cur)
                cur = ch
    if cur:
        lines.append(cur)
    return lines


def draw_para(d, text, f, x, y, max_w, line_h, fill=INK, indent_chars=2):
    """中文段落：首行缩进两字，返回结束 y。"""
    indent = f.getlength(u"　" * indent_chars)
    first = True
    for para in text.split("\n"):
        lines = wrap(u"　" * indent_chars + para, f, max_w) if first else wrap(para, f, max_w)
        for i, line in enumerate(lines):
            d.text((x, y), line, font=f, fill=fill)
            y += line_h
        first = False
        y += int(line_h * 0.55)
    return y


def vertical_text(d, text, f, x, y, char_gap=1.22, col_gap=1.55, color=INK, max_rows=None):
    """竖排：从右往左，逐字下行。返回 (占用宽度, 占用高度)。"""
    row_h = int(f.size * char_gap)
    rows = max_rows or H
    cols = []
    cur = []
    for ch in text:
        if ch == "\n" or len(cur) >= rows:
            cols.append(cur)
            cur = []
            if ch == "\n":
                continue
        cur.append(ch)
    if cur:
        cols.append(cur)
    cx = x
    total_w = 0
    for col in cols:
        cy = y
        for ch in col:
            w = d.textlength(ch, font=f)
            d.text((cx - w / 2, cy), ch, font=f, fill=color)
            cy += row_h
        total_w += int(f.size * col_gap)
        cx -= int(f.size * col_gap)
    return total_w, row_h * max((len(c) for c in cols), default=0)


def page_title(img, kicker, idx_text):
    d = ImageDraw.Draw(img)
    f_k = font(FONT_SERIF, 30, 500)
    d.text((108, 112), kicker, font=f_k, fill=INK_SOFT)
    f_i = font(FONT_SERIF, 26, 400)
    w = d.textlength(idx_text, font=f_i)
    d.text((W - 108 - w, 116), idx_text, font=f_i, fill=INK_FAINT)
    d.line([(108, 162), (W - 108, 162)], fill=(198, 188, 172), width=1)
    return img


def page_footer(img, n, total, label=u"照鉴 · 镜子"):
    d = ImageDraw.Draw(img)
    f = font(FONT_SERIF, 24, 400)
    d.line([(108, H - 150), (W - 108, H - 150)], fill=(206, 196, 180), width=1)
    d.text((108, H - 128), label, font=f, fill=INK_FAINT)
    t = u"%d / %d" % (n, total)
    w = d.textlength(t, font=f)
    d.text((W - 108 - w, H - 128), t, font=f, fill=INK_FAINT)
    return img


def card_cover(st, idx, total):
    img = paper_bg(seed=idx)
    frame(img)
    d = ImageDraw.Draw(img)

    page_title(img, u"照鉴 · 每日一则", st.get("src", u""))

    # 竖排标题：按字数自适应字号，整块垂直居中
    title = st["title"]
    n = len(title)
    size = 100 if n <= 8 else 88 if n <= 12 else 76 if n <= 16 else 66 if n <= 20 else 58
    rows = min(8, max(6, -(-n // max(1, -(-n // 8)))))
    f_t = font(FONT_SERIF, size, 700)
    row_h = int(size * 1.24)
    ncols = -(-n // rows)
    block_h = min(n, rows) * row_h
    vy = int((H - 120 - block_h) / 2) + 40
    vx = W - 176
    vertical_text(d, title, f_t, vx, vy, char_gap=1.24, col_gap=1.60, color=INK, max_rows=rows)

    # 金句：左下横排，最多两行
    gold = st.get("gold", "")
    if gold:
        f_g = font(FONT_SERIF, 36, 500)
        lines = wrap(gold, f_g, W - 176 - 150)
        gy = H - 300 - (len(lines) - 1) * 54
        for line in lines:
            d.text((176, gy), line, font=f_g, fill=CINNABAR)
            gy += 54

    seal(img, 176, H - 196, u"照鉴", 92)

    f_s = font(FONT_SERIF, 24, 400)
    d.text((W - 300, H - 176), u"引经据典 · 说今天的事", font=f_s, fill=INK_FAINT)
    return img


def card_page(st, idx, total, kind):
    img = paper_bg(seed=idx * 7 + hash(kind) % 97)
    frame(img)

    if kind == "quote":
        page_title(img, u"其一 · 古人怎么说", st.get("src", u""))
        d = ImageDraw.Draw(img)
        f_q = font(FONT_SERIF, 56, 500)
        qtext = u"「" + st["quote"] + u"」"
        # 先按标点切段，再按宽度装箱，避免把句子拦腰截断
        segs = []
        buf = ""
        for ch in qtext:
            buf += ch
            if ch in u"，。；：！？」":
                segs.append(buf)
                buf = ""
        if buf:
            segs.append(buf)
        lines, cur = [], ""
        for s in segs:
            if f_q.getlength(cur + s) <= W - 260 or not cur:
                cur += s
            else:
                lines.append(cur)
                cur = s
        if cur:
            lines.append(cur)
        y = 250
        for line in lines:
            w = f_q.getlength(line)
            d.text(((W - w) / 2, y), line, font=f_q, fill=INK)
            y += int(56 * 1.72)
        y += 30
        d.line([(W / 2 - 60, y), (W / 2 + 60, y)], fill=CINNABAR_SOFT, width=2)
        y += 56
        f_b = font(FONT_SERIF, 40, 400)
        draw_para(d, st["p1"], f_b, 132, y, W - 264, 72, INK_SOFT, indent_chars=0)
        page_footer(img, 2, 5)
        return img

    if kind == "feel":
        page_title(img, u"其二 · 是不是你", u"照见")
        d = ImageDraw.Draw(img)
        f_b = font(FONT_SERIF, 42, 400)
        draw_para(d, st["p2"], f_b, 132, 226, W - 264, 78, INK, indent_chars=2)
        page_footer(img, 3, 5)
        return img

    if kind == "turn":
        page_title(img, u"其三 · 换个看法", u"觉醒")
        d = ImageDraw.Draw(img)
        f_b = font(FONT_SERIF, 42, 400)
        y = draw_para(d, st["p3"], f_b, 132, 226, W - 264, 78, INK, indent_chars=2)
        # 金句块
        gold = st.get("gold", "")
        if gold:
            y += 30
            d.rectangle([120, y, W - 120, y + 128], fill=(238, 230, 215))
            f_g = font(FONT_SERIF, 40, 500)
            lines = wrap(gold, f_g, W - 320)
            ty = y + (128 - len(lines) * 58) // 2
            for line in lines:
                w = f_g.getlength(line)
                d.text(((W - w) / 2, ty), line, font=f_g, fill=CINNABAR)
                ty += 58
        page_footer(img, 4, 5)
        return img

    # landing
    page_title(img, u"其四 · 你可以做的一件事", u"落点")
    d = ImageDraw.Draw(img)
    f_b = font(FONT_SERIF, 42, 400)
    y = draw_para(d, st["p4"], f_b, 132, 226, W - 264, 78, INK, indent_chars=2)
    d.line([(132, y + 20), (W - 132, y + 20)], fill=(206, 196, 180), width=1)
    f_t = font(FONT_SERIF, 34, 500)
    d.text((132, y + 62), u"「照鉴 · 镜子」微信小程序", font=f_t, fill=INK)
    f_s = font(FONT_SERIF, 30, 400)
    d.text((132, y + 118), u"十道题，看清自己是哪一型；每天一句，知道今天该怎么过。", font=f_s, fill=INK_SOFT)
    seal(img, W - 200, H - 300, u"知行", 92)
    page_footer(img, 5, 5)
    return img


STORY_FIELDS = ("id", "src", "quote", "title", "gold", "p1", "p2", "p3", "p4", "tags")


def note_text(st):
    body = "\n\n".join([st["p1"], st["p2"], st["p3"], st["p4"]])
    tags = " ".join(st.get("tags", [])) if isinstance(st.get("tags"), list) else st.get("tags", "")
    return "%s\n\n%s\n\n%s" % (st["title"], body, tags)


def render_one(st, idx, outdir, quality=92):
    os.makedirs(outdir, exist_ok=True)
    imgs = {
        "cover": card_cover(st, idx, 5),
        "p1": card_page(st, idx, 5, "quote"),
        "p2": card_page(st, idx, 5, "feel"),
        "p3": card_page(st, idx, 5, "turn"),
        "p4": card_page(st, idx, 5, "landing"),
    }
    paths = []
    sid = st["id"]
    for k in ("cover", "p1", "p2", "p3", "p4"):
        p = os.path.join(outdir, "%s_%s.png" % (sid, k))
        imgs[k].save(p, "PNG", optimize=True)
        paths.append(p)
    return paths


def load_stories(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stories", default=os.path.join(os.path.dirname(__file__), "stories_100.jsonl"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "cards"))
    ap.add_argument("--only", default="", help="只渲染指定 id，逗号分隔")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--notes", action="store_true", help="同时导出 note 文案 txt")
    a = ap.parse_args()

    stories = load_stories(a.stories)
    if a.only:
        want = set(x.strip() for x in a.only.split(",") if x.strip())
        stories = [s for s in stories if s["id"] in want]
    if a.limit:
        stories = stories[: a.limit]

    base = os.path.dirname(os.path.abspath(__file__))
    done = 0
    for i, st in enumerate(stories, 1):
        outdir = os.path.join(a.out, st["id"])
        paths = render_one(st, i, outdir)
        if a.notes:
            with open(os.path.join(outdir, "note.txt"), "w", encoding="utf-8") as f:
                f.write(note_text(st))
        done += 1
        print("[%d/%d] %s %s" % (i, len(stories), st["id"], st["title"]))
    print("DONE %d 篇 → %s" % (done, a.out))


if __name__ == "__main__":
    main()
