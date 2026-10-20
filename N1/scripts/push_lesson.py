#!/usr/bin/env python3
"""Push N1 lesson files to GitHub (repo PhimNgan/short-film-director-prompt, folder N1/).

Usage: push_lesson.py --day N
Mỗi lệnh upload của gh_api.py tạo một commit riêng.
"""
import json
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/hatch/workspace/n1-lessons")
GH = [sys.executable,
      "/home/hatch/workspace/custom-connectors/custom.github/bin/gh_api.py"]
OWNER, REPO, PREFIX = "PhimNgan", "short-film-director-prompt", "N1"

README = """# N1 Mỗi Ngày — 180 bài học tiếng Nhật N1

Video học N1 tự động tạo mỗi ngày lúc 19:00 (giờ Tokyo).

## Nội dung mỗi bài (~5 phút)
- 1 mẫu ngữ pháp N1 (giải thích + ví dụ + mẹo nhớ)
- 3 chữ Kanji N1 (âm đọc, nghĩa, từ ghép)
- 5 từ vựng N1 (kèm câu ví dụ)
- Mini quiz + ôn tập

180 bài **không trùng lặp** nội dung với nhau.

## Cấu trúc thư mục
- `plan/plan_180.json` — giáo trình 180 ngày
- `lessons/day-NNN/` — mỗi bài gồm:
  - `video.mp4` — video bài học
  - `caption.srt` — phụ đề
  - `script.md` — kịch bản lời thoại + mô tả slide
  - `slides/` — ảnh slide trình bày trong video
- `scripts/` — pipeline dựng video (slide/TTS/ghép)

## Lịch phát hành
Bài mới mỗi ngày 19:00 JST, từ bài 001 đến 180.
"""


def upload(local, repo_path, message):
    r = subprocess.run(GH + ["upload", OWNER, REPO, repo_path, str(local), message],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print(("OK  " if ok else "FAIL"), repo_path)
    if not ok:
        print(r.stdout[-500:], r.stderr[-500:])
    return ok


def main():
    day = int(sys.argv[sys.argv.index("--day") + 1])
    tag = f"day-{day:03d}"
    ldir = BASE / "lessons" / tag
    assert ldir.exists(), f"chưa có {ldir} — chạy make_lesson.py trước"

    state_file = BASE / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}

    readme_local = BASE / "N1_README.md"
    readme_local.write_text(README)
    upload(readme_local, f"{PREFIX}/README.md", f"N1: cập nhật README (bài {day})")

    plan = BASE / "plan" / "plan_180.json"
    if plan.exists() and not state.get("plan_pushed"):
        upload(plan, f"{PREFIX}/plan/plan_180.json",
               f"N1: giáo trình 180 ngày (bài {day})")
        state["plan_pushed"] = True

    if not state.get("scripts_pushed"):
        for s in ("make_lesson.py", "slides.py", "push_lesson.py"):
            p = BASE / "scripts" / s
            if p.exists():
                upload(p, f"{PREFIX}/scripts/{s}", f"N1: pipeline dựng video (bài {day})")
        state["scripts_pushed"] = True

    files = [("video.mp4", "video bài học"),
             ("caption.srt", "phụ đề"),
             ("script.md", "kịch bản")]
    for name, desc in files:
        upload(ldir / name, f"{PREFIX}/lessons/{tag}/{name}",
               f"N1 Bài {day}: {desc}")
    for png in sorted((ldir / "slides").glob("*.png")):
        upload(png, f"{PREFIX}/lessons/{tag}/slides/{png.name}",
               f"N1 Bài {day}: {png.name}")

    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print("Đẩy xong bài", day)


if __name__ == "__main__":
    main()
