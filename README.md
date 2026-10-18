# Wuxia Short Film Prompt

A reusable, production-grade prompt that turns an AI assistant into your **director, screenwriter, and production manager** for creating 30–60 minute wuxia / xianxia short films.

## What's inside

- `prompt-lam-phim-ngan-kiem-hiep-tien-hiep.md` — the full prompt (in Vietnamese). Copy everything below the second `---` and send it to a fresh AI session.

## The workflow

The prompt drives a 6-step gated production pipeline (**Step 0 → Step 5**). Every step ends with an explicit confirmation gate — the AI cannot move forward until you approve:

| Step | Name | What happens |
|------|------|--------------|
| 0 | Prep | Lock genre (wuxia/xianxia sub-genre), target length, visual style |
| 1 | Title | 3 title options, each with a hook/logline — you pick 1 |
| 2 | Story & characters | Plot summary, character sheets, world-building rules |
| 3 | Script | Two approval rounds: beat sheet first, then full dialogue script |
| 4 | Visuals | 10+ character/scene images with strict face & costume consistency |
| 5 | Assembly | Per-scene clips, distinct voice per character, music & SFX, revision rounds until final cut |

Plus built-in operating rules: a `📌 Step X/5` tracker on every reply, a **daily 7:00 AM check-in** asking whether to start/continue, inline edit handling, and a session naming convention (`🎬 Phim <Genre> — <Title>`).

## Usage

1. Copy the prompt into a new chat session.
2. Answer the AI's questions at each step.
3. Reply **"Duyệt"** (approve) to advance — or request edits inline and re-confirm.
