# -*- coding: utf-8 -*-
"""照鉴·一百则 → 发布物料生成器

产出三样：
1) 小红书图文包 markdown（与 publish_helper.parse_post 兼容）
2) 卡片硬链接到镜子号 asset_root（发布引擎要求图片必须在 asset_root 下）
3) 发布队列行（每日 08:00 一篇）

幂等：重复执行不会重复插队列行（按 platform+code 去重）。
"""
import csv
import json
import os
import shutil
import sys

SRC_JSONL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stories_100.jsonl")
SRC_CARDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards")

PUB = "C:/Users/surface/Desktop/每日发布"
MIRROR = os.path.join(PUB, "03_小红书_镜子号_9225")
CARD_DST = os.path.join(MIRROR, "基础素材_配图卡", "照鉴一百则")
MD_DST = os.path.join(MIRROR, "储备文案", "小红书图文包_照鉴一百则_Z001-Z100.md")
QUEUE = os.path.join(PUB, "发布队列.csv")

SLOT = "08:00"
START_DATE = "2026-10-21"
PLATFORM = "镜子"
TAG_TAIL = "#照鉴镜子"

# 收藏/转发钩子，轮换用，避免每篇结尾雷同
HOOKS = [
    "这段要是说中了你，收藏着。下次又犯的时候，翻出来看一遍。",
    "看得懂的，替身边那个也在硬撑的人转一下。",
    "存下来。等哪天你想起某个人，会发现你早就在这段里见过他。",
    "想收藏就收藏，不用留言。有些话自己知道就够了。",
    "如果这段像在写你，别急着关。先放着，明天再看一遍。",
    "转给那个你一直想劝、又不知道怎么开口的人。",
]


def load_stories():
    rows = []
    with open(SRC_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_body(st, idx):
    parts = []
    quote = (st.get("quote") or "").strip()
    src = (st.get("src") or "").strip()
    if quote:
        parts.append("「%s」%s" % (quote, ("　—— " + src) if src else ""))
    for k in ("p1", "p2", "p3", "p4"):
        t = (st.get(k) or "").strip()
        if t:
            parts.append(t)
    parts.append(HOOKS[idx % len(HOOKS)])
    return "\n\n".join(parts)


def write_markdown(stories):
    lines = [
        "# 镜子号·照鉴一百则（引经据典·每日一则）",
        "",
        "> 定位：古人一句话，说今天的事。每篇一个典故落一件具体的生活困境，",
        "> 收口落到镜子小程序的功能（十道题／知行卡／每日指引／宝盒／月报）。",
        "> 合规：禁算命·占卜·运势·命格·诊断·预测·月运；禁 AI/智能/机器人 字眼。",
        "> 每天 08:00 一篇，100 篇覆盖 2026-10-21 ~ 2027-01-28。",
        "",
    ]
    for i, st in enumerate(stories):
        tags = " ".join(st.get("tags") or [])
        if TAG_TAIL not in tags:
            tags = (tags + " " + TAG_TAIL).strip()
        lines += [
            "## %s" % st["id"],
            "- 封面文案：%s" % st["title"].strip(),
            "- 出处：%s" % (st.get("src") or "").strip(),
            "",
            "正文：",
            build_body(st, i),
            "",
            "- 标签：%s" % tags,
            "",
        ]
    os.makedirs(os.path.dirname(MD_DST), exist_ok=True)
    with open(MD_DST, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    return MD_DST


def link_cards(stories):
    """把渲染好的卡片放进 asset_root（发布引擎强制校验路径前缀）。
    优先硬链接，跨盘失败退回复制。"""
    os.makedirs(CARD_DST, exist_ok=True)
    n_link = n_copy = n_skip = 0
    for st in stories:
        sid = st["id"]
        s_dir = os.path.join(SRC_CARDS, sid)
        d_dir = os.path.join(CARD_DST, sid)
        os.makedirs(d_dir, exist_ok=True)
        for name in sorted(os.listdir(s_dir)):
            if not name.endswith(".png"):
                continue
            s, d = os.path.join(s_dir, name), os.path.join(d_dir, name)
            if os.path.exists(d):
                n_skip += 1
                continue
            try:
                os.link(s, d)
                n_link += 1
            except OSError:
                shutil.copy2(s, d)
                n_copy += 1
    return n_link, n_copy, n_skip


def queue_rows(stories):
    from datetime import date, timedelta
    y, m, d = (int(x) for x in START_DATE.split("-"))
    day0 = date(y, m, d)
    rows = []
    for i, st in enumerate(stories):
        day = (day0 + timedelta(days=i)).isoformat()
        sid = st["id"]
        folder = os.path.join(CARD_DST, sid)
        imgs = [os.path.join(folder, "%s_%s.png" % (sid, k))
                for k in ("cover", "p1", "p2", "p3", "p4")]
        imgs = [p for p in imgs if os.path.exists(p)]
        rows.append({
            "date": day,
            "platform": PLATFORM,
            "post_file": os.path.relpath(MD_DST, PUB),
            "code": sid,
            "images": ";".join(imgs),
            "slot": SLOT,
        })
    return rows


def append_queue(rows):
    exist = set()
    header = None
    with open(QUEUE, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        header = rd.fieldnames
        for r in rd:
            exist.add((r.get("date"), r.get("platform"), r.get("code")))
    add = [r for r in rows if (r["date"], r["platform"], r["code"]) not in exist]
    if not add:
        return 0
    with open(QUEUE, "a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        for r in add:
            w.writerow(r)
    return len(add)


def main():
    stories = load_stories()
    if len(stories) != 100:
        print("⚠️ 篇数不是 100：", len(stories))
    md = write_markdown(stories)
    print("图文包:", md)
    nl, nc, ns = link_cards(stories)
    print("卡片 硬链接%d 复制%d 已存在%d" % (nl, nc, ns))
    rows = queue_rows(stories)
    missing = [r["code"] for r in rows if not r["images"]]
    if missing:
        print("⚠️ 无图片行:", missing[:10])
    n = append_queue(rows)
    print("队列新增 %d 行（%s ~ %s）" % (n, rows[0]["date"], rows[-1]["date"]))


if __name__ == "__main__":
    main()
