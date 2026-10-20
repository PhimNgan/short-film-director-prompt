#!/usr/bin/env python3
"""Build one daily N1 lesson: slides, TTS audio, SRT captions, MP4 video.

Usage: make_lesson.py --day N | --day auto
Outputs: lessons/day-NNN/{video.mp4, caption.srt, script.md, slides/*.png}
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    NOW = datetime.now(ZoneInfo("Asia/Tokyo"))
except Exception:
    NOW = datetime.now()

BASE = Path("/home/hatch/workspace/n1-lessons")
sys.path.insert(0, str(BASE / "scripts"))
from slides import render_all  # noqa: E402

TTS = "/opt/hatch/bin/tts"
VI_VOICE = "avocado_v2:vd2_r8_rep5k_3492_v068_28k_g5k"   # Vietnamese, female
JA_VOICE = "avocado_v2:vd2_r8_rep1k_a134_v068_28k_g5k"  # Japanese, female
GAP = 0.35  # seconds of silence between narration chunks


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def load_day(day):
    plan = BASE / "plan" / "plan_180.json"
    if plan.exists():
        days = {d["day"]: d for d in json.loads(plan.read_text())["days"]}
        if day in days:
            return days[day], days.get(day + 1, {}).get("theme_vi", "chủ đề mới")
    seed = BASE / "plan" / "seeds" / f"day_{day:03d}.json"
    if seed.exists():
        return json.loads(seed.read_text()), "chủ đề mới"
    raise SystemExit(f"Không tìm thấy dữ liệu bài {day}")


def split_mixed(text):
    """Split mixed Vietnamese/Japanese text into (lang, chunk) pieces."""
    parts = re.split(r"([\u3040-\u30ff\u4e00-\u9fff々〜…・、。！？「」『』（）]+)", text)
    out = []
    for p in parts:
        p = p.strip(" \t")
        if not p:
            continue
        lang = "ja" if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", p) else "vi"
        out.append((lang, p))
    return out


def build_segments(d):
    day = d["day"]
    g = d["grammar"]
    segs = []

    def S(key, chunks):
        segs.append({"key": key, "chunks": [
            {"lang": lang, "text": t, "caption": c or t}
            for lang, t, c in chunks]})

    S("intro", [
        ("vi", f"Xin chào các bạn! Chào mừng đến với N1 mỗi ngày, bài số {day}.", None),
        ("vi", f"Hôm nay chúng ta sẽ chinh phục mẫu ngữ pháp {d['theme_vi'].lower()}, "
               f"{len(d['kanji'])} chữ Kanji và {len(d['vocab'])} từ vựng N1 hoàn toàn mới.", None),
        ("vi", "Cùng bắt đầu nào!", None),
    ])

    gram_chunks = [("vi", "Ngữ pháp hôm nay là", None),
                   ("ja", g["pattern_ja"], f"{g['pattern']}\n{g['meaning_vi']}"),
                   ("vi", f"Nghĩa là: {g['meaning_vi']}.", None)]
    gram_chunks += [(lang, t, None) for lang, t in split_mixed("Cách chia: " + g["formation"])]
    gram_chunks += [(lang, t, None) for lang, t in split_mixed("Mẹo nhớ: " + d["memory_hooks"][0])]
    S("grammar", gram_chunks)

    ex_chunks = [("vi", "Cùng nghe ba ví dụ nhé.", None)]
    for i, ex in enumerate(g["examples"], 1):
        ex_chunks.append(("vi", f"Ví dụ {i}:", None))
        ex_chunks.append(("ja", ex["ja"], f"{ex['ja']}\n{ex['reading']}\n{ex['vi']}"))
        ex_chunks.append(("vi", ex["vi"], None))
    S("examples", ex_chunks)

    kj_chunks = []
    for i, k in enumerate(d["kanji"], 1):
        kj_chunks.append(("vi", f"Chữ Kanji thứ {i}:", None))
        kj_chunks.append(("ja", f"{k['char']}、{k['onyomi']}",
                          f"{k['char']} — ON: {k['onyomi']} / KUN: {k['kunyomi']}\n{k['meaning_vi']}"))
        kj_chunks.append(("vi", f"Nghĩa là {k['meaning_vi']}.", None))
        kj_chunks += [(lang, t, None) for lang, t in split_mixed(k["hook"])]
    S("kanji", kj_chunks)

    vc_chunks = [("vi", f"{len(d['vocab'])} từ vựng N1 hôm nay. Nghe và lặp lại theo nhé.", None)]
    for v in d["vocab"]:
        vc_chunks.append(("ja", f"{v['word']}、{v['reading']}",
                          f"{v['word']}（{v['reading']}）: {v['meaning_vi']}"))
        vc_chunks.append(("vi", f"Nghĩa là {v['meaning_vi']}.", None))
        vc_chunks.append(("ja", v["example_ja"], f"{v['example_ja']}\n{v['example_vi']}"))
        vc_chunks.append(("vi", v["example_vi"], None))
    S("vocab", vc_chunks)

    qz_chunks = [("vi", "Mini quiz nè!", None)]
    for i, q in enumerate(d["quiz"], 1):
        qz_chunks.append(("vi", f"Câu {i + 1}. {q['q_vi']}", None))
        qz_chunks.append(("ja", q["q_ja"], f"{q['q_ja']}\n{q['q_vi']}"))
        qz_chunks.append(("vi", "Đáp án là:", None))
        qz_chunks.append(("ja", q["a_ja"], f"✓ {q['a_ja']}"))
        qz_chunks += [(lang, t, None) for lang, t in split_mixed(q["a_vi"])]
    qz_chunks.append(("vi", "Cùng ôn lại nhé. Hôm nay chúng ta đã học mẫu", None))
    qz_chunks.append(("ja", g["pattern_ja"], f"Ôn tập: {g['pattern']}"))
    chars_ja = "、".join(k["char"] for k in d["kanji"])
    qz_chunks.append(("ja", chars_ja, None))
    qz_chunks.append(("vi", f"{len(d['kanji'])} chữ Kanji và {len(d['vocab'])} từ vựng mới. Tuyệt vời!", None))
    S("quiz", qz_chunks)

    S("outro", [
        ("vi", "Hết bài rồi! Nội dung ngày mai hoàn toàn mới, không trùng với hôm nay.", None),
        ("vi", "Nhớ ôn lại trước khi ngủ để nhớ lâu nhé.", None),
        ("ja", "お疲れ様でした!", "お疲れ様でした! (Cảm ơn bạn đã cố gắng!)"),
        ("vi", "Hẹn gặp lại lúc mười chín giờ ngày mai!", None),
    ])
    return segs


def tts(text, voice, lang, out):
    subprocess.run([TTS, "speak", "--output", str(out), "--voice", voice,
                    "--language", lang, "--text-stdin"],
                   input=text.encode("utf-8"), check=True,
                   capture_output=True, timeout=240)


def duration(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(p.stdout.strip().split()[0])
    except Exception:
        p2 = subprocess.run(["ffmpeg", "-i", str(path)],
                            capture_output=True, text=True)
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p2.stderr)
        h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
        return h * 3600 + mi * 60 + s


def srt_time(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    day = None
    if "--day" in sys.argv:
        v = sys.argv[sys.argv.index("--day") + 1]
        day = None if v == "auto" else int(v)
    state_file = BASE / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    if day is None:
        day = int(state.get("last_done_day", 0)) + 1
    if day > 180:
        raise SystemExit("Đã hoàn thành 180 bài!")

    d, next_theme = load_day(day)
    tag = f"day-{day:03d}"
    lesson_dir = BASE / "lessons" / tag
    slide_dir = lesson_dir / "slides"
    work = BASE / "work" / tag
    chunk_dir = work / "chunks"
    for p in (slide_dir, chunk_dir):
        p.mkdir(parents=True, exist_ok=True)

    segments = build_segments(d)
    print(f"Bài {day}: {len(segments)} slide, "
          f"{sum(len(s['chunks']) for s in segments)} đoạn thoại", flush=True)

    # silence gap clip
    silence = work / "silence.mp3"
    if not silence.exists():
        run(["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"anullsrc=r=44100:cl=stereo", "-t", str(GAP), str(silence)])

    # TTS every chunk
    srt_entries = []
    seg_audios = []
    t = 0.0
    for si, seg in enumerate(segments):
        files = []
        for ci, ch in enumerate(seg["chunks"]):
            mp3 = chunk_dir / f"s{si}c{ci}.mp3"
            if not mp3.exists() or mp3.stat().st_size == 0:
                tts(ch["text"],
                    JA_VOICE if ch["lang"] == "ja" else VI_VOICE,
                    ch["lang"], mp3)
            dur = duration(mp3)
            srt_entries.append((t, t + dur, ch["caption"]))
            t += dur
            files += [mp3, silence]
            t += GAP
        lst = work / f"concat_s{si}.txt"
        lst.write_text("".join(f"file '{f}'\n" for f in files))
        seg_mp3 = work / f"seg{si}.mp3"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c:a", "libmp3lame", "-b:a", "128k", str(seg_mp3)])
        seg_audios.append((seg_mp3, duration(seg_mp3)))

    # SRT
    srt = lesson_dir / "caption.srt"
    with open(srt, "w") as f:
        for i, (a, b, cap) in enumerate(srt_entries, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{cap}\n\n")

    # slides
    date_str = NOW.strftime("Ngày %d/%m/%Y")
    slide_paths = render_all(d, next_theme, date_str, str(slide_dir))
    print("Đã render", len(slide_paths), "slide", flush=True)

    # per-segment video
    seg_mp4s = []
    for si, seg in enumerate(segments):
        mp3, adur = seg_audios[si]
        mp4 = work / f"seg{si}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30",
             "-i", slide_paths[si], "-i", str(mp3),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             "-t", f"{adur + 0.6:.2f}", str(mp4)])
        seg_mp4s.append(mp4)

    concat_list = work / "video_concat.txt"
    concat_list.write_text("".join(f"file '{p}'\n" for p in seg_mp4s))
    concat_mp4 = work / "concat.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c", "copy", str(concat_mp4)])
    total = duration(concat_mp4)

    # final: fades + optional teacher overlay (bottom-right, 1/4 W x 1/4 H)
    teacher = BASE / "assets" / "teacher.png"
    video_mp4 = lesson_dir / "video.mp4"
    if teacher.exists():
        fc = (f"[0:v]fade=t=in:st=0:d=0.6,fade=t=out:st={total-0.6:.2f}:d=0.6,"
              f"format=yuv420p[v];[1:v]scale=320:180[t];[v][t]overlay=W-320-24:H-180-24")
        run(["ffmpeg", "-y", "-i", str(concat_mp4), "-i", str(teacher),
             "-filter_complex", fc, "-c:v", "libx264", "-preset", "medium",
             "-crf", "25", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", str(video_mp4)])
    else:
        fc = (f"fade=t=in:st=0:d=0.6,fade=t=out:st={total-0.6:.2f}:d=0.6,"
              f"format=yuv420p")
        run(["ffmpeg", "-y", "-i", str(concat_mp4), "-vf", fc,
             "-c:v", "libx264", "-preset", "medium", "-crf", "25",
             "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", str(video_mp4)])

    final_dur = duration(video_mp4)
    size_mb = video_mp4.stat().st_size / 1e6

    # script.md
    md = [f"# Bài {day:03d} — {d['theme_vi']}", "",
          f"Ngày: {date_str} • Thời lượng video: {final_dur:.0f}s",
          "", "## Kịch bản lời thoại", ""]
    for seg in segments:
        md.append(f"### {seg['key']}")
        for ch in seg["chunks"]:
            md.append(f"- [{'JA' if ch['lang']=='ja' else 'VI'}] {ch['text']}")
        md.append("")
    md += ["## Slide", ""]
    md += [f"- slides/slide-{i+1:02d}.png — {s['key']}" for i, s in enumerate(segments)]
    (lesson_dir / "script.md").write_text("\n".join(md))

    state["last_done_day"] = day
    state["last_built_utc"] = datetime.utcnow().isoformat()
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    print(f"XONG bài {day}: video {final_dur:.0f}s, {size_mb:.1f}MB", flush=True)
    print(f"  {video_mp4}", flush=True)


if __name__ == "__main__":
    main()
