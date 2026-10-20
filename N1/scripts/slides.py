#!/usr/bin/env python3
"""Render 1280x720 lesson slides with Pillow (Noto CJK JP fonts)."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
NOTO_B = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
NOTO_R = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"

ACCENT = (255, 209, 102)
WHITE = (245, 247, 255)
MUTED = (168, 178, 210)
DIM = (118, 128, 162)

_font_cache = {}


def font(path, size, index=0):
    key = (path, size, index)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size, index=index)
    return _font_cache[key]


def base_image():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    top, bot = (15, 26, 60), (38, 62, 112)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)],
               fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse([950, -160, 1450, 340], fill=(255, 209, 102, 14))
    od.ellipse([-220, 420, 260, 900], fill=(120, 160, 255, 16))
    od.ellipse([180, 560, 420, 800], fill=(255, 255, 255, 8))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    return img


def chrome(img, day, total=180):
    d = ImageDraw.Draw(img)
    f_badge = font(NOTO_B, 26)
    f_small = font(NOTO_R, 22)
    # header badge
    badge = "N1 MỖI NGÀY"
    bw = d.textlength(badge, font=f_badge)
    d.rounded_rectangle([56, 34, 56 + bw + 44, 78], radius=20, fill=ACCENT)
    d.text((56 + 22, 40), badge, font=f_badge, fill=(20, 26, 50))
    d.text((56 + bw + 70, 40), f"BÀI {day:03d}", font=f_badge, fill=WHITE)
    d.line([(56, 100), (W - 56, 100)], fill=(255, 255, 255, 40), width=2)
    # footer
    d.text((56, H - 52), f"Bài {day} / {total}", font=f_small, fill=DIM)
    d.text((W - 56 - d.textlength("19:00 hằng ngày • JLPT N1", font=f_small), H - 52),
           "19:00 hằng ngày • JLPT N1", font=f_small, fill=DIM)
    return d


def wrap(d, text, fnt, max_w):
    lines = []
    for para in str(text).split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt) <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                while d.textlength(w, font=fnt) > max_w and len(w) > 1:
                    k = len(w)
                    while k > 1 and d.textlength(w[:k], font=fnt) > max_w:
                        k -= 1
                    lines.append(w[:k])
                    w = w[k:]
                cur = w
        if cur:
            lines.append(cur)
    return lines


def card(img, box, radius=18, fill=(255, 255, 255, 16)):
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=radius, fill=fill)
    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))
    return ImageDraw.Draw(img)


def centered(d, cx, y, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return y


def render_cover(day, theme_vi, theme_ja, date_str, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 170, "N1 MỖI NGÀY", font(NOTO_B, 108), WHITE)
    centered(d, W / 2, 300, f"BÀI {day:03d}", font(NOTO_B, 52), ACCENT)
    centered(d, W / 2, 380, theme_vi, font(NOTO_B, 46), WHITE)
    centered(d, W / 2, 448, theme_ja, font(NOTO_R, 34), MUTED)
    for i, t in enumerate(["Ngữ pháp", "Kanji", "Từ vựng"]):
        f = font(NOTO_B, 28)
        tw = d.textlength(t, font=f)
        x = W / 2 - (3 * 190) / 2 + i * 190
        d.rounded_rectangle([x, 530, x + 170, 584], radius=27, outline=ACCENT, width=2)
        d.text((x + 85 - tw / 2, 536), t, font=f, fill=ACCENT)
    centered(d, W / 2, 620, date_str, font(NOTO_R, 26), DIM)
    img.save(out)


def render_grammar(day, g, hook, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 130, "NGỮ PHÁP", font(NOTO_B, 34), ACCENT)
    centered(d, W / 2, 180, g["pattern"], font(SERIF_B, 92), WHITE)
    for i, ln in enumerate(wrap(d, g["meaning_vi"], font(NOTO_B, 36), W - 240)):
        centered(d, W / 2, 300 + i * 50, ln, font(NOTO_B, 36), WHITE)
    d = card(img, [90, 400, W - 90, 500])
    d.text((120, 414), "CÁCH CHIA", font=font(NOTO_B, 24), fill=ACCENT)
    for i, ln in enumerate(wrap(d, g["formation"], font(NOTO_R, 30), W - 300)):
        d.text((120, 448 + i * 42), ln, font=font(NOTO_R, 30), fill=WHITE)
    d = card(img, [90, 520, W - 90, 640])
    d.text((120, 532), "★ MẸO NHỚ", font=font(NOTO_B, 24), fill=ACCENT)
    for i, ln in enumerate(wrap(d, hook, font(NOTO_R, 27), W - 300)):
        d.text((120, 566 + i * 38), ln, font=font(NOTO_R, 27), fill=WHITE)
    img.save(out)


def render_examples(day, examples, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 122, "VÍ DỤ", font(NOTO_B, 34), ACCENT)
    y = 178
    circ = ["①", "②", "③", "④", "⑤"]
    for i, ex in enumerate(examples):
        d = card(img, [70, y, W - 70, y + 148])
        d.text((100, y + 12), circ[i], font=font(NOTO_B, 34), fill=ACCENT)
        yy = y + 12
        for ln in wrap(d, ex["ja"], font(NOTO_B, 33), W - 320):
            d.text((170, yy), ln, font=font(NOTO_B, 33), fill=WHITE)
            yy += 44
        for ln in wrap(d, ex["reading"], font(NOTO_R, 23), W - 320):
            d.text((170, yy), ln, font=font(NOTO_R, 23), fill=MUTED)
            yy += 32
        for ln in wrap(d, ex["vi"], font(NOTO_R, 27), W - 320):
            d.text((170, yy), ln, font=font(NOTO_R, 27), fill=(200, 210, 235))
            yy += 38
        y += 164
    img.save(out)


def render_kanji(day, kanji, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 122, "KANJI", font(NOTO_B, 34), ACCENT)
    col_w, gap = 350, 40
    x0 = (W - (3 * col_w + 2 * gap)) / 2
    for i, k in enumerate(kanji):
        x = x0 + i * (col_w + gap)
        d = card(img, [x, 180, x + col_w, 640])
        f_ch = font(SERIF_B, 118)
        cw = d.textlength(k["char"], font=f_ch)
        d.text((x + (col_w - cw) / 2, 196), k["char"], font=f_ch, fill=WHITE)
        centered(d, x + col_w / 2, 330, f"ON: {k['onyomi']}", font(NOTO_R, 26), ACCENT)
        centered(d, x + col_w / 2, 366, f"KUN: {k['kunyomi']}", font(NOTO_R, 26), MUTED)
        yy = 410
        for ln in wrap(d, k["meaning_vi"], font(NOTO_B, 30), col_w - 60):
            tw = d.textlength(ln, font=font(NOTO_B, 30))
            d.text((x + (col_w - tw) / 2, yy), ln, font=font(NOTO_B, 30), fill=WHITE)
            yy += 42
        yy += 6
        for c in k["compounds"]:
            for ln in wrap(d, "• " + c, font(NOTO_R, 22), col_w - 60):
                d.text((x + 30, yy), ln, font=font(NOTO_R, 22), fill=MUTED)
                yy += 32
    img.save(out)


def render_vocab(day, vocab, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 118, "TỪ VỰNG", font(NOTO_B, 34), ACCENT)
    y = 162
    for i, v in enumerate(vocab):
        d = card(img, [60, y, W - 60, y + 94])
        d.text((90, y + 6), f"{i+1}. {v['word']}（{v['reading']}）",
               font=font(NOTO_B, 34), fill=WHITE)
        mw = d.textlength(v["meaning_vi"], font=font(NOTO_B, 30))
        d.text((W - 90 - mw, y + 10), v["meaning_vi"], font=font(NOTO_B, 30), fill=ACCENT)
        d.text((90, y + 52), v["example_ja"], font=font(NOTO_R, 24), fill=(200, 210, 235))
        d.text((90 + d.textlength(v["example_ja"], font=font(NOTO_R, 24)) + 16, y + 54),
               "— " + v["example_vi"], font=font(NOTO_R, 22), fill=MUTED)
        y += 102
    img.save(out)


def render_quiz(day, quiz, recap, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 122, "MINI QUIZ + ÔN TẬP", font(NOTO_B, 34), ACCENT)
    y = 180
    for i, q in enumerate(quiz):
        d = card(img, [70, y, W - 70, y + 150])
        d.text((100, y + 14), f"Câu {i+1}: {q['q_vi']}", font=font(NOTO_B, 28), fill=WHITE)
        for ln in wrap(d, q["q_ja"], font(NOTO_B, 32), W - 300):
            d.text((100, y + 54), ln, font=font(NOTO_B, 32), fill=ACCENT)
            break
        ans = q["a_ja"] + "  —  " + q["a_vi"]
        for ln in wrap(d, "✓ " + ans, font(NOTO_R, 26), W - 300):
            d.text((100, y + 100), ln, font=font(NOTO_R, 26), fill=(170, 220, 170))
            break
        y += 166
    d = card(img, [70, y, W - 70, y + 96], fill=(255, 209, 102, 22))
    for ln in wrap(d, "★ " + recap, font(NOTO_B, 28), W - 300):
        d.text((100, y + 30), ln, font=font(NOTO_B, 28), fill=WHITE)
        break
    # second wrap line if needed
    lines = wrap(d, "★ " + recap, font(NOTO_B, 28), W - 300)
    if len(lines) > 1:
        d.text((100, y + 62), lines[1], font=font(NOTO_B, 28), fill=WHITE)
    img.save(out)


def render_outro(day, next_theme_vi, out):
    img = base_image()
    d = chrome(img, day)
    centered(d, W / 2, 200, "お疲れ様でした!", font(SERIF_B, 72), ACCENT)
    centered(d, W / 2, 300, "HẸN GẶP LẠI!", font(NOTO_B, 64), WHITE)
    for i, ln in enumerate(wrap(d, f"Bài tiếp theo: {next_theme_vi}",
                                font(NOTO_R, 36), W - 240)):
        centered(d, W / 2, 400 + i * 50, ln, font(NOTO_R, 36), MUTED)
    centered(d, W / 2, 520, "Nhớ ôn lại trước khi ngủ nhé!",
             font(NOTO_B, 32), WHITE)
    centered(d, W / 2, 580, "19:00 hằng ngày • Bài mới không trùng lặp",
             font(NOTO_R, 26), DIM)
    img.save(out)


def render_all(day_data, next_theme_vi, date_str, slide_dir):
    import os
    os.makedirs(slide_dir, exist_ok=True)
    day = day_data["day"]
    g = day_data["grammar"]
    paths = []
    def save(fn, *a):
        p = os.path.join(slide_dir, f"slide-{len(paths)+1:02d}.png")
        fn(*a, p)
        paths.append(p)
    save(render_cover, day, day_data["theme_vi"], day_data["theme_ja"], date_str)
    save(render_grammar, day, g, day_data["memory_hooks"][0])
    save(render_examples, day, g["examples"])
    save(render_kanji, day, day_data["kanji"])
    save(render_vocab, day, day_data["vocab"])
    recap = (f"Hôm nay: {g['pattern']} • Kanji "
             f"{' '.join(k['char'] for k in day_data['kanji'])} • "
             f"{len(day_data['vocab'])} từ vựng mới")
    save(render_quiz, day, day_data["quiz"], recap)
    save(render_outro, day, next_theme_vi)
    return paths
